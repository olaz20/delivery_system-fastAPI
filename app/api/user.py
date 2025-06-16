from fastapi import FastAPI, Response , status, Depends, APIRouter, HTTPException
from app.schemas.user import UserCreate, UserOut
from sqlalchemy.orm import Session
from app.core import database
from app.core import security
from app.models.user import User
from app.services.email import send_confirmation_email

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserOut)
async def create_user(user: UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    hashed_password = security.hash(user.password)
    user.password = hashed_password
    token = security.create_email_token(user.email)
    try:
        await send_confirmation_email(user.email, token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
    db_user = User(
        email = user.email,
        first_name = user.first_name,
        last_name = user.last_name,
        password = hashed_password,
        is_verified=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

   
   
    return db_user