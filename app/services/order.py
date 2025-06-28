from app.schemas.order import GeoPoint, OrderOut, OrderCreate, OrderFullOut, ProofOfDeliveryOut
from fastapi import Depends, HTTPException, status, UploadFile, File,Request,BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_driver, get_current_user
from app.models.user import User
from app.models.order import Order, OrderStatus,OrderStatusHistory, ProofOfDelivery
from app.core.config import settings
from app.schemas.user import UserRole
from pathlib import Path
import shutil
import uuid
from app.core.response import create_success_response
from app.services.utils import validate_image_file
from app.services.payment import calculate_price_service
from app.services.email import send_order_confirmation_email



async def create_order_service(
    request: Request,
    background_tasks: BackgroundTasks,
    order: OrderCreate,
    goods_image: UploadFile =File(None),
    db: Session = Depends(get_db), 
    current_customer: User = Depends(get_current_user),
): 
    price = await calculate_price_service(order.pickup_location.dict(), order.delivery_location.dict(), order.package_details.dict())    

    goods_image_path = None
    if goods_image:
        await validate_image_file(goods_image)
    db_order = Order(
        customer_id=current_customer.id,
        pickup_location=order.pickup_location.dict(),
        delivery_location=order.delivery_location.dict(),
        package_details= order.package_details.dict(),
        recipient_details=order.recipient_details.dict(),
        goods_image_path=str(goods_image_path) if goods_image_path else None,
        price=price,
        is_verified=False,
        status=OrderStatus.CREATED
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    status_history = OrderStatusHistory(
        order_id=db_order.id,
        status=OrderStatus.CREATED,
        changed_by_id=current_customer.id
    )
    db.add(status_history)
    db.commit()

    background_tasks.add_task(
        send_order_confirmation_email,
        email=current_customer.email,
        customer_name=current_customer.first_name,
        order_id=str(db_order.id)

    )

    return create_success_response(
        data=OrderOut.model_validate(db_order, from_attributes=True),
        message="Order created successfully.",
        code=201,
        request_id=request.state.request_id
    )




def update_order_status_service(request: Request, order_id: int, status: OrderOut, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, details="Order not found")
    
    valid_transitions = {
        OrderStatus.CREATED: [OrderStatus.ASSIGNED, OrderStatus.CANCELLED],
        OrderStatus.ASSIGNED: [OrderStatus.PICKED_UP, OrderStatus.CANCELLED, OrderStatus.FAILED],
        OrderStatus.PICKED_UP: [OrderStatus.DELIVERED, OrderStatus.FAILED],
        OrderStatus.CANCELLED: [],
        OrderStatus.FAILED: [],
        OrderStatus.DELIVERED: []
    }
    if status not in valid_transitions[db_order.status]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status transition")
    
    if status in [OrderStatus.PICKED_UP, OrderStatus.DELIVERED, OrderStatus.FAILED] and current_user.role != UserRole.DRIVER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only drivers can update to this status")
    if status == OrderStatus.CANCELLED and current_user.role not in [UserRole.CUSTOMER, UserRole.DISPATCHER]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only customers or dispatchers can cancel")
    
    db_order.status = status
    db.commit()
    db.refresh(db_order)
    
    status_history = OrderStatusHistory(
        order_id=db_order.id,
        status=status,
        changed_by_id=current_user.id
    )
    db.add(status_history)
    db.commit()

    return create_success_response(
        data=OrderOut.from_orm(db_order),
        message=f"Order status updated to {status}.",
        request_id=request.state.request_id
    )





async def upload_proof_of_delivery_service(
    request:Request,
    order_id: int,
    image: UploadFile = File(None),
    signature: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_driver: User = Depends(get_current_driver)
):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if db_order.status != OrderStatus.DELIVERED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order not delivered")
    if db_order.driver_id != current_driver.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your order")
    
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(exist_ok=True)
    
    image_path = None
    signature_path = None
    
    if image:
        file_extension = image.filename.split(".")[-1]
        image_path = upload_dir / f"image_{order_id}_{uuid.uuid4()}.{file_extension}"
        with image_path.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
    
    if signature:
        file_extension = signature.filename.split(".")[-1]
        signature_path = upload_dir / f"signature_{order_id}_{uuid.uuid4()}.{file_extension}"
        with signature_path.open("wb") as buffer:
            shutil.copyfileobj(signature.file, buffer)
    
    db_proof = ProofOfDelivery(
        order_id=order_id,
        image_path=str(image_path) if image_path else None,
        signature_path=str(signature_path) if signature_path else None
    )
    db.add(db_proof)
    db.commit()
    db.refresh(db_proof)
    
    return create_success_response(
        data=ProofOfDeliveryOut.from_orm(db_proof),
        message="Proof of delivery uploaded successfully.",
        request_id=request.state.request_id
    )




def get_order_service(request: Request,order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    if current_user.role not in [UserRole.ADMIN, UserRole.DISPATCHER] and \
       current_user.id not in [db_order.customer_id, db_order.driver_id]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this order")
    
    return create_success_response(
        data=OrderFullOut.from_orm(db_order),
        message="Order retrieved successfully.",
        request_id=request.state.request_id
    )
