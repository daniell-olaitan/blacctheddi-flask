from sqlmodel import SQLModel


class Analytics(SQLModel):
    total_views: int
    total_updates: int
    total_videos: int
