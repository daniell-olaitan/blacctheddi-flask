import boto3
import json

from botocore.client import Config
from uuid import uuid4
from flask import Blueprint, request, jsonify
from app.core.dependencies import verify_admin, safe_db_operation
from app.crud import admin as admin_crud
from app.schemas.event import EventCreate
from app.schemas.update import LiveUpdateCreate
from config import get_settings

settings = get_settings()
r2_client = boto3.client(
    "s3",
    endpoint_url=settings.r2_endpoint_url_s3,
    aws_access_key_id=settings.r2_access_key_id,
    aws_secret_access_key=settings.r2_secret_access_key,
    config=Config(signature_version="s3v4")
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/videos/multipart/initiate", methods=["POST"])
@verify_admin
def initiate_video_upload():
    data = request.json
    filename = data.get("filename")
    content_type = data.get("content_type", "video/mp4")

    if not filename:
        return jsonify({"error": "Filename required"}), 400

    key = f"videos/{uuid4()}_{filename}"

    try:
        response = r2_client.create_multipart_upload(
            Bucket=settings.r2_bucket_name,
            Key=key,
            ContentType=content_type
        )
    except Exception as e:
        return jsonify({'error': 'failed'}), 500

    return jsonify({
        "upload_id": response["UploadId"],
        "key": key
    })


@admin_bp.route("/videos/multipart/sign-part", methods=["POST"])
@verify_admin
def sign_video_part():
    data = request.json
    key = data.get("key")
    upload_id = data.get("upload_id")
    try:
        part_number = int(data.get("part_number"))
    except Exception as e:
        return jsonify({'error': 'invalid part number'}), 400


    if not key or not upload_id or not part_number:
        return jsonify({"error": "Missing key, upload_id, or part_number"}), 400

    try:
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
    except Exception as e:
        return jsonify({'error': 'failed'}), 500

    return jsonify({"url": url})


@admin_bp.route("/videos", methods=["POST"])
@verify_admin
def complete_video_upload():
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

    try:
        result = r2_client.complete_multipart_upload(
            Bucket=settings.r2_bucket_name,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={"Parts": parts}
        )
    except Exception:
        return jsonify({'error': 'failed'}), 500

    video_url = f"{settings.r2_public_url}/{key}"
    try:
        if not safe_db_operation(admin_crud.validate_category_ids, category_ids):
            return jsonify({"error": "Some category IDs are invalid."}), 400

        video_data = {
            "title": title,
            "description": description,
            "categories": category_ids,
            'video_url': video_url
        }

        created_video = safe_db_operation(admin_crud.upload_files, video_data, thumbnail)
        return jsonify(created_video)
    except Exception as e:
        return jsonify({'error': 'failed'}), 500


@admin_bp.route("/events", methods=["POST"])
@verify_admin
def create_event():
    title = request.form.get("title")
    details = request.form.get("details")
    image_file = request.files.get("image_file")

    if not title or not details:
        return jsonify({"error": "Missing title or details"}), 400

    event = EventCreate(title=title, details=details)

    try:
        created_event = safe_db_operation(admin_crud.create_event, event, image_file)
        return jsonify(created_event)
    except Exception as e:
        return jsonify({'error': 'failed'}), 500


@admin_bp.route("/events/<int:event_id>/updates", methods=["POST"])
@verify_admin
def add_update_to_event(event_id):
    title = request.form.get("title")
    details = request.form.get("details")
    image_file = request.files.get("image_file")

    if not title or not details:
        return jsonify({"error": "Missing title or details"}), 400

    update = LiveUpdateCreate(title=title, details=details)

    try:
        created_update = safe_db_operation(admin_crud.add_update, event_id, update, image_file)
        return jsonify(created_update)
    except Exception as e:
        return jsonify({'error': 'failed'}), 500


@admin_bp.route("/analytics", methods=["GET"])
@verify_admin
def get_the_analytics():
    try:
        analytics = safe_db_operation(admin_crud.get_analytics)
        return jsonify(analytics.model_dump())
    except Exception as e:
        return jsonify({'error': 'failed'}), 500


@admin_bp.route("/events/<int:event_id>", methods=["DELETE"])
@verify_admin
def close_and_delete_event(event_id):
    try:
        result = safe_db_operation(admin_crud.delete_event, event_id)
        return jsonify(result.model_dump())
    except Exception as e:
        return jsonify({'error': 'failed'}), 500
