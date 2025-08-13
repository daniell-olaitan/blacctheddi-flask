import jwt
from flask import Blueprint, request, jsonify
from datetime import timedelta

from app.schemas.auth import Token, PWDReset, TokenFull, LoginRequest
from app.core.utils import create_token, verify_password, get_password_hash, get_settings
from app.schemas.common import StatusJSON
from app.core.dependencies import get_db, verify_admin
from app.crud.admin import get_admin
from app.storage.models import Admin

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
settings = get_settings()


@auth_bp.route("/login", methods=["POST"])
def login_for_access_token():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    try:
        payload = LoginRequest(**data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    with get_db() as db:
        admin = get_admin(db=db, username=payload.username)
        if not admin:
            return jsonify({"detail": "Incorrect username"}), 401

        if not verify_password(payload.password, admin.password):
            return jsonify({"detail": "Incorrect password"}), 401

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_token(
            data={"sub": admin.username}, expires_delta=access_token_expires
        )

        refresh_token = create_token(
            data={"sub": admin.username}, expires_delta=timedelta(days=7)
        )

        token_data = TokenFull(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
        return jsonify(token_data.model_dump())


@auth_bp.route("/refresh", methods=["POST"])
def refresh_token():
    data = request.get_json()
    if not data or "refresh_token" not in data:
        return jsonify({"error": "Missing refresh_token"}), 400

    refresh_token_value = data["refresh_token"]

    try:
        payload = jwt.decode(
            refresh_token_value, settings.secret_key, algorithms=[ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            return jsonify({"detail": "Invalid token"}), 401

        # Issue new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_token(
            data={"sub": username}, expires_delta=access_token_expires
        )

        token_data = Token(access_token=access_token, token_type="bearer")
        return jsonify(token_data.model_dump())

    except Exception:
        return jsonify({"detail": "Invalid or expired refresh token"}), 401


@auth_bp.route("/change-password", methods=["POST"])
@verify_admin
def change_admin_password(current_admin: Admin):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    try:
        user_details = PWDReset(**data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    with get_db() as db:
        if verify_password(user_details.old_password, current_admin.password):
            current_admin.password = get_password_hash(user_details.new_password)
            db.add(current_admin)
            db.commit()
            return jsonify(StatusJSON(status="ok").model_dump())

        return jsonify({"detail": "Incorrect old password"}), 400
