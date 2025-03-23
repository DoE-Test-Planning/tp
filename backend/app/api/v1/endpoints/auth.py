from datetime import timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.core.auth import create_access_token, get_current_active_user
from app.core.config import settings
from app.core.database import get_db
from app.crud import user as user_crud
from app.schemas.user import UserCreate, User

router = APIRouter()

# Google OAuth config
GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI = settings.GOOGLE_REDIRECT_URI


@router.post("/google", response_model=Dict[str, str])
async def google_auth(code: str, db: AsyncSession = Depends(get_db)) -> Any:
    """
    Authenticate with Google OAuth2.
    
    Args:
        code: OAuth authorization code from Google
        db: Database session
        
    Returns:
        Access token and token type
    """
    # Exchange authorization code for access token
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=token_data)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to authenticate with Google",
            )
        
        token_info = response.json()
        
        # Get user info from Google
        user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        headers = {"Authorization": f"Bearer {token_info['access_token']}"}
        
        user_response = await client.get(user_info_url, headers=headers)
        
        if user_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to get user info from Google",
            )
        
        user_info = user_response.json()
    
    # Check if user exists, create if not
    db_user = await user_crud.get_by_google_id(db, google_id=str(user_info["id"]))
    
    if not db_user:
        user_in = UserCreate(
            email=user_info["email"],
            full_name=user_info.get("name"),
            profile_picture=user_info.get("picture"),
            google_id=str(user_info["id"]),
        )
        db_user = await user_crud.create(db, obj_in=user_in)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(db_user.id)}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Dict[str, str])
async def refresh_token(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Refresh access token.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        New access token and token type
    """
    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(current_user.id)}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    } 