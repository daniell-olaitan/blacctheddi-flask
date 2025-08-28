from sqlmodel import Session, select
from app.storage.models import Video, Comment, Like, VideoCategoryLink, Category
from app.schemas.comment import CommentPublic, CommentCreate
from app.schemas.like import LikePublic
from app.schemas.video import VideoCombined, VideoPublicWithRel
from config import get_settings
from sqlalchemy.orm import selectinload

settings = get_settings()


def get_recent_videos(db: Session) -> list[VideoPublicWithRel]:
    videos = db.exec(select(Video).order_by(Video.timestamp.desc())).all()[:3]
    return [
        VideoPublicWithRel.model_validate(v).model_dump()
        for v in videos
    ]


def get_videos(
    db: Session,
    category_ids: list[int],
    group_by_category: bool
) -> list[VideoPublicWithRel] | dict[str, list[VideoPublicWithRel]]:
    if group_by_category:
        if not category_ids:
            category_ids = [cat.id for cat in db.exec(select(Category)).all()]

        # Eager load videos for the categories
        stmt = (
            select(Category)
            .where(Category.id.in_(category_ids))
            .options(selectinload(Category.videos))
        )
        categories = db.exec(stmt).all()

        grouped = {
            category.name: sorted(
                category.videos,
                key=lambda v: v.timestamp,
                reverse=True
            )
            for category in categories
        }

        return {
            category: [VideoPublicWithRel.model_validate(v).model_dump() for v in vids]
            for category, vids in grouped.items()
        }

    else:
        if category_ids:
            stmt = (
                select(Video)
                .join(VideoCategoryLink, Video.id == VideoCategoryLink.video_id)
                .where(VideoCategoryLink.category_id.in_(category_ids))
                .order_by(Video.timestamp.desc())
                .distinct()
            )
        else:
            stmt = select(Video).order_by(Video.timestamp.desc())

        videos = db.exec(stmt).all()

        return [
            VideoPublicWithRel.model_validate(v).model_dump()
            for v in videos
        ]


def get_video_and_increment_views(db: Session, video_id: int) -> VideoCombined:
    video = db.get(Video, video_id)
    if video:
        video.views += 1
        db.add(video)
        db.flush()
        db.refresh(video)

        videos = db.exec(select(Video).order_by(Video.views.desc())).all()
        related_videos = [v for v in videos if v.id != video_id][:5]
        video_combined = {
            "video": video,
            "related_videos": related_videos
        }

        return VideoCombined.model_validate(video_combined).model_dump()

    return None


def get_like_count_for_video(db: Session, video_id: int) -> int:
    return len(db.exec(select(Like).where(Like.video_id == video_id)).all())


def get_view_count_for_video(db: Session, video_id: int) -> int:
    video = db.get(Video, video_id)
    return video.views if video else 0


def get_related_videos(db: Session, video_id: int) -> list[Video]:
    videos = db.exec(select(Video).order_by(Video.views.desc())).all()
    return [v for v in videos if v.id != video_id][:5]


def comment_on_video(
    db: Session,
    video_id: int,
    content_data: CommentCreate
) -> CommentPublic:
    comment = Comment(**content_data.model_dump(), video_id=video_id)
    db.add(comment)
    db.flush()
    db.refresh(comment)

    return CommentPublic.model_validate(comment).model_dump()


def like_video(db: Session, video_id: int) -> LikePublic:
    like = Like(video_id=video_id)
    db.add(like)

    return LikePublic.model_validate(like).model_dump()


def get_comments_for_video(db: Session, video_id: int) -> list[CommentPublic]:
    comments = db.exec(select(Comment).where(Comment.video_id == video_id)).all()
    return [
        CommentPublic.model_validate(c).model_dump()
        for c in comments
    ]


def get_like_count_for_video(db: Session, video_id: int) -> int:
    return len(db.exec(select(Like).where(Like.video_id == video_id)).all())
