from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"],
deprecated="auto")

def hash(password: str):
    return pwd_context.hash(password)

def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_email_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode = {"sub": email, "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")