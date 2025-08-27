from sqlalchemy.orm import sessionmaker
from sqlmodel import Session
from app.storage.models import SQLModel, create_engine
from config import get_settings

engine = create_engine(get_settings().database_uri)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session
)

def create_db():
    SQLModel.metadata.create_all(engine)
