import boto3
import json

from uuid import uuid4
from flask import Blueprint, request, jsonify
from app.core.dependencies import get_db, verify_admin
from app.crud import admin as admin_crud
from app.schemas.event import EventCreate, EventPublic
from app.schemas.update import LiveUpdateCreate, LiveUpdatePublic
from app.schemas.video import VideoPublic
from config import get_settings

settings = get_settings()
r2_client = boto3.client(
    "s3",
    endpoint_url=settings.r2_endpoint_url_s3,
    aws_access_key_id=settings.r2_access_key_id,
    aws_secret_access_key=settings.r2_secret_access_key
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/videos/multipart/initiate", methods=["POST"])
@verify_admin
def initiate_video_upload(current_admin):
    data = request.json
    filename = data.get("filename")
    content_type = data.get("content_type", "video/mp4")

    if not filename:
        return jsonify({"error": "Filename required"}), 400

    key = f"videos/{uuid4()}_{filename}"

    response = r2_client.create_multipart_upload(
        Bucket=settings.r2_bucket_name,
        Key=key,
        ContentType=content_type
    )

    return jsonify({
        "upload_id": response["UploadId"],
        "key": key
    })


@admin_bp.route("/videos/multipart/sign-part", methods=["POST"])
@verify_admin
def sign_video_part(current_admin):
    data = request.json
    key = data.get("key")
    upload_id = data.get("upload_id")
    part_number = data.get("part_number")

    if not key or not upload_id or not part_number:
        return jsonify({"error": "Missing key, upload_id, or part_number"}), 400

    url = r2_client.generate_presigned_url(
        "upload_part",
        Params={
            "Bucket": settings.r2_bucket_name,
            "Key": key,
            "UploadId": upload_id,
            "PartNumber": part_number
        },
        ExpiresIn=3600
    )

    return jsonify({"url": url})


@admin_bp.route("/videos", methods=["POST"])
@verify_admin
def complete_video_upload(current_admin):
    title = request.form.get("title")
    description = request.form.get("description")
    category_ids_raw = request.form.getlist("category_ids")
    thumbnail = request.files.get("thumbnail")

    key = request.form.get("key")         # from initiate step
    upload_id = request.form.get("upload_id")
    parts = request.form.get("parts")     # JSON string of parts

    if not title or not description or not category_ids_raw or not key or not upload_id or not parts:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        category_ids = [int(cid) for cid in category_ids_raw]
    except ValueError:
        return jsonify({"error": "Invalid category IDs"}), 400

    try:
        parts = json.loads(parts)  # ensure it's a proper list of dicts
    except Exception:
        return jsonify({"error": "Invalid parts format"}), 400

    result = r2_client.complete_multipart_upload(
        Bucket=settings.r2_bucket_name,
        Key=key,
        UploadId=upload_id,
        MultipartUpload={"Parts": parts}
    )

    video_url = f"{settings.r2_public_url}/{key}"
    with get_db() as db:
        categories = admin_crud.validate_category_ids(db, category_ids)
        if categories is None:
            return jsonify({"error": "Some category IDs are invalid."}), 400

        video_data = {
            "title": title,
            "description": description,
            "categories": categories,
            'video_url': video_url
        }

        created_video = admin_crud.upload_files(db, video_data, thumbnail)
        return jsonify(VideoPublic.model_validate(created_video).model_dump())


@admin_bp.route("/events", methods=["POST"])
@verify_admin
def create_event(current_admin):
    title = request.form.get("title")
    details = request.form.get("details")
    image_file = request.files.get("image_file")

    if not title or not details:
        return jsonify({"error": "Missing title or details"}), 400

    event = EventCreate(title=title, details=details)

    with get_db() as db:
        created_event = admin_crud.create_event(db, event, image_file)
        return jsonify(EventPublic.model_validate(created_event).model_dump())


@admin_bp.route("/events/<int:event_id>/updates", methods=["POST"])
@verify_admin
def add_update_to_event(current_admin, event_id):
    title = request.form.get("title")
    details = request.form.get("details")
    image_file = request.files.get("image_file")

    if not title or not details:
        return jsonify({"error": "Missing title or details"}), 400

    update = LiveUpdateCreate(title=title, details=details)

    with get_db() as db:
        created_update = admin_crud.add_update(db, event_id, update, image_file)
        return jsonify(LiveUpdatePublic.model_validate(created_update).model_dump())


@admin_bp.route("/analytics", methods=["GET"])
@verify_admin
def get_the_analytics(current_admin):
    with get_db() as db:
        analytics = admin_crud.get_analytics(db)
        return jsonify(analytics.model_dump())


@admin_bp.route("/events/<int:event_id>", methods=["DELETE"])
@verify_admin
def close_and_delete_event(current_admin, event_id):
    with get_db() as db:
        result = admin_crud.delete_event(db, event_id)
        return jsonify(result.model_dump())
