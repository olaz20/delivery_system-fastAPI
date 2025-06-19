from sqlalchemy import Column, DateTime 
from datetime import datetime

class Audit:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_up = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)