from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class TenantBase(BaseModel):
    name: str

class TenantCreate(TenantBase):
    pass

class Tenant(TenantBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str = "Developer"

class UserCreate(UserBase):
    password: str
    tenant_name: Optional[str] = None # Optional new tenant creation

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None

class User(UserBase):
    id: str
    tenant_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class TokenPayload(BaseModel):
    sub: Optional[str] = None
