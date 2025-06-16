from app.core.database import Base
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from .common import Audit


class User(Base, Audit):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)