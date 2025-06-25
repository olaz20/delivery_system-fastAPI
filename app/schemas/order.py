from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
from .user import UserOut
from uuid import UUID


class OrderStatus(str, Enum):
    CREATED="created"
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    FAILED = "failed"

class GeoPoint(BaseModel):
    type: str = Field("Point", Literal=True)
    coordinates: List[float]

class PackageDetails(BaseModel):
    weight_kg:float
    dimensions_cm: list[float] = Field(..., min_items=1)
    description: Optional[str] = None

class RecipientDetails(BaseModel):
    name: str
    phone: str  # e.g., "+1234567890"

class OrderCreate(BaseModel):
    pickup_location: GeoPoint
    delivery_location: GeoPoint
    package_details: PackageDetails
    recipient_details: RecipientDetails

class OrderOut(BaseModel):
    id: UUID
    customer: UserOut
    driver: Optional[UserOut]
    payment_id: Optional[UUID]
    pickup_location: GeoPoint
    delivery_location: GeoPoint
    package_details: PackageDetails
    price: float
    goods_image_path: Optional[str]
    status: OrderStatus
    is_verified: bool
    driver_id: Optional[UUID]

    class Config:
        from_attributes = True

class OrderStatusHistoryOut(BaseModel):
    id: int
    status: OrderStatus
    changed_by: UserOut
    timestamp: datetime

    class Config:
        from_attributes = True 

class ProofOfDeliveryOut(BaseModel):
    id: int
    image_path: Optional[str]
    signature_path: Optional[str]
    uploaded_at: datetime

    class Config:
        from_attributes = True

class OrderFullOut(OrderOut):
    status_history: List[OrderStatusHistoryOut]
    proof_of_delivery: Optional[ProofOfDeliveryOut]

