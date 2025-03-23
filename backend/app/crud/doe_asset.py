from typing import Any, Dict, List, Optional, Union
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
import json

from app.crud.base import CRUDBase
from app.models.doe_asset import DoEAsset, DoEAssetVersion, ShareableLink
from app.schemas.doe_asset import DoEAssetCreate, DoEAssetUpdate


class CRUDDoEAsset(CRUDBase[DoEAsset, DoEAssetCreate, DoEAssetUpdate]):
    """
    CRUD operations for DoE Asset model
    """
    
    async def get_by_unique_url_id(self, db: AsyncSession, *, unique_url_id: str) -> Optional[DoEAsset]:
        """
        Get a DoE asset by its unique URL ID
        """
        result = await db.execute(
            select(DoEAsset)
            .where(DoEAsset.unique_url_id == unique_url_id)
            .options(
                joinedload(DoEAsset.current_version),
                joinedload(DoEAsset.previous_version),
                joinedload(DoEAsset.shared_links)
            )
        )
        return result.scalars().first()
    
    async def get_multi_by_user(
        self, db: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[DoEAsset]:
        """
        Get multiple DoE assets for a specific user
        """
        result = await db.execute(
            select(DoEAsset)
            .where(DoEAsset.user_id == user_id)
            .options(
                joinedload(DoEAsset.current_version),
            )
            .order_by(desc(DoEAsset.updated_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def create_with_version(
        self, db: AsyncSession, *, obj_in: DoEAssetCreate, user_id: int
    ) -> DoEAsset:
        """
        Create a new DoE asset with initial version
        """
        # Create a new asset
        asset = DoEAsset(
            name=obj_in.name,
            user_id=user_id,
            asset_size_bytes=0,
            md_file_size_bytes=0,
            xlsx_file_size_bytes=0
        )
        db.add(asset)
        await db.flush()
        
        # Create initial version
        parameter_data = {
            "parameter_sets": [
                {
                    "name": ps.name,
                    "parameters": [
                        {
                            "name": p.name,
                            "value": p.value,
                            "scenarios": p.scenarios
                        }
                        for p in ps.parameters
                    ]
                }
                for ps in obj_in.parameter_sets
            ]
        }
        
        version = DoEAssetVersion(
            asset_id=asset.id,
            version_number=1,
            parameter_data=parameter_data
        )
        db.add(version)
        await db.flush()
        
        # Link version to asset
        asset.current_version_id = version.id
        
        # Calculate asset size
        asset_size = len(json.dumps(parameter_data).encode("utf-8"))
        asset.asset_size_bytes = asset_size
        
        await db.commit()
        await db.refresh(asset)
        
        return asset
    
    async def update_with_version(
        self, db: AsyncSession, *, db_obj: DoEAsset, obj_in: DoEAssetUpdate
    ) -> DoEAsset:
        """
        Update a DoE asset and create a new version
        """
        # Update basic asset info
        if obj_in.name is not None:
            db_obj.name = obj_in.name
        
        # If parameter sets are updated, create a new version
        if obj_in.parameter_sets is not None:
            # Get current version number
            current_version = await db.get(DoEAssetVersion, db_obj.current_version_id)
            new_version_number = current_version.version_number + 1
            
            # Create parameter data from input
            parameter_data = {
                "parameter_sets": [
                    {
                        "name": ps.name,
                        "parameters": [
                            {
                                "name": p.name,
                                "value": p.value,
                                "scenarios": p.scenarios
                            }
                            for p in ps.parameters
                        ]
                    }
                    for ps in obj_in.parameter_sets
                ]
            }
            
            # Create new version
            new_version = DoEAssetVersion(
                asset_id=db_obj.id,
                version_number=new_version_number,
                parameter_data=parameter_data
            )
            db.add(new_version)
            await db.flush()
            
            # Update version references
            db_obj.previous_version_id = db_obj.current_version_id
            db_obj.current_version_id = new_version.id
            
            # Calculate new asset size
            asset_size = len(json.dumps(parameter_data).encode("utf-8"))
            db_obj.asset_size_bytes = asset_size
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj
    
    async def create_shareable_link(
        self, db: AsyncSession, *, asset_id: int, permission_type: str
    ) -> ShareableLink:
        """
        Create a shareable link for a DoE asset
        """
        shareable_link = ShareableLink(
            asset_id=asset_id,
            permission_type=permission_type
        )
        db.add(shareable_link)
        await db.commit()
        await db.refresh(shareable_link)
        
        return shareable_link
    
    async def get_by_access_token(
        self, db: AsyncSession, *, access_token: str
    ) -> Optional[DoEAsset]:
        """
        Get a DoE asset by shareable link access token
        """
        result = await db.execute(
            select(DoEAsset)
            .join(ShareableLink, ShareableLink.asset_id == DoEAsset.id)
            .where(ShareableLink.access_token == access_token)
            .options(
                joinedload(DoEAsset.current_version),
                joinedload(DoEAsset.shared_links)
            )
        )
        return result.scalars().first()
    
    async def update_export_file_sizes(
        self, db: AsyncSession, *, asset_id: int, md_size: int, xlsx_size: int
    ) -> DoEAsset:
        """
        Update the export file sizes for a DoE asset
        """
        asset = await self.get(db, id=asset_id)
        if asset:
            asset.md_file_size_bytes = md_size
            asset.xlsx_file_size_bytes = xlsx_size
            db.add(asset)
            await db.commit()
            await db.refresh(asset)
        return asset


doe_asset = CRUDDoEAsset(DoEAsset) 