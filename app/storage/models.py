import boto3

from sqlmodel import SQLModel, Field, create_engine, Relationship
from sqlalchemy import Column, TEXT, event
from urllib.parse import urlparse
from config import get_settings
from app.schemas.event import EventBase
from app.schemas.update import LiveUpdateBase
from app.schemas.comment import CommentBase
from app.schemas.like import LikeBase
from app.schemas.video import VideoBase
from app.schemas.category import CategoryBase

settings = get_settings()
engine = create_engine(settings.database_uri)


class VideoCategoryLink(SQLModel, table=True):
    video_id: int | None = Field(default=None, foreign_key="videos.id", primary_key=True)
    category_id: int | None = Field(default=None, foreign_key="categories.id", primary_key=True)


class Admin(SQLModel, table=True):
    __tablename__ = 'admins'

    id: int | None = Field(default=None, primary_key=True)
    username: str
    password: str


class Event(EventBase, table=True):
    __tablename__ = 'events'

    id: int | None = Field(default=None, primary_key=True)
    details: str = Field(sa_column=Column(TEXT, nullable=False))

    updates: list["LiveUpdate"] = Relationship(back_populates="event", cascade_delete=True)
    comments: list["Comment"] = Relationship(back_populates="event", cascade_delete=True)
    likes: list["Like"] = Relationship(back_populates="event", cascade_delete=True)


class LiveUpdate(LiveUpdateBase, table=True):
    __tablename__ = 'liveupdates'

    id: int | None = Field(default=None, primary_key=True)
    details: str = Field(sa_column=Column(TEXT, nullable=False))

    event: Event | None = Relationship(back_populates="updates")
    comments: list["Comment"] = Relationship(back_populates="update", cascade_delete=True)
    likes: list["Like"] = Relationship(back_populates="update", cascade_delete=True)


class Video(VideoBase, table=True):
    __tablename__ = 'videos'

    id: int | None = Field(default=None, primary_key=True)
    description: str = Field(sa_column=Column(TEXT, nullable=False))

    comments: list["Comment"] = Relationship(back_populates="video", cascade_delete=True)
    likes: list["Like"] = Relationship(back_populates="video", cascade_delete=True)
    categories: list["Category"] = Relationship(back_populates="videos", link_model=VideoCategoryLink)


class Category(CategoryBase, table=True):
    __tablename__ = 'categories'
    id: int | None = Field(default=None, primary_key=True)

    videos: list["Video"] = Relationship(back_populates="categories", link_model=VideoCategoryLink)


class Comment(CommentBase, table=True):
    __tablename__ = 'comments'

    id: int | None = Field(default=None, primary_key=True)
    content: str = Field(sa_column=Column(TEXT, nullable=False))

    update: LiveUpdate | None = Relationship(back_populates="comments")
    event: Event | None = Relationship(back_populates="comments")
    video: Video | None = Relationship(back_populates="comments")


class Like(LikeBase, table=True):
    __tablename__ = 'likes'
    id: int | None = Field(default=None, primary_key=True)

    event: Event | None = Relationship(back_populates="likes")
    update: LiveUpdate | None = Relationship(back_populates="likes")
    video: Video | None = Relationship(back_populates="likes")


r2_client = boto3.client(
    "s3",
    endpoint_url=settings.r2_endpoint_url_s3,
    aws_access_key_id=settings.r2_access_key_id,
    aws_secret_access_key=settings.r2_secret_access_key
)

# Utility to delete a file from R2 given its public URL
def delete_r2_file_from_url(url: str):
    """Delete a file from Cloudflare R2 given its public URL."""
    if not url:
        return
    try:
        parsed = urlparse(url)
        key = parsed.path.lstrip("/")
        r2_client.delete_object(
            Bucket=settings.r2_bucket_name,
            Key=key
        )
    except Exception as e:
        print(f"[R2 DELETE ERROR] Could not delete {url}: {e}")


# Generic cleanup event registration
def register_r2_cleanup(model, url_fields: list[str]):
    @event.listens_for(model, "after_delete")
    def _cleanup_media(mapper, connection, target):
        for field in url_fields:
            url = getattr(target, field, None)
            delete_r2_file_from_url(url)


# Attach cleanup to models
register_r2_cleanup(Video, ["thumbnail_url", "url"])
register_r2_cleanup(LiveUpdate, ["image_url"])
register_r2_cleanup(Event, ["image_url"])
