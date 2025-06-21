from app.core.database import get_db
from app.core.security import get_current_driver, get_current_user
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from app.schemas.user import UserRole
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import User

from app.core.config import settings


from app.schemas.order import GeoPoint, OrderOut, OrderCreate, OrderFullOut, ProofOfDeliveryOut
from app.services.order import update_driver_location_service, create_order_service, assign_driver_to_order_service,upload_proof_of_delivery_service, get_order_service


router = APIRouter(
    prefix="/order",
    tags=["Orders"]
)

@router.post("/location", status_code=status.HTTP_200_OK)
def update_location_route(
    location: GeoPoint,
    db: Session = Depends(get_db),
    current_driver: User = Depends(get_current_driver)
):
    return update_driver_location_service(location, db, current_driver)






@router.post("/", status_code=status.HTTP_201_CREATED, response_model=OrderOut)
async def create_order_service(
    order: OrderCreate,
    goods_image: UploadFile =File(None),
    db: Session = Depends(get_db), 
    current_customer: User = Depends(get_current_user)
):
  return create_order_service(order, goods_image, db, current_customer)





@router.post("/{order_id}/assign", response_model=OrderOut)
async def assign_driver_to_order(order_id: int, db:Session = Depends(get_db), current_dispatcher: User = Depends(get_current_driver)):
    return assign_driver_to_order_service(order_id, db)







@router.post("/{order_id}/update-status", response_model=OrderOut)
def update_order_status_service(order_id: int, status: OrderOut, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return update_order_status_service(order_id, status, db, current_user)



@router.post("/{order_id}/proof-of-delivery", response_model=ProofOfDeliveryOut)
async def upload_proof_of_delivery(
    order_id: int,
    image: UploadFile = File(None),
    signature: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_driver: User = Depends(get_current_driver)
):
    return upload_proof_of_delivery_service(order_id, image, signature, db, current_driver)



@router.get("/{order_id}", response_model=OrderFullOut)
def get_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_order_service(order_id, db, current_user)
    