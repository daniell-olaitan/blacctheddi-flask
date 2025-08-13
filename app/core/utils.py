import jwt
import boto3

from uuid import uuid4
from passlib.context import CryptContext
from config import get_settings
from datetime import timedelta, timezone, datetime
from werkzeug.datastructures import FileStorage
from flask import abort, jsonify
from sqlmodel import SQLModel
from functools import wraps

settings = get_settings()

ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def create_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT token with optional expiry."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt


# File Upload Setup
r2_client = boto3.client(
    "s3",
    endpoint_url=settings.r2_endpoint_url_s3,
    aws_access_key_id=settings.r2_access_key_id,
    aws_secret_access_key=settings.r2_secret_access_key
)


def store_file(file: FileStorage, file_type: str = "videos") -> str:
    """
    Upload a file to R2 storage and return its public URL.

    Args:
        file (FileStorage): File uploaded from Flask request.
        file_type (str): Folder prefix in R2 bucket.

    Returns:
        str: Publicly accessible file URL.
    """
    try:
        # Generate unique key with folder prefix
        key = f"{file_type}/{uuid4()}_{file.filename}"

        # Upload to R2
        r2_client.upload_fileobj(
            Fileobj=file.stream,
            Bucket=settings.r2_bucket_name,
            Key=key,
            ExtraArgs={"ContentType": file.mimetype}
        )

        return f"{settings.r2_public_url}/{key}"

    except Exception as e:
        abort(500, description=f"Upload failed: {str(e)}")
