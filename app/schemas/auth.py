from sqlmodel import SQLModel


class LoginRequest(SQLModel):
    username: str
    password: str


class Token(SQLModel):
    access_token: str
    token_type: str


class TokenFull(Token):
    refresh_token: str


class PWDReset(SQLModel):
    old_password: str
    new_password: str
