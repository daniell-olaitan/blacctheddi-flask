from flask import Blueprint, jsonify, request, abort
from app.core.dependencies import get_db
from app.crud import video as videos_crud
from app.schemas.comment import CommentPublic, CommentCreate
from app.schemas.like import LikePublic
from app.schemas.video import VideoCombined, VideoPublicWithRel

video_bp = Blueprint("video", __name__, url_prefix="/videos")


@video_bp.route("/ungrouped", methods=["GET"])
def get_ungrouped_videos():
    category_ids = request.args.getlist("category_ids", type=int) or None
    with get_db() as db:
        videos = videos_crud.get_videos(db, category_ids, group_by_category=False)
        return jsonify(
            [
                VideoPublicWithRel.model_validate(v).model_dump()
                for v in videos
            ]
        )


@video_bp.route("/grouped", methods=["GET"])
def get_grouped_videos():
    category_ids = request.args.getlist("category_ids", type=int) or None
    with get_db() as db:
        grouped = videos_crud.get_videos(db, category_ids, group_by_category=True)
        return jsonify({
            category: [VideoPublicWithRel.model_validate(v).model_dump() for v in vids]
            for category, vids in grouped.items()
        })


@video_bp.route("/recent", methods=["GET"])
def fetch_recent_videos():
    with get_db() as db:
        videos = videos_crud.get_recent_videos(db)
        return jsonify(
            [
                VideoPublicWithRel.model_validate(v).model_dump()
                for v in videos
            ]
        )


@video_bp.route("/<int:video_id>", methods=["GET"])
def get_a_video(video_id: int):
    with get_db() as db:
        video = videos_crud.get_video_and_increment_views(db, video_id)
        if video:
            return jsonify(VideoCombined.model_validate(video).model_dump())

        abort(404, description="Video not found")


@video_bp.route("/<int:video_id>/views", methods=["GET"])
def get_video_views(video_id: int):
    with get_db() as db:
        count = videos_crud.get_view_count_for_video(db, video_id)
        return jsonify(count)


@video_bp.route("/<int:video_id>/comments", methods=["POST"])
def comment_on_video(video_id: int):
    with get_db() as db:
        content_data = request.get_json()
        content = CommentCreate(**content_data)
        comment = videos_crud.comment_on_video(db, video_id, content)
        return jsonify(CommentPublic.model_validate(comment).model_dump())


@video_bp.route("/<int:video_id>/comments", methods=["GET"])
def get_video_comments(video_id: int):
    with get_db() as db:
        comments = videos_crud.get_comments_for_video(db, video_id)
        return jsonify(
            [
                CommentPublic.model_validate(c).model_dump()
                for c in comments
            ]
        )


@video_bp.route("/<int:video_id>/likes", methods=["POST"])
def like_video(video_id: int):
    with get_db() as db:
        like = videos_crud.like_video(db, video_id)
        return jsonify(LikePublic.model_validate(like).model_dump())


@video_bp.route("/<int:video_id>/likes", methods=["GET"])
def get_video_likes(video_id: int):
    with get_db() as db:
        count = videos_crud.get_like_count_for_video(db, video_id)
        return jsonify(count)
