from flask import Blueprint, jsonify, request
from app.core.dependencies import get_db
from app.crud import event as events_crud
from app.schemas.event import EventPublicWithRel, LiveUpdatePublicWithEvent
from app.schemas.comment import CommentCreate, CommentPublic
from app.schemas.like import LikePublic

event_bp = Blueprint("event", __name__, url_prefix="/events")


@event_bp.route("/", methods=["GET"])
def list_events():
    with get_db() as db:
        events = events_crud.get_all_live_events(db)
        return jsonify(
            [
                EventPublicWithRel.model_validate(event).model_dump()
                for event in events
            ]
        )


@event_bp.route("/<int:event_id>/updates", methods=["GET"])
def get_event_updates(event_id: int):
    limit = request.args.get("limit", default=10, type=int)
    offset = request.args.get("offset", default=0, type=int)
    with get_db() as db:
        updates = events_crud.get_updates_for_event(db, event_id, limit, offset)
        return jsonify(
            [
                LiveUpdatePublicWithEvent.model_validate(update).model_dump()
                for update in updates
            ]
        )


@event_bp.route("/<int:event_id>", methods=["GET"])
def get_an_event(event_id: int):
    with get_db() as db:
        event = events_crud.get_event(db, event_id)
        if event:
            return jsonify(EventPublicWithRel.model_validate(event).model_dump())

        return jsonify({"detail": "Event not found"}), 404


@event_bp.route("/<int:event_id>/comments", methods=["POST"])
def comment_on_event(event_id: int):
    data = request.get_json()
    content = CommentCreate(**data)
    with get_db() as db:
        comment = events_crud.comment_on_event(db, event_id, content)
        return jsonify(CommentPublic.model_validate(comment).model_dump())


@event_bp.route("/<int:event_id>/comments", methods=["GET"])
def get_event_comments(event_id: int):
    with get_db() as db:
        comments = events_crud.get_comments_for_event(db, event_id)
        return jsonify(
            [
                CommentPublic.model_validate(comment).model_dump()
                for comment in comments
            ]
        )


@event_bp.route("/<int:event_id>/likes", methods=["POST"])
def like_an_event(event_id: int):
    with get_db() as db:
        like = events_crud.like_event(db, event_id)
        return jsonify(LikePublic.model_validate(like).model_dump())


@event_bp.route("/<int:event_id>/likes", methods=["GET"])
def get_event_likes(event_id: int):
    with get_db() as db:
        count = events_crud.get_like_count_for_event(db, event_id)
        return jsonify(count)
