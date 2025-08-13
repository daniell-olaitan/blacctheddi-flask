from app.storage.models import SQLModel, create_engine
from config import get_settings

engine = create_engine(get_settings().database_uri)


def create_db():
    SQLModel.metadata.create_all(engine)
