from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str

    class Config:
       orm_mode = True