from pydantic import BaseModel
from uuid import UUID
from typing import Dict, Optional

class PaymentInitialize(BaseModel):
    email: str
    amount: float
    reference: str
    callback_url: str

class PaymentOut(BaseModel):
    id: UUID
    reference: str
    amount: float
    status: str
    customer_id: UUID
    order_id: Optional[UUID] 
    class Config:
       from_attributes = True