from fastapi import APIRouter, Depends, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.database import get_db
from app.core.security import get_current_driver, get_current_user
from app.services.payment import initialize_payment_service, verify_payment_service
from sqlalchemy.orm import Session
from uuid import UUID

router = APIRouter(
    prefix="/payment",
    tags=["payments"]
)

@router.post("/initialize-payment", status_code=status.HTTP_201_CREATED)
async def initialize_payment(
    request: Request,
    order_id: UUID,
    db: Session = Depends(get_db),
    current_customer: User = Depends(get_current_user),
):
    return await initialize_payment_service(request, order_id, db, current_customer)


@router.post("/verify-payment", status_code=status.HTTP_200_OK)
async def verify_payment(
    request: Request,
    background_tasks:BackgroundTasks,
    reference: str,
    db: Session = Depends(get_db),
    current_customer: User = Depends(get_current_user)
):
    return await verify_payment_service(request,background_tasks, reference, db,current_customer)
    

