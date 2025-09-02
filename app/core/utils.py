import jwt
import boto3

from botocore.client import Config
from uuid import uuid4
from passlib.context import CryptContext
from config import get_settings
from datetime import timedelta, timezone, datetime
from werkzeug.datastructures import FileStorage
from flask import abort

ALGORITHM = "HS256"
settings = get_settings()
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
    aws_secret_access_key=settings.r2_secret_access_key,
    config=Config(signature_version="s3v4")
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
        abort(500, description=f"Upload failed")


def delete_file(file_url: str):
    """
    Delete a file from R2 storage given its public URL.

    Args:
        file_url (str): Publicly accessible file URL.
    """
    try:
        base_url = settings.r2_public_url.rstrip("/")
        old_key = file_url.split(f"{base_url}/")[-1]
        r2_client.delete_object(Bucket=settings.r2_bucket_name, Key=old_key)
    except Exception:
        pass  # Continue even if deletion fails
