from flask import Blueprint, jsonify, request
from app.core.dependencies import safe_db_operation
from app.crud import event as events_crud
from app.schemas.comment import CommentCreate

event_bp = Blueprint("event", __name__, url_prefix="/events")


@event_bp.route("", methods=["GET"])
def list_events():
    try:
        events = safe_db_operation(events_crud.get_all_live_events)
        return jsonify(events)
    except Exception as e:
        return jsonify({'error': 'failed'}), 500


@event_bp.route("/<int:event_id>/updates", methods=["GET"])
def get_event_updates(event_id: int):
    limit = request.args.get("limit", default=10, type=int)
    offset = request.args.get("offset", default=0, type=int)
    try:
        updates = safe_db_operation(events_crud.get_updates_for_event, event_id, limit, offset)
        return jsonify(updates)
    except Exception as e:
        return jsonify({'error': 'failed'}), 500


@event_bp.route("/<int:event_id>", methods=["GET"])
def get_an_event(event_id: int):
    try:
        event = safe_db_operation(events_crud.get_event, event_id)
        if event:
            return jsonify(event)

        return jsonify({"detail": "Event not found"}), 404
    except Exception as e:
        return jsonify({'error': 'failed'}), 500


@event_bp.route("/<int:event_id>/comments", methods=["POST"])
def comment_on_event(event_id: int):
    data = request.get_json()
    content = CommentCreate(**data)
    try:
        comment = safe_db_operation(events_crud.comment_on_event, event_id, content)
        return jsonify(comment)
    except Exception as e:
        return jsonify({'error': 'failed'}), 500


@event_bp.route("/<int:event_id>/comments", methods=["GET"])
def get_event_comments(event_id: int):
    try:
        comments = safe_db_operation(events_crud.get_comments_for_event, event_id)
        return jsonify(comments)
    except Exception as e:
        return jsonify({'error': 'failed'}), 500


@event_bp.route("/<int:event_id>/likes", methods=["POST"])
def like_an_event(event_id: int):
    try:
        like = safe_db_operation(events_crud.like_event, event_id)
        return jsonify(like)
    except Exception as e:
        return jsonify({'error': 'failed'}), 500


@event_bp.route("/<int:event_id>/likes", methods=["GET"])
def get_event_likes(event_id: int):
    try:
        count = safe_db_operation(events_crud.get_like_count_for_event, event_id)
        return jsonify(count)
    except Exception as e:
        return jsonify({'error': 'failed'}), 500
