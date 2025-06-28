from app.core.config import settings
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_driver, get_current_user
import httpx
from app.models.user import User
from app.core.response import create_success_response
import requests
from app.models.payment import Payment
from app.schemas.payment import PaymentOut
from app.schemas.order import OrderCreate
import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.models.order import Order, OrderStatus, OrderStatusHistory
from app.services.logistics import assign_driver_service , retry_assign_driver
from app.core.config import settings
from geopy.distance import geodesic
from app.services.email import send_driver_assignment_email, send_payment_success_email




PAYSTACK_HEADERS = {
    "Authorization": f"Bearer {settings.paystack_secret_key}",
    "Content-Type": "application/json"
}

async def calculate_price_service(pickup_location: dict, delivery_location: dict, package_details: dict) -> float:
    pickup_coords = (pickup_location["coordinates"][1], pickup_location["coordinates"][0])
    
    delivery_coords = (delivery_location["coordinates"][1], delivery_location["coordinates"][0])
     
    distance_km = geodesic(pickup_coords, delivery_coords).km

    base_price = distance_km * settings.base_price_per_km

    weight_price = package_details["weight_kg"] * settings.weight_price_per_kg

    demand_price = (base_price + weight_price) * settings.demand_multiplier

    return round(demand_price, 2)


async def initialize_payment_service(request: Request,  order_id: UUID,  db: Session, current_customer: User,) -> dict:
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
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                "https://api.paystack.co/transaction/initialize",
                json=payment_data,
                headers=PAYSTACK_HEADERS
            )
    except httpx.ConnectTimeout:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Paystack timed out. Please try again later."
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error connecting to Paystack: {str(exc)}"
        )

    
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

    return create_success_response(
        data={
            "order_id": order_id,
            "payment_url": payment_response["data"]["authorization_url"]
        },
        message="Payment initialized successfully.",
        request_id=request.state.request_id
    )



async def verify_payment_service(
    request: Request,
    background_tasks: BackgroundTasks,
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
    db_order = db.query(Order).filter(Order.id == db_payment.order_id).first()
    if not db_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    

    if payment_response["data"]["status"] == "success":
        db_payment.status = "success"
        db_order.is_verified = True
        db.commit()
        db.refresh(db_payment)
        db.refresh(db_order)


        driver = await assign_driver_service(db, db_order.pickup_location)
        driver_name, driver_email = None, None
        if driver:
            db_order.driver_id = driver.id
            db_order.status = OrderStatus.ASSIGNED
            status_history = OrderStatusHistory(
                order_id=db_order.id,
                status=OrderStatus.ASSIGNED,
                changed_by_id=db_order.driver_id
            )
            db.add(status_history)
            db.commit()
            
            driver_name = driver.first_name
            driver_email = driver.email
            background_tasks.add_task(
                send_driver_assignment_email,
                email=driver_email,
                driver_name=driver_name,
                order_id=str(db_order.id)
            )

        else:
            background_tasks.add_task(retry_assign_driver, db, db_order.id, 1)
        background_tasks.add_task(
            send_payment_success_email,
            email=current_customer.email,
            customer_name=current_customer.first_name,
            order_id=str(db_order.id),
            driver_name=driver_name,
            driver_email=driver_email
        )
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment not successful")
    return create_success_response(
        data=PaymentOut.model_validate(db_payment, from_attributes=True),
        message="Payment verified successfully",
        request_id=request.state.request_id
    )

