from flask import Blueprint, jsonify
from app.core.dependencies import safe_db_operation
from app.crud import like as like_crud

like_bp = Blueprint("like", __name__, url_prefix="/likes")


@like_bp.route("/<int:like_id>", methods=["DELETE"])
def unlike_update_or_video(like_id: int):
    try:
        result = safe_db_operation(like_crud.unlike_item, like_id)
        return jsonify(result.model_dump())
    except Exception as e:
        return jsonify({'error': 'failed'}), 500
