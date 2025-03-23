from typing import Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base schema for user data"""
    email: EmailStr
    full_name: Optional[str] = None
    profile_picture: Optional[str] = None
    
    
class UserCreate(UserBase):
    """Schema for creating a new user"""
    google_id: str
    

class UserUpdate(BaseModel):
    """Schema for updating a user"""
    full_name: Optional[str] = None
    profile_picture: Optional[str] = None


class UserInDB(UserBase):
    """Schema for user data from database"""
    id: int
    google_id: str
    is_active: bool
    storage_used_bytes: int
    
    class Config:
        orm_mode = True


class User(UserInDB):
    """Schema for user data returned to client"""
    storage_used_mb: float
    formatted_storage_used: str 