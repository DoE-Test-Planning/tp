#!/usr/bin/env python3
"""
Script to create all database tables based on the SQLAlchemy models.
This is an alternative to using Alembic migrations when starting from scratch.
"""
import asyncio
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow absolute imports
sys.path.append(str(Path(__file__).resolve().parents[2]))

from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.models.base import Base


async def create_tables():
    """Create all database tables."""
    engine = create_async_engine(str(settings.DATABASE_URI))
    
    async with engine.begin() as conn:
        # Import all models to ensure they're registered with Base.metadata
        from app.models.user import User
        from app.models.doe_asset import DoEAsset, DoEAssetVersion, ShareableLink
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    
    print("All database tables created successfully")


if __name__ == "__main__":
    asyncio.run(create_tables()) 