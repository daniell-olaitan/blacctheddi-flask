import os
from functools import lru_cache


class Settings:
    secret_key: str = os.getenv("SECRET_KEY", "default-secret")
    database_uri: str = os.getenv("DATABASE_URI", "sqlite:///app.db")
    config: str = os.getenv("CONFIG", "development")
    r2_access_key_id: str = os.getenv("R2_ACCESS_KEY_ID", "")
    r2_secret_access_key: str = os.getenv("R2_SECRET_ACCESS_KEY", "")
    r2_bucket_name: str = os.getenv("R2_BUCKET_NAME", "")
    r2_endpoint_url_s3: str = os.getenv("R2_ENDPOINT_URL_S3", "")
    r2_public_url: str = os.getenv("R2_PUBLIC_URL", "")
    admin_user: str = os.getenv("ADMIN_USER", "admin")
    admin_pwd: str = os.getenv("ADMIN_PWD", "password")
    video_categories: list[str] = [
        "New Releases",
        "Comedy & Satire",
        "News & Affairs",
        "Documentaries & Features",
        "Short Films",
        "Docu series",
        "Movies",
        "Entertainment",
        "Comedy",
        "Innovations",
        "Blog companion"
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
