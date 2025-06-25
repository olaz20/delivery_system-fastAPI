from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, JSON, DateTime, func, Boolean
import enum
from app.core.base import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.models.common import Audit
from uuid import uuid4




class OrderStatus(str, enum.Enum):
    CREATED = "created"
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    FAILED = "failed"

class Order(Base, Audit):
    __tablename__ = "orders"
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4)
    customer_id=Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"))
    is_verified = Column(Boolean, default=False)
    pickup_location=Column(JSONB, nullable=False)
    recipient_details = Column(JSONB, nullable=False)
    package_details = Column(JSONB, nullable=False)
    goods_image_path = Column(String, nullable=True)
    delivery_location=Column(JSONB, nullable=False)
    price = Column(Float, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.CREATED, nullable=False)

    customer = relationship("User", foreign_keys=[customer_id])
    driver = relationship("User", foreign_keys=[driver_id])
    status_history = relationship("OrderStatusHistory", back_populates="order")
    proof_of_delivery = relationship("ProofOfDelivery", uselist=False, back_populates="order")

class OrderStatusHistory(Base, Audit):
    __tablename__ = "order_status_history"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    order_id= Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(OrderStatus), nullable=False)
    changed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=func.now())
    order = relationship("Order", back_populates="status_history")
    changed_by = relationship("User")

class ProofOfDelivery(Base, Audit):
    __tablename__ = "proof_of_delivery"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    order_id=Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True)
    image_path = Column(String, nullable=True)
    signature_path=Column(String, nullable=True)
    uploaded_path=Column(DateTime, default=func.now())
    order = relationship("Order", back_populates="proof_of_delivery")



class DriverLocation(Base, Audit):
    __tablename__ = "driver_locations"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    driver_id=Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    location=Column(JSONB, nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
