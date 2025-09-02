from sqlmodel import Session, select
from app.storage.models import Comment, Like
from app.schemas.comment import CommentCreate, CommentPublic
from app.storage.models import LiveUpdate
from app.schemas.like import LikePublic
from app.schemas.event import LiveUpdatePublicWithEvent


def get_update(db: Session, update_id: int) -> LiveUpdatePublicWithEvent | None:
    update = db.get(LiveUpdate, update_id)
    if update:
        return LiveUpdatePublicWithEvent.model_validate(update).model_dump()


def comment_on_update(
    db: Session,
    update_id: int,
    content_data: CommentCreate
) -> CommentPublic:
    comment = Comment(**content_data.model_dump(), update_id=update_id)
    db.add(comment)
    db.flush()
    db.refresh(comment)

    return CommentPublic.model_validate(comment).model_dump()


def like_update(db: Session, update_id: int) -> LikePublic:
    like = Like(update_id=update_id)
    db.add(like)
    db.flush()
    db.refresh(like)

    return LikePublic.model_validate(like).model_dump()


def get_recent_updates(db: Session) -> list[LiveUpdatePublicWithEvent]:
    updates = db.exec(select(LiveUpdate).order_by(LiveUpdate.timestamp.desc())).all()[:3]
    return [
        LiveUpdatePublicWithEvent.model_validate(u).model_dump()
        for u in updates
    ]


def get_like_count_for_update(db: Session, update_id: int) -> int:
    return len(db.exec(select(Like).where(Like.update_id == update_id)).all())


def get_comments_for_update(db: Session, update_id: int) -> list[CommentPublic]:
    comments = db.exec(select(Comment).where(Comment.update_id == update_id)).all()
    return [CommentPublic.model_validate(c).model_dump() for c in comments]
