from flask import Blueprint, jsonify
from app.core.dependencies import safe_db_operation
from app.crud import category as category_crud
category_bp = Blueprint("category", __name__, url_prefix="/categories")


@category_bp.route("", methods=["GET"])
def fetch_all_video_categories():
    try:
        categories = safe_db_operation(category_crud.get_all_categories)
        return jsonify(categories)
    except Exception as e:
        return jsonify({'error': 'Failed'})
