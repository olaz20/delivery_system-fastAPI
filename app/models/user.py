from app.core.base import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from .common import Audit
import uuid
import enum
from sqlalchemy.orm import relationship

class UserRole(str, enum.Enum):
    CUSTOMER ="customer"
    ADMIN = "admin"
    DISPATCHER = "dispatcher"

class User(Base, Audit):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4,)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    staff_id = Column(String, unique=True, nullable=True) # e.g STF001
    payments = relationship("Payment", back_populates="customer")
    
    
class TokenBlackList(Base, Audit):
    __tablename__ = "token_blacklist"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    blacklisted_at = Column(DateTime, default=datetime.utcnow)