from fastapi import  status, Depends, APIRouter
from app.schemas.user import  UserOut, UserCreate, Token, Login, RefreshToken, StaffCreate
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
async def create_user(user: UserCreate, db: Session = Depends(database.get_db)): 
    return await create_user_service(user, db)


@router.get("/verify")
async def verify_email(token: str, db: Session = Depends(database.get_db)):
      return await verify_email_service(token, db)



@router.post("/login", response_model=Token)
def login(user_credentials: Login, db:Session = Depends(database.get_db)):
     return login_user_service(user_credentials, db)



@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    return logout_user_service(token, db)


@router.post("/refresh", response_model=dict)
def refresh_token(refresh_token: RefreshToken, db: Session = Depends(database.get_db)):
    return refresh_token_service(refresh_token, db)

@router.post("/staff", status_code=status.HTTP_201_CREATED, response_model=UserOut)
def create_staff(staff: StaffCreate, db: Session = Depends(database.get_db), current_admin: user.User = Depends(get_current_admin)):
    return create_staff_service(staff, db, get_current_admin )