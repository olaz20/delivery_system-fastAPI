from app.schemas.response import StandardResponse
from fastapi.responses import JSONResponse
from datetime import datetime
from uuid import UUID
from typing import Any, List

def create_success_response(data: Any, message: str = "Request processed successfully.", code: int = 200, request_id: UUID = None) -> StandardResponse:
    return StandardResponse(
        status="success",
        code=code,
        message=message,
        data=data,
        timestamp=datetime.utcnow(),
        request_id=request_id
    )

def create_error_response(message: str, errors: List[dict], code: int, request_id: UUID = None) -> StandardResponse:
    return StandardResponse(
        status="error",
        code=code,
        message=message,
        errors=errors,
        timestamp=datetime.utcnow(),
        request_id=request_id
    )
