from flask import Blueprint, request, jsonify
from app.core.dependencies import get_db, verify_admin
from app.crud import admin as admin_crud
from app.schemas.event import EventCreate, EventPublic
from app.schemas.update import LiveUpdateCreate, LiveUpdatePublic
from app.schemas.video import VideoPublic

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


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


@admin_bp.route("/videos", methods=["POST"])
@verify_admin
def upload_video(current_admin):
    title = request.form.get("title")
    description = request.form.get("description")
    category_ids_raw = request.form.getlist("category_ids")
    thumbnail = request.files.get("thumbnail")
    video_file = request.files.get("video_file")

    if not title or not description or not category_ids_raw or not thumbnail or not video_file:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        category_ids = [int(cid) for cid in category_ids_raw]
    except ValueError:
        return jsonify({"error": "Invalid category IDs"}), 400

    with get_db() as db:
        categories = admin_crud.validate_category_ids(db, category_ids)
        if categories is None:
            return jsonify({"error": "Some category IDs are invalid."}), 400

        video_data = {
            "title": title,
            "description": description,
            "categories": categories
        }

        created_video = admin_crud.upload_files(db, video_data, thumbnail, video_file)
        return jsonify(VideoPublic.model_validate(created_video).model_dump())


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
