from pydantic import BaseModel, EmailStr
from uuid import UUID
from enum import Enum
from typing import Optional, Any
from datetime import datetime


class UserRole(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    DISPATCHER = "dispatcher"



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
    role: UserRole
    staff_id: str | None


    class Config:
        from_attributes = True

class StaffCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str 
    password: str
    role: UserRole
    staff_id: str
    department: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class StandardResponse(BaseModel):
    status: str
    code: int
    message: str
    data: Token  # <- this wraps the token
    request_id: UUID
    errors: Optional[Any] = None
    timestamp: datetime




class Login(BaseModel):
    email: EmailStr
    password: str

class RefreshToken(BaseModel):
    refresh_token: str