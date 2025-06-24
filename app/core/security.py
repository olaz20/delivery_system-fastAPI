from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from app.core.config import settings
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from app.models.user import TokenBlackList, User
from jose import jwt, JWTError
from app.core import database
from fastapi.security import OAuth2PasswordBearer
from app.schemas.user import UserRole
pwd_context = CryptContext(schemes=["bcrypt"],
deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def hash(password: str):
    return pwd_context.hash(password)

def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_email_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode = {"sub": email, "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(lambda: next(__import__("app.core.database").core.database.get_db()))) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Check if token is blacklisted
    if db.query(TokenBlackList).filter(TokenBlackList.token == token).first():
        raise credentials_exception
     
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        if email is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


def refresh_access_token(refresh_token: str, db: Session) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
    )
    
    # Check if refresh token is blacklisted
    if db.query(TokenBlackList).filter(TokenBlackList.token == refresh_token).first():
        raise credentials_exception
    
    try:
        payload = jwt.decode(refresh_token, settings.secret_key, algorithms=["HS256"])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        if email is None or token_type != "refresh":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    
    access_token = create_access_token({"sub": email})
    return {"access_token": access_token, "token_type": "bearer"}


def initialize_default_admin(db: Session):
    admin_email = settings.default_admin_email
    if not db.query(User).filter(User.email == admin_email).first():
        admin = User(
            email=admin_email,
            first_name ="Admin",
            last_name = "Admin",
            password=hash(settings.admin_password),
            is_verified=True,
            role=UserRole.ADMIN,
            staff_id="ADM001"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
    return None

def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, details="Admin access requried")
    return current_user


def get_current_driver(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.DISPATCHER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Driver access required")
    return current_user
