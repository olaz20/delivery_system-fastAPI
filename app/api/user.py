from fastapi import  status, Depends, APIRouter, Request
from app.schemas.user import  UserOut, UserCreate, Login, RefreshToken, StaffCreate, StandardResponse
from sqlalchemy.orm import Session
from app.core import database
from app.services.user import create_user_service, verify_email_service, login_user_service, logout_user_service,refresh_token_service, create_staff_service
from app.core.security import oauth2_scheme, get_current_admin
from app.models import user



router = APIRouter(
    prefix="/users",
    tags=["Users"]
)
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserOut)
async def create_user(request: Request, user: UserCreate, db: Session = Depends(database.get_db)): 
    return await create_user_service(request, user, db)


@router.get("/verify")
async def verify_email(request: Request, token: str, db: Session = Depends(database.get_db)):
      return await verify_email_service(request, token, db)



@router.post("/login", response_model=StandardResponse)
def login(request: Request, user_credentials: Login, db:Session = Depends(database.get_db)):
     return login_user_service(request, user_credentials, db)



@router.post("/logout")
def logout(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    return logout_user_service(request, token, db)


@router.post("/refresh", response_model=dict)
def refresh_token(request: Request, refresh_token: RefreshToken, db: Session = Depends(database.get_db)):
    return refresh_token_service(request, refresh_token, db)

@router.post("/staff", status_code=status.HTTP_201_CREATED, response_model=StandardResponse)
def create_staff(request: Request, staff: StaffCreate, db: Session = Depends(database.get_db), current_admin: user.User = Depends(get_current_admin)):
    return create_staff_service(request, staff, db, current_admin)