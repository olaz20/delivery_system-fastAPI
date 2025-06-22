from pydantic import BaseModel
from typing import Any, List, Optional, Dict
from datetime import datetime
from uuid import UUID

class ErrorDetail(BaseModel):
    message: Optional[str] = None
    suggestion: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None
class ErrorItem(BaseModel):
    code: str
    field: Optional[str] = None 
    details: Optional[ErrorDetail] = None

class StandardResponse(BaseModel):
    status: str
    code: int
    message: str
    data: Optional[Any] = None 
    errors: Optional[List[ErrorItem]] = None
    timestamp: datetime
    request_id: UUID

    class Config:
        json_schema_extra = {
            "example": {
                "status": 400,
                "error": {
                    "code": "email_already_registered",
                    "message": "The provided email address is already registered.",
                    "field": "email",
                    "details": {
                        "suggestion": "Please use a different email or log in with this email."
                    }
                }
            }
        }