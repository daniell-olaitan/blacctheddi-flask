# app/core/dependencies.py
import jwt
from sqlmodel import Session
from app.storage.database import db_config, get_db, db_retry
from passlib.context import CryptContext
from jwt.exceptions import InvalidTokenError
from flask import request, jsonify
from functools import wraps
from config import get_settings
from app.crud.admin import get_admin

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
engine = db_config.create_engine()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@db_retry()
def safe_db_operation(operation_func, *args, **kwargs):
    """Execute database operation with automatic retry"""
    with get_db() as db:
        return operation_func(db, *args, **kwargs)


def verify_admin(f):
    """
    Decorator to protect routes requiring admin authentication.

    Usage:
        @app.route("/protected")
        @verify_admin
        def protected_route():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Token missing"}), 401

        try:
            payload = jwt.decode(
                token,
                get_settings().secret_key,
                algorithms=[ALGORITHM]
            )
            username = payload.get("sub")
            if username is None:
                return jsonify({"error": "Invalid token"}), 401
        except InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        if not safe_db_operation(get_admin, username=username):
            return jsonify({"error": "Unauthorized"}), 401

        return f(*args, **kwargs)

    return decorated_function
