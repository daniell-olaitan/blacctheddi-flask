import boto3

from app.schemas.event import EventPublic
from app.schemas.update import LiveUpdatePublic
from app.schemas.video import VideoPublic
from sqlmodel import Session, select
from app.storage.models import Admin, Event, LiveUpdate, Video, Category, VideoCategoryLink
from app.schemas.event import EventCreate
from app.schemas.update import LiveUpdateCreate
from werkzeug.datastructures import FileStorage
from app.schemas.common import StatusJSON
from app.schemas.admin import Analytics
from app.core.utils import store_file
from config import get_settings

settings = get_settings()
r2_client = boto3.client(
    "s3",
    endpoint_url=settings.r2_endpoint_url_s3,
    aws_access_key_id=settings.r2_access_key_id,
    aws_secret_access_key=settings.r2_secret_access_key
)


def get_admin(db: Session, username: str) -> bool:
    if db.exec(select(Admin).where(Admin.username == username)).first():
        return True

    return False


def validate_category_ids(db: Session, ids: list) -> bool:
    categories = db.exec(
        select(Category).where(Category.id.in_(ids))
    ).all()

    if len(categories) == len(set(ids)):
        return True

    return False


def create_event(
    db: Session,
    event_data: EventCreate,
    image_file: FileStorage
) -> EventPublic:
    image_url = store_file(image_file, 'images') if image_file else None
    event = Event(
        **event_data.model_dump(),
        image_url=image_url
    )

    db.add(event)
    db.flush()
    db.refresh(event)

    return EventPublic.model_validate(event).model_dump()


def add_update(
    db: Session,
    event_id: int,
    update_data: LiveUpdateCreate,
    image_file: FileStorage
) -> LiveUpdatePublic:
    image_url = store_file(image_file, 'images') if image_file else None
    update = LiveUpdate(
        **update_data.model_dump(),
        event_id=event_id,
        image_url=image_url
    )

    db.add(update)
    db.flush()
    db.refresh(update)

    return LiveUpdatePublic.model_validate(update).model_dump()


def upload_files(
    db: Session,
    video_data: dict,
    thumbnail: FileStorage,
) -> VideoPublic:
    thumbnail_url = store_file(thumbnail, 'images') if thumbnail else None
    video = Video(
        title=video_data['title'],
        description=video_data['description'],
        url=video_data['video_url'],
        thumbnail_url=thumbnail_url
    )

    db.add(video)
    db.flush()
    db.refresh(video)

    for id in video_data['categories']:
        link = VideoCategoryLink(video_id=video.id, category_id=id)
        db.add(link)

    db.flush()
    db.refresh(video)

    return VideoPublic.model_validate(video).model_dump()


def get_analytics(db: Session) -> Analytics:
    videos =  db.exec(select(Video)).all()
    return Analytics(
        total_views=sum(v.views for v in videos),
        total_updates=len(db.exec(select(LiveUpdate)).all()),
        total_videos=len(videos)
    )


def delete_event(db: Session, event_id: int) -> StatusJSON:
    event = db.get(Event, event_id)
    if event:
        db.delete(event)

    return StatusJSON(status='ok')
