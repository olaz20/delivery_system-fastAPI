from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str

    class Config:
       from_attributes = True

class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    is_verified: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class Login(BaseModel):
    email: EmailStr
    password: str

class RefreshToken(BaseModel):
    refresh_token: str