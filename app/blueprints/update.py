from flask import Blueprint, jsonify, request, abort
from app.core.dependencies import get_db
from app.crud import update as updates_crud
from app.schemas.comment import CommentPublic, CommentCreate
from app.schemas.like import LikePublic
from app.schemas.event import LiveUpdatePublicWithEvent

update_bp = Blueprint("update", __name__, url_prefix="/updates")


@update_bp.route("/recent", methods=["GET"])
def fetch_recent_updates():
    with get_db() as db:
        updates = updates_crud.get_recent_updates(db)
        return jsonify(
            [
                LiveUpdatePublicWithEvent.model_validate(u).model_dump()
                for u in updates
            ]
        )


@update_bp.route("/<int:update_id>", methods=["GET"])
def get_event_update(update_id: int):
    with get_db() as db:
        update = updates_crud.get_update(db, update_id)
        if update:
            return jsonify(LiveUpdatePublicWithEvent.model_validate(update).model_dump())

        abort(404, description="Live update not found")


@update_bp.route("/<int:update_id>/comments", methods=["POST"])
def comment_on_update(update_id: int):
    with get_db() as db:
        content_data = request.get_json()
        content = CommentCreate(**content_data)
        comment = updates_crud.comment_on_update(db, update_id, content)
        return jsonify(CommentPublic.model_validate(comment).model_dump())


@update_bp.route("/<int:update_id>/comments", methods=["GET"])
def get_update_comments(update_id: int):
    with get_db() as db:
        comments = updates_crud.get_comments_for_update(db, update_id)
        return jsonify([CommentPublic.model_validate(c).model_dump() for c in comments])


@update_bp.route("/<int:update_id>/likes", methods=["POST"])
def like_update(update_id: int):
    with get_db() as db:
        like = updates_crud.like_update(db, update_id)
        return jsonify(LikePublic.model_validate(like).model_dump())


@update_bp.route("/<int:update_id>/likes", methods=["GET"])
def get_update_likes(update_id: int):
    with get_db() as db:
        count = updates_crud.get_like_count_for_update(db, update_id)
        return jsonify(count)
