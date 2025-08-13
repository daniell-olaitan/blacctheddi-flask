from sqlmodel import Field, SQLModel
from datetime import timezone, datetime


class LikeBase(SQLModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_id: int | None = Field(default=None, foreign_key="events.id", ondelete='CASCADE')
    update_id: int | None = Field(default=None, foreign_key="liveupdates.id", ondelete='CASCADE')
    video_id: int | None = Field(default=None, foreign_key="videos.id", ondelete='CASCADE')


class LikePublic(LikeBase):
    id: int
