from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Request
from app.schemas.response import StandardResponse, ErrorItem, ErrorDetail
from fastapi.responses import JSONResponse
from app.core.response import create_error_response
from fastapi.exceptions import RequestValidationError



app = FastAPI()
class RequestIDMiddleware(BaseHTTPMiddleware):
     async def dispatch(self, request, call_next):
        request_id = uuid4()
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = str(request)
        return response
     
app.add_middleware(RequestIDMiddleware)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    error_mapping = {
        "Email already registered": {
            "code": "email_already_registered",
            "field": "email",
            "details": ErrorDetail(suggestion="Please use a different email or log in with this email.")
        },
        "Staff ID already registered": {
            "code": "staff_id_already_registered",
            "field": "staff_id",
            "details": ErrorDetail(suggestion="Please use a unique staff ID.")
        },
        "Invalid image format. Use JPG, JPEG, or PNG": {
            "code": "invalid_image_format",
            "field": "goods_image",
            "details": ErrorDetail(suggestion="Please upload a JPG, JPEG, or PNG image.")
        },
        "Image size exceeds 5MB": {
            "code": "image_size_exceeded",
            "field": "goods_image",
            "details": ErrorDetail(suggestion="Please upload an image smaller than 5MB.")
        },
        "Order not found": {
            "code": "order_not_found",
            "field": None,
            "details": ErrorDetail(suggestion="Please check the order ID.")
        },
        # Add more mappings as needed
    }
    
    error_info = error_mapping.get(exc.detail, {
        "code": "generic_error",
        "field": None,
        "details": ErrorDetail(message=exc.detail)
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            message=exc.detail,
            errors=[ErrorItem(**error_info)],
            code=exc.status_code,
            request_id=request.state.request_id
        ).dict()
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = error["loc"][-1] if error["loc"] else None
        errors.append(ErrorItem(
            code="validation_error",
            field=str(field),
            details=ErrorDetail(message=error["msg"])
        ))
    
    return JSONResponse(
        status_code=422,
        content=create_error_response(
            message="Validation failed for the request.",
            errors=errors,
            code=422,
            request_id=request.state.request_id
        ).dict()
    )