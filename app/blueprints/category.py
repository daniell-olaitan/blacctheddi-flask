# app/routers/category.py (Flask version)
from flask import Blueprint, jsonify
from app.core.dependencies import get_db
from app.crud import category as category_crud
from app.schemas.category import CategoryPublic

category_bp = Blueprint("category", __name__, url_prefix="/categories")


@category_bp.route("/", methods=["GET"])
def fetch_all_video_categories():
    with get_db() as db:
        categories = category_crud.get_all_categories(db)
        return jsonify(
            [
                CategoryPublic.model_validate(cat).model_dump()
                for cat in categories
            ]
        )
