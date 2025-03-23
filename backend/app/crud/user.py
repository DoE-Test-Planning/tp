from typing import Any, Dict, Optional, Union
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """
    CRUD operations for User model
    """
    
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """
        Get a user by email
        """
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()
    
    async def get_by_google_id(self, db: AsyncSession, *, google_id: str) -> Optional[User]:
        """
        Get a user by Google ID
        """
        result = await db.execute(select(User).where(User.google_id == google_id))
        return result.scalars().first()
    
    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """
        Create a new user
        """
        db_obj = User(
            email=obj_in.email,
            full_name=obj_in.full_name,
            profile_picture=obj_in.profile_picture,
            google_id=obj_in.google_id,
            is_active=True,
            storage_used_bytes=0
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update_storage_used(self, db: AsyncSession, *, user_id: int, new_size: int) -> User:
        """
        Update the storage used by a user
        """
        user = await self.get(db, id=user_id)
        if user:
            user.storage_used_bytes = new_size
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user


user = CRUDUser(User) 