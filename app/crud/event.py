from sqlmodel import Session, select
from app.schemas.comment import CommentCreate, CommentPublic
from app.storage.models import Event, LiveUpdate, Comment, Like
from app.schemas.event import EventPublicWithRel, LiveUpdatePublicWithEvent
from app.schemas.like import LikePublic


def get_event(db: Session, event_id: int) -> EventPublicWithRel | None:
    event = db.get(Event, event_id)
    if event:
        return EventPublicWithRel.model_validate(event).model_dump()

    return None


def get_all_live_events(db: Session) -> list[EventPublicWithRel]:
    events = db.exec(select(Event).where(Event.status == "live")).all()
    return [
        EventPublicWithRel.model_validate(event).model_dump()
        for event in events
    ]


def comment_on_event(
    db: Session,
    event_id: int,
    content_data: CommentCreate
) -> CommentPublic:
    comment = Comment(**content_data.model_dump(), event_id=event_id)
    db.add(comment)
    db.flush()
    db.refresh(comment)

    return CommentPublic.model_validate(comment).model_dump()


def like_event(db: Session, event_id: int) -> LikePublic:
    like = Like(event_id=event_id)
    db.add(like)

    return LikePublic.model_validate(like).model_dump()


def get_like_count_for_event(db: Session, event_id: int) -> int:
    return len(db.exec(select(Like).where(Like.event_id == event_id)).all())


def get_comments_for_event(db: Session, event_id: int) -> list[Comment]:
    comments = db.exec(select(Comment).where(Comment.event_id == event_id)).all()
    return [
        CommentPublic.model_validate(comment).model_dump()
        for comment in comments
    ]


def get_updates_for_event(
    db: Session,
    event_id: int,
    limit: int,
    offset: int
) -> list[LiveUpdate]:
    updates = db.exec(
        select(LiveUpdate)
        .where(LiveUpdate.event_id == event_id)
        .order_by(LiveUpdate.timestamp.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return [
        LiveUpdatePublicWithEvent.model_validate(update).model_dump()
        for update in updates
    ]
