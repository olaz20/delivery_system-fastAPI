from fastapi import FastAPI, Response , status, Depends, APIRouter, HTTPException
from schemas.user import UserCreate
from sqlalchemy.orm import Session
from core.database import get_db
from core import security
from models.user import User
from app.services.email import send_confirmation_email

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    hashed_password = security.hash(user.password)
    user.password = hashed_password
    db_user = User(
        email = user.email,
        name = user.name,
        hashed_password=hashed_password,
        is_verified=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    token = security.create_email_token(user.email)
    await send_confirmation_email(user.email, token)
    return db_user