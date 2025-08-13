from sqlmodel import SQLModel, Field


class CategoryBase(SQLModel):
    name: str = Field(index=True, unique=True)


class CategoryPublic(CategoryBase):
    id: int
