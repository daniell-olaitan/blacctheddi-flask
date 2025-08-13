from sqlmodel import Session
from app.storage.models import Like
from app.schemas.common import StatusJSON


def unlike_item(db: Session, like_id: int) -> StatusJSON:
    event = db.get(Like, like_id)
    if event:
        db.delete(event)
        db.commit()

    return StatusJSON(status='unliked')
