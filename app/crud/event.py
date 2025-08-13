from sqlmodel import Session, select
from app.schemas.comment import CommentCreate
from app.storage.models import Event, LiveUpdate, Comment, Like


def get_event(db: Session, event_id: int) -> Event:
    return db.get(Event, event_id)


def get_all_live_events(db: Session) -> list[Event]:
    return db.exec(select(Event).where(Event.status == "live")).all()


def comment_on_event(
    db: Session,
    event_id: int,
    content_data: CommentCreate
) -> Comment:
    comment = Comment(**content_data.model_dump(), event_id=event_id)
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return comment


def like_event(db: Session, event_id: int) -> Like:
    like = Like(event_id=event_id)
    db.add(like)
    db.commit()

    return like


def get_like_count_for_event(db: Session, event_id: int) -> int:
    return len(db.exec(select(Like).where(Like.event_id == event_id)).all())


def get_comments_for_event(db: Session, event_id: int) -> list[Comment]:
    return db.exec(select(Comment).where(Comment.event_id == event_id)).all()


def get_updates_for_event(
    db: Session,
    event_id: int,
    limit: int,
    offset: int
) -> list[LiveUpdate]:
    return db.exec(
        select(LiveUpdate)
        .where(LiveUpdate.event_id == event_id)
        .order_by(LiveUpdate.timestamp.desc())
        .offset(offset)
        .limit(limit)
    ).all()
