from sqlalchemy.orm import relationship
from app.core.base import Base
from app.models.common import Audit
from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
import uuid



class Payment(Base, Audit):
    __tablename__ = "payments"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4, nullable=False)
    reference = Column(String, unique=True, index=True)
    amount = Column(Float)
    status = Column(String, default="pending")
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    
    customer = relationship("User", back_populates="payments")
    orders = relationship("Order", back_populates="payment", foreign_keys="Order.payment_id")