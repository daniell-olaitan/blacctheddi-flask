import os
import time
import logging

from app.storage.models import SQLModel
from config import get_settings
from sqlalchemy import create_engine, text
from sqlmodel import Session
from contextlib import contextmanager
from typing import Generator


class DatabaseConfig:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.is_production = os.getenv('CONFIG') == 'deployment'

    def create_engine(self):
        """Create a new engine instance - no connection pooling for shared hosting"""
        if self.is_production:
            # Production settings for shared hosting - NO POOLING
            return create_engine(
                self.database_url,
                poolclass=None,  # No connection pool
                # Connection settings for shared hosting
                connect_args={
                    "charset": "utf8mb4",
                    "autocommit": False,
                    "connect_timeout": 10,
                    "read_timeout": 30,
                    "write_timeout": 30,
                    "sql_mode": "TRADITIONAL"  # Prevent command out of sync
                },
                # Engine settings
                echo=False,
                future=True,
            )
        else:
            # Development settings
            return create_engine(
                self.database_url,
                echo=False,
                future=True,
            )


# Global database configuration
db_config = DatabaseConfig(get_settings().database_uri)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Get a fresh database session for each request.
    This completely avoids connection pooling issues.
    """
    engine = None
    session = None

    try:
        # Create a fresh engine for each request
        engine = db_config.create_engine()

        # Test the connection before creating session
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # Create session
        session = Session(engine)

        yield session

        # Commit if no errors
        session.commit()

    except Exception as e:
        if session:
            try:
                session.rollback()
            except:
                pass  # Ignore rollback errors
        raise e

    finally:
        # Clean up resources
        if session:
            try:
                session.close()
            except:
                pass  # Ignore close errors

        if engine:
            try:
                engine.dispose()
            except:
                pass  # Ignore disposal errors


# Alternative function for dependency injection
# def get_db():
#     """Use this in your route dependencies"""
#     return get_database_session()


# Retry decorator for database operations
def db_retry(max_attempts=5, delay=1):
    """Decorator to retry database operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_message = str(e).lower()

                    # Check if it's a retryable error
                    retryable_errors = [
                        'mysql server has gone away',
                        'lost connection to mysql server',
                        'command out of sync',
                        'broken pipe',
                        'connection was killed'
                    ]

                    is_retryable = any(error in error_message for error in retryable_errors)
                    if is_retryable and attempt < max_attempts - 1:
                        logging.warning(f"Database error on attempt {attempt + 1}: {e}")
                        time.sleep(delay * (2 ** attempt))  # Exponential backoff
                        continue
                    else:
                        break

            raise last_exception
        return wrapper
    return decorator


def create_db():
    SQLModel.metadata.create_all(db_config.create_engine())
