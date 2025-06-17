from fastapi import HTTPException, status, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.email import send_confirmation_email
from app.core import security, database
from app.models.user import User, TokenBlackList
from jose import jwt, JWTError
from app.core.config import settings
from app.schemas.user import Login, RefreshToken
from app.core.security import create_access_token, create_refresh_token, verify, oauth2_scheme, refresh_access_token


async def send_verfication_email(email: str):
    token = security.create_email_token(email)
    try:
        await send_confirmation_email(email, token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")







async def create_user_service(user: UserCreate, db: Session):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        if db_user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
            
        else:
            await send_verfication_email(user.email)
            return db_user
    hashed_password = security.hash(user.password)
    user.password = hashed_password
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
    await send_verfication_email(user.email)
    return db_user

async def verify_email_service(token: str, db: Session):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
        
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= "Invalid token")
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, details="User not found")
    if db_user.is_verified:
        return {"message": "Email already verified"}
    db_user.is_verified = True
    db.commit()
    return {"message": "Email verified successfully"}


def login_user_service(user_credentials: Login, db:Session = Depends(database.get_db)):
    user = db.query(User).filter(User.email == user_credentials.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if not user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")
    
    if not verify(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

def logout_user_service(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    # Add token to blacklist
    db_token = TokenBlackList(token=token)
    db.add(db_token)
    db.commit()
    return {"message": "Successfully logged out"}

def refresh_token_service(refresh_token: RefreshToken, db: Session = Depends(database.get_db)):
    token_data = refresh_access_token(refresh_token.refresh_token, db)
    return token_data
