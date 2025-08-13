from sqlmodel import Session, select
from app.storage.models import Comment, Like
from app.schemas.comment import CommentCreate
from app.storage.models import LiveUpdate


def get_update(db: Session, update_id: int) -> LiveUpdate:
    return db.get(LiveUpdate, update_id)


def comment_on_update(
    db: Session,
    update_id: int,
    content_data: CommentCreate
) -> Comment:
    comment = Comment(**content_data.model_dump(), update_id=update_id)
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return comment


def like_update(db: Session, update_id: int) -> Like:
    like = Like(update_id=update_id)
    db.add(like)
    db.commit()

    return like


def get_recent_updates(db: Session) -> list[LiveUpdate]:
    return db.exec(select(LiveUpdate).order_by(LiveUpdate.timestamp.desc())).all()[:3]


def get_like_count_for_update(db: Session, update_id: int) -> int:
    return len(db.exec(select(Like).where(Like.update_id == update_id)).all())


def get_comments_for_update(db: Session, update_id: int) -> list[Comment]:
    return db.exec(select(Comment).where(Comment.update_id == update_id)).all()
