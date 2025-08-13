from flask import Blueprint, jsonify
from app.core.dependencies import get_db
from app.crud import like as like_crud
from app.schemas.common import StatusJSON

like_bp = Blueprint("like", __name__, url_prefix="/likes")


@like_bp.route("/<int:like_id>", methods=["DELETE"])
def unlike_update_or_video(like_id: int):
    with get_db() as db:
        result = like_crud.unlike_item(db, like_id)
        return jsonify(result.model_dump())
