from app.core.database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from .common import Audit
import uuid

class User(Base, Audit):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4,)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)

class TokenBlackList(Base, Audit):
    __tablename__ = "token_blacklist"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    blacklisted_at = Column(DateTime, default=datetime.utcnow)