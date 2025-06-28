from app.core.response import create_success_response
from fastapi import APIRouter, Depends, HTTPException, status,Request
from app.schemas.order import GeoPoint, OrderOut
from app.models.order import Order, OrderStatus,OrderStatusHistory,DriverLocation        
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.core.security import get_current_driver, get_current_user
from app.core.database import get_db
from app.schemas.user import UserRole
from sqlalchemy import cast, Text
from datetime import datetime, timedelta
from app.models.user import User
import uuid
import json
from uuid import UUID


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


async def assign_driver_service(db: Session, pickup_location: dict) -> User:
    freshness_threshold = datetime.utcnow() - timedelta(minutes=settings.gps_freshness_minutes)
    coords = pickup_location.get("coordinates", [])
    if len(coords) != 2:
        raise ValueError("pickup_location must contain 'coordinates' with [longitude, latitude]")
    
    pickup_point = {
        "type": "Point",
        "coordinates": coords
    }
    pickup_point_json = json.dumps(pickup_point)


    active_orders = db.query(Order.driver_id).filter(
    Order.status.in_(["created", "assigned", "picked_up"])
    ).subquery()

    nearest_driver = (
        db.query(User, DriverLocation.location)
        .join(DriverLocation, User.id == DriverLocation.driver_id)
        .filter(
            User.role == UserRole.DISPATCHER,
            User.is_verified == True,
            DriverLocation.updated_at >= freshness_threshold,
           # User.id.notin_(select(active_orders.c.driver_id))
        )
        .order_by(
            func.ST_Distance(
                func.ST_SetSRID(func.ST_GeomFromGeoJSON(cast(DriverLocation.location, Text)), 4326),
                func.ST_SetSRID(func.ST_GeomFromGeoJSON(cast(pickup_point_json, Text)), 4326)
            )
        )
        .limit(1)
        .first()
    )

    if not nearest_driver:
        return None

    return nearest_driver[0]


async def retry_assign_driver(db: Session, order_id: UUID, retry_count: int, max_retries: int = 12):
    """Retry assigning a driver every 5 minutes, up to 1 hour (12 retries)."""
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order or db_order.status != OrderStatus.CREATED:
        return
    driver = await assign_driver_service(db, db_order.pickup_location)
    if driver:
        db_order.driver_id = driver.id
        db_order.status = OrderStatus.ASSIGNED
        status_history = OrderStatusHistory(
            order_id=order_id,
            status=OrderStatus.ASSIGNED,
            changed_by_id=db_order.driver_id,
        )
        db.add(status_history)
        db.commit()
        return
    if retry_count >= max_retries:
        db_order.status = OrderStatus.FAILED
        status_history = OrderStatusHistory(
            id=uuid.uuid4(),
            order_id=order_id,
            status=OrderStatus.FAILED,
            changed_by_id=None,
        )  
        db.add(status_history)
        db.commit()
        return 
    from time import sleep
    sleep(300)
    await retry_assign_driver(db, order_id, retry_count +1, max_retries)




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

