from app.core.config import settings
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File,Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_driver, get_current_user
from app.models.user import User
from app.core.response import create_success_response
import requests
from app.models.payment import Payment
from app.schemas.payment import PaymentOut
from app.services.order import calculate_price_service
from app.schemas.order import OrderCreate
import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.models.order import Order, OrderStatus, OrderStatusHistory
from app.services.order import assign_driver_service


PAYSTACK_HEADERS = {
    "Authorization": f"Bearer {settings.paystack_secret_key}",
    "Content-Type": "application/json"
}



async def initialize_payment(request: Request,  order_id: UUID,  db: Session = Depends(get_db), current_customer: User = Depends(get_current_user),) -> dict:
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if db_order.customer_id != current_customer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to initialize payment for this order")
    payment_data = {
        "email": current_customer.email,
        "amount": int(db_order.price * 100),
        "reference": f"order_{uuid.uuid4()}",
        "callback_url": f"{settings.frontend_url}/payment/callback"
    }
    response = request.post(
        "https://api.paystack.co/transaction/initialize",
        json=payment_data,
        headers=PAYSTACK_HEADERS
    )
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to initialize payment")
    
    payment_response = response.json()
    if not payment_response.get("status"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=payment_response.get("message"))
    
    db_payment = Payment(
        reference=payment_data["reference"],
        amount=int(db_order.price * 100),
        status="pending",
        customer_id=current_customer.id,
        order_id=order_id
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    
    db_order.payment_id = db_payment.id
    db.commit()
    db.refresh(db_order)



async def verify_payment_service(
    request: Request,
    reference: str,
    db: Session = Depends(get_db),
    current_customer: User = Depends(get_current_user)
):
    response = requests.get(
        f"https://api.paystack.co/transaction/verify/{reference}",
        headers=PAYSTACK_HEADERS
    ) 
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to verify payment")

    payment_response = response.json()
    if not payment_response.get("status"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=payment_response.get("message"))

    db_payment = db.query(Payment).filter(Payment.reference == reference).first()
    if not db_payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    if db_payment.customer_id != current_customer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to verify this payment")
    db_order=db.query(Order).filter(Order.id==db_payment.order.id).first()
    if not db_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    

    if payment_response["data"]["status"] == "success":
        db_payment.status = "success"
        db_order.is_verified = True
        db.commit()
        db.refresh(db_payment)
        db.refresh(db_order)


        driver = await assign_driver_service(db, db_order.pickup_location)
        if not driver:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No available drivers")
        db_order.driver_id = driver.id
        db_order.status = OrderStatus.ASSIGNED
        db.commit()
        db.refresh(db_order)
        status_history = OrderStatusHistory(
                order_id=db_order.id,
                status=OrderStatus.ASSIGNED,
                changed_by_id=db_order.dispatcher_id,
                
            )
        db.add(status_history)
        db.commit()
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment not successful")
    return create_success_response(
        data=PaymentOut.model_validate(db_payment, from_attributes=True),
        message="Payment verified successfully",
        request_id=request.state.request_id
    )

