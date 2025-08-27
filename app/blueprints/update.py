from flask import Blueprint, jsonify, request, abort
from app.core.dependencies import safe_db_operation
from app.crud import update as updates_crud
from app.schemas.comment import CommentPublic, CommentCreate

update_bp = Blueprint("update", __name__, url_prefix="/updates")


@update_bp.route("/recent", methods=["GET"])
def fetch_recent_updates():
    try:
        updates = safe_db_operation(updates_crud.get_recent_updates)
        return jsonify(updates)
    except Exception as e:
        return jsonify({'error': 'failed'}), 500


@update_bp.route("/<int:update_id>", methods=["GET"])
def get_event_update(update_id: int):
    try:
        update = safe_db_operation(updates_crud.get_update, update_id)
        if update:
            return jsonify(update)

        return jsonify({'error': 'live update not found'}), 404
    except Exception as e:
        return jsonify({'error': 'failed'}), 500


@update_bp.route("/<int:update_id>/comments", methods=["POST"])
def comment_on_update(update_id: int):
    try:
        content_data = request.get_json()
        content = CommentCreate(**content_data)
        comment = safe_db_operation(updates_crud.comment_on_update, update_id, content)
        return jsonify(comment)
    except Exception as e:
        return jsonify({'error': 'failed'}), 500


@update_bp.route("/<int:update_id>/comments", methods=["GET"])
def get_update_comments(update_id: int):
    try:
        comments = safe_db_operation(updates_crud.get_comments_for_update, update_id)
        return jsonify(comments)
    except Exception as e:
        return jsonify({'error': 'failed'}), 500


@update_bp.route("/<int:update_id>/likes", methods=["POST"])
def like_update(update_id: int):
    try:
        like = safe_db_operation(updates_crud.like_update, update_id)
        return jsonify(like)
    except Exception as e:
        return jsonify({'error': 'failed'}), 500


@update_bp.route("/<int:update_id>/likes", methods=["GET"])
def get_update_likes(update_id: int):
    try:
        count = safe_db_operation(updates_crud.get_like_count_for_update, update_id)
        return jsonify(count)
    except Exception as e:
        return jsonify({'error': 'failed'}), 500
