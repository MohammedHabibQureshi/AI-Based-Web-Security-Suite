from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core import security
from app.core.config import settings
from app.models.auth import Tenant, User
from app.schemas import auth as schemas
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/register", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )

    # 1. Create Tenant
    tenant_name = user_in.tenant_name or f"{user_in.name}'s Organization"
    tenant = Tenant(name=tenant_name)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    # 2. Create User
    hashed_pwd = security.get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        name=user_in.name,
        hashed_password=hashed_pwd,
        role="Admin",  # First user registered in workspace is Admin
        tenant_id=tenant.id
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 3. Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/login", response_model=schemas.Token)
def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=schemas.User)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
