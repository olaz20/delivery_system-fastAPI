from fastapi import HTTPException, status, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, StaffCreate, UserOut, Token
from app.services.email import send_confirmation_email
from app.core import security, database
from app.models.user import User, TokenBlackList, UserRole
from jose import jwt, JWTError
from app.core.config import settings
from app.schemas.user import Login, RefreshToken
from app.core.security import create_access_token, create_refresh_token, verify, oauth2_scheme, refresh_access_token, get_current_admin
from app.core.response import  create_success_response

async def send_verfication_email(email: str):
    token = security.create_email_token(email)
    try:
        await send_confirmation_email(email, token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")







async def create_user_service(user: UserCreate, db: Session, request:Request):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        if db_user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
            
        else:
            await send_verfication_email(user.email)
            return db_user
    hashed_password = security.hash(user.password)
    user.password = hashed_password
    db_user = User(
        email = user.email,
        first_name = user.first_name,
        last_name = user.last_name,
        password = hashed_password,
        is_verified=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    await send_verfication_email(user.email)
    return create_success_response(
        data=UserOut.from_orm(db_user),
        message="User created successfully. Please verify your email.",
        code=201,
        request_id=request.state.request_id)

async def verify_email_service(token: str, db: Session, request:Request):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
        
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= "Invalid token")
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, details="User not found")
    if db_user.is_verified:
        return create_success_response(
            data={"message": "Email already verified"},
            message="Email verification status checked",
            request_id=request.state.request_id
        )
    db_user.is_verified = True
    db.commit()
    return create_success_response(
        data={"message": "Email verified successfully"},
        message= "Email verified successfully",
        request_id=request.state.request_id
    )


def login_user_service(request:Request, user_credentials: Login, db:Session):
    user = db.query(User).filter(User.email == user_credentials.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if not user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")
    
    if not verify(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})

    return create_success_response(
        data=Token(access_token=access_token,
            refresh_token=refresh_token, token_type="bearer"),
        message="Login successful",
        request_id=request.state.request_id
    )


def logout_user_service(request: Request,token: str, db: Session):
    # Add token to blacklist
    db_token = TokenBlackList(token=token)
    db.add(db_token)
    db.commit()
    return create_success_response (data={"message":"Successfully logged out"},
    message="Successfully logged out",
    request_id=request.state.request_id)

def refresh_token_service(request: Request, refresh_token: RefreshToken, db: Session ):
    token_data = refresh_access_token(refresh_token.refresh_token, db)
    return create_success_response(data=token_data,
                                   message="Token refreshed successfully",
                                   request_id=request.state.request_id)

def create_staff_service(request: Request, staff: StaffCreate, db: Session, current_admin: User):
    if db.query(User).filter(User.email == staff.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    if db.query(User).filter(User.staff_id == staff.staff_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role for staff")
    
    if staff.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role for staff")
    
    hashed_password = hash(staff.password)
    db_user = User(
        email = staff.email,
        first_name = staff.first_name,
        last_name = staff.last_name,
        password= hashed_password,
        is_verified=True,
        role=staff.role,
        staff_id=staff.staff_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return create_success_response(
        data=UserOut.from_orm(db_user),
        message="Staff user created successfully",
        code=201, 
        request_id=request.state.request_id
    )

