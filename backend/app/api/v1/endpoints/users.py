from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.crud import user as user_crud
from app.schemas.user import User, UserUpdate

router = APIRouter()


@router.get("/me", response_model=User)
async def read_user_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user profile.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User profile data
    """
    return current_user


@router.put("/me", response_model=User)
async def update_user_me(
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update current user profile.
    
    Args:
        user_in: User data to update
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated user profile data
    """
    user = await user_crud.update(db, db_obj=current_user, obj_in=user_in)
    return user 