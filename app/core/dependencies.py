# app/core/dependencies.py
import jwt
from sqlmodel import Session
from app.storage.database import engine
from passlib.context import CryptContext
from jwt.exceptions import InvalidTokenError
from flask import request, jsonify
from functools import wraps
from config import get_settings
from app.storage.database import SessionLocal
from app.crud.admin import get_admin
from contextlib import contextmanager

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
def get_db() -> Session:
    """Return a database session."""
    return Session(engine)


def verify_admin(f):
    """
    Decorator to protect routes requiring admin authentication.

    Usage:
        @app.route("/protected")
        @verify_admin
        def protected_route(admin):
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

        with get_db() as db:
            admin = get_admin(db=db, username=username)
            if admin is None:
                return jsonify({"error": "Unauthorized"}), 401

        # Pass the admin object to the route handler
        return f(admin, *args, **kwargs)

    return decorated_function
