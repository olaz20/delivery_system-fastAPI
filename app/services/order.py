from app.schemas.order import GeoPoint, OrderOut, OrderCreate, OrderFullOut, ProofOfDeliveryOut
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File,Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_driver, get_current_user
from app.models.user import User
from app.models.order import Order, OrderStatus,OrderStatusHistory, ProofOfDelivery, DriverLocation        
from sqlalchemy import func
from app.core.config import settings
from datetime import datetime, timedelta
from app.schemas.user import UserRole
from geopy.distance import geodesic
from pathlib import Path
import shutil
import uuid
from app.core.response import create_success_response


def update_driver_location_service(
   request: Request, location: GeoPoint, db: Session, current_driver: User
):
    db_location = db.query(DriverLocation).filter(DriverLocation.driver_id == current_driver.id).first()
    if db_location:
        db_location.location = location.dict()
        db_location.updated_at = func.now()
    else:
        db_location = DriverLocation(
            driver_id = current_driver.id,
            location=location.dict()
        )
        db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return create_success_response(
        data={"message": "Location updated successfully"},
        message="Driver location updated.",
        request_id=request.state.request_id
    )



def assign_driver_service(db: Session, pickup_location: dict) -> User:
    freshness_threshold = datetime.utcnow() - timedelta(minutes=settings.gps_freshness_minutes)

    active_orders = db.query(Order.driver_id).filter(
        Order.status.in_(["created", "assigned", "picked_up"])
    ).subquery()
    nearest_driver = db.query(User, DriverLocation.location).join(DriverLocation, User.id == DriverLocation.driver_id).filter(
        User.role == UserRole.DISPATCHER,
        User.is_verified == True,
        DriverLocation.updated_at >= freshness_threshold,
        User.id.notin_(active_orders)
    ).order_by(
        func.ST_Distance(
            func.ST_SetSRID(
                func.ST_GeomFromGeoJSON(DriverLocation.location),
                4326
            ),
            func.ST_SetSRID(
                func.ST_GeomFromGeoJSON(func.json_build_object(
                    'type', 'Point',
                    'coordinates', pickup_location['coordinates']
                )),
                4326
            )
        )
    ).first()

    if not nearest_driver:
        return None
    
    return nearest_driver[0]

async def calculate_price_service(pickup_location: dict, delivery_location: dict, package_details: dict) -> float:
    pickup_coords = (pickup_location["coordinates"][1], pickup_location["coordinates"][0])
    
    delivery_coords = (delivery_location["coordinates"][1], delivery_location["coordinates"][0])
     
    distance_km = geodesic(pickup_coords, delivery_coords).km

    base_price = distance_km * settings.base_price_per_km

    weight_price = package_details["weight_kg"] * settings.weight_price_per_kg

    demand_price = (base_price + weight_price) * settings.demand_multiplier

    return round(demand_price, 2)




async def create_order_service(
    request: Request,
    order: OrderCreate,
    goods_image: UploadFile =File(None),
    db: Session = Depends(get_db), 
    current_customer: User = Depends(get_current_user),
):
    if goods_image:
        allowed_extensions = {".jpg", ".jpeg", ".png"}
        file_extension = Path(goods_image.filename).suffix.lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image format. Use JPG, JPEG, or PNG")
        if goods_image.size > 5 * 1024 * 1024:  # 5MB limit
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image size exceeds 5MB")
    price = await calculate_price_service(order.pickup_location.dict(), order.delivery_location.dict(), order.package_details.dict())    

    goods_image_path = None
    if goods_image:
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(exist_ok=True)
        file_extension = Path(goods_image.filename).suffix
        goods_image_path = upload_dir / f"goods_{uuid.uuid4()}{file_extension}"
        with goods_image_path.open("wb") as buffer:
            shutil.copyfileobj(goods_image.file, buffer)

    db_order = Order(
        customer_id=current_customer.id,
        pickup_location=order.pickup_location.dict(),
        delivery_location=order.delivery_location.dict(),
        package_details= order.package_details.dict(),
        recipient_details=order.recipient_details.dict(),
        goods_image_path=str(goods_image_path) if goods_image_path else None,
        price=price,
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

    return create_success_response(
        data=OrderOut.model_validate(db_order, from_attributes=True),
        message="Order created successfully.",
        code=201,
        request_id=request.state.request_id
    )




async def assign_driver_to_order_service(request: Request,order_id: int, db:Session = Depends(get_db), current_dispatcher: User = Depends(get_current_driver)):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if db_order.status != OrderStatus.CREATED:
       raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order not in created status") 
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
        changed_by_id=current_dispatcher.id
    )
    db.add(status_history)
    db.commit()
    return create_success_response(
        data=OrderOut.from_orm(db_order),
        message="Driver assigned successfully",
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
