from sqlmodel import Field, SQLModel
from datetime import timezone, datetime
from app.schemas.like import LikePublic
from app.schemas.comment import CommentPublic


class LiveUpdateCreate(SQLModel):
    title: str
    details: str


class LiveUpdateBase(LiveUpdateCreate):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_id: int = Field(foreign_key="events.id", ondelete='CASCADE')
    image_url: str | None = None


class LiveUpdatePublic(LiveUpdateBase):
    id: int


class LiveUpdatePublicWithRel(LiveUpdatePublic):
    comments: list[CommentPublic]
    likes: list[LikePublic]
