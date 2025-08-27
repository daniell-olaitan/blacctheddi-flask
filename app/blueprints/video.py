from flask import Blueprint, jsonify, request
from app.core.dependencies import safe_db_operation
from app.crud import video as videos_crud
from app.schemas.comment import  CommentCreate

video_bp = Blueprint("video", __name__, url_prefix="/tvs")


@video_bp.route("/ungrouped", methods=["GET"])
def get_ungrouped_videos():
    category_ids = request.args.getlist("category_ids", type=int) or None
    try:
        videos = safe_db_operation(videos_crud.get_videos, category_ids, group_by_category=False)
        return jsonify(videos)
    except Exception as e:
        return jsonify({'error': 'failed'}), 500


@video_bp.route("/grouped", methods=["GET"])
def get_grouped_videos():
    category_ids = request.args.getlist("category_ids", type=int) or None
    try:
        videos = safe_db_operation(videos_crud.get_videos, category_ids, group_by_category=True)
        return jsonify(videos)
    except Exception as e:
        return jsonify({'error': 'failed'}), 500


@video_bp.route("/recent", methods=["GET"])
def fetch_recent_videos():
    try:
        videos = safe_db_operation(videos_crud.get_recent_videos)
        return jsonify(videos)
    except Exception as e:
        return jsonify({'error': 'failed'}), 500


@video_bp.route("/<int:video_id>", methods=["GET"])
def get_a_video(video_id: int):
    try:
        video = safe_db_operation(videos_crud.get_video_and_increment_views, video_id)
        if video:
            return jsonify(video)

        return jsonify({'error': "Video not found"}), 404
    except Exception as e:
        return jsonify({'error': 'failed'}), 500


@video_bp.route("/<int:video_id>/views", methods=["GET"])
def get_video_views(video_id: int):
    try:
        count = safe_db_operation(videos_crud.get_view_count_for_video, video_id)
        return jsonify(count)
    except Exception as e:
        return jsonify({'error': 'failed'}), 500


@video_bp.route("/<int:video_id>/comments", methods=["POST"])
def comment_on_video(video_id: int):
    try:
        content_data = request.get_json()
        content = CommentCreate(**content_data)
        comment = safe_db_operation(videos_crud.comment_on_video, video_id, content)
        return jsonify(comment)
    except Exception as e:
        return jsonify({'error': 'failed'}), 500


@video_bp.route("/<int:video_id>/comments", methods=["GET"])
def get_video_comments(video_id: int):
    try:
        comments = safe_db_operation(videos_crud.get_comments_for_video, video_id)
        return jsonify(comments)
    except Exception as e:
        return jsonify({'error': 'failed'}), 500


@video_bp.route("/<int:video_id>/likes", methods=["POST"])
def like_video(video_id: int):
    try:
        like = safe_db_operation(videos_crud.like_video, video_id)
        return jsonify(like)
    except Exception as e:
        return jsonify({'error': 'failed'}), 500


@video_bp.route("/<int:video_id>/likes", methods=["GET"])
def get_video_likes(video_id: int):
    try:
        count = safe_db_operation(videos_crud.get_like_count_for_video, video_id)
        return jsonify(count)
    except Exception as e:
        return jsonify({'error': 'failed'}), 500
