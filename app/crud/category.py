from sqlmodel import select, Session
from app.storage.models import Category
from app.schemas.category import CategoryPublic


def get_all_categories(db: Session) -> list[Category]:
    categories = db.exec(select(Category)).all()
    return [
        CategoryPublic.model_validate(cat).model_dump()
        for cat in categories
    ]
