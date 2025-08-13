from sqlmodel import Session, select
from app.storage.models import Category


def get_all_categories(db: Session) -> list[Category]:
    return db.exec(select(Category)).all()
