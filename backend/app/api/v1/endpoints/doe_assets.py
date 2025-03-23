from typing import Any, List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_active_user, verify_storage_quota
from app.core.config import settings
from app.core.database import get_db
from app.crud import doe_asset, user as user_crud
from app.models.doe_asset import DoEAsset as DoEAssetModel
from app.schemas.doe_asset import (
    DoEAsset, DoEAssetCreate, DoEAssetUpdate, 
    ShareableLinkCreate, ExportFormat
)
from app.schemas.user import User
from app.services.doe_generator import DoEGenerator

router = APIRouter()


@router.get("/", response_model=List[DoEAsset])
async def list_doe_assets(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    List DoE assets for current user.
    
    Args:
        skip: Number of assets to skip
        limit: Maximum number of assets to return
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of DoE assets
    """
    assets = await doe_asset.get_multi_by_user(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return assets


@router.post("/", response_model=DoEAsset)
async def create_doe_asset(
    asset_in: DoEAssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create a new DoE asset.
    
    Args:
        asset_in: DoE asset data to create
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created DoE asset
    """
    # Verify storage quota
    verify_storage_quota(current_user)
    
    # Create asset
    asset = await doe_asset.create_with_version(
        db, obj_in=asset_in, user_id=current_user.id
    )
    
    # Update user storage
    await user_crud.update_storage_used(
        db, user_id=current_user.id, 
        new_size=current_user.storage_used_bytes + asset.total_size_bytes
    )
    
    return asset


@router.get("/{asset_id}", response_model=DoEAsset)
async def get_doe_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get a DoE asset by ID.
    
    Args:
        asset_id: DoE asset ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        DoE asset
    """
    asset = await doe_asset.get(db, id=asset_id)
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DoE asset not found",
        )
    
    if asset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return asset


@router.put("/{asset_id}", response_model=DoEAsset)
async def update_doe_asset(
    asset_id: int,
    asset_in: DoEAssetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a DoE asset.
    
    Args:
        asset_id: DoE asset ID
        asset_in: DoE asset data to update
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated DoE asset
    """
    asset = await doe_asset.get(db, id=asset_id)
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DoE asset not found",
        )
    
    if asset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Get old size for storage calculation
    old_size = asset.total_size_bytes
    
    # Update asset
    asset = await doe_asset.update_with_version(
        db, db_obj=asset, obj_in=asset_in
    )
    
    # Update user storage
    size_diff = asset.total_size_bytes - old_size
    if size_diff != 0:
        new_size = current_user.storage_used_bytes + size_diff
        # Verify storage quota for increased size
        if size_diff > 0:
            if new_size > settings.MAX_STORAGE_PER_USER_MB * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Storage quota exceeded. Maximum allowed: {settings.MAX_STORAGE_PER_USER_MB}MB"
                )
                
        await user_crud.update_storage_used(
            db, user_id=current_user.id, new_size=new_size
        )
    
    return asset


@router.delete("/{asset_id}", response_model=DoEAsset)
async def delete_doe_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a DoE asset.
    
    Args:
        asset_id: DoE asset ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Deleted DoE asset
    """
    asset = await doe_asset.get(db, id=asset_id)
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DoE asset not found",
        )
    
    if asset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Get size for storage calculation
    size = asset.total_size_bytes
    
    # Delete asset
    asset = await doe_asset.remove(db, id=asset_id)
    
    # Update user storage
    await user_crud.update_storage_used(
        db, user_id=current_user.id, 
        new_size=max(0, current_user.storage_used_bytes - size)
    )
    
    return asset


@router.post("/{asset_id}/share", response_model=Dict[str, str])
async def create_shareable_link(
    asset_id: int,
    link_in: ShareableLinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create a shareable link for a DoE asset.
    
    Args:
        asset_id: DoE asset ID
        link_in: Shareable link data to create
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Shareable link URL
    """
    asset = await doe_asset.get(db, id=asset_id)
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DoE asset not found",
        )
    
    if asset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Create shareable link
    link = await doe_asset.create_shareable_link(
        db, asset_id=asset_id, permission_type=link_in.permission_type
    )
    
    # Generate shareable URL
    base_url = settings.FRONTEND_URL
    share_url = f"{base_url}/share/{link.access_token}"
    
    return {"share_url": share_url}


@router.get("/shared/{access_token}", response_model=DoEAsset)
async def get_shared_doe_asset(
    access_token: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a DoE asset by shareable link.
    
    Args:
        access_token: Shareable link access token
        db: Database session
        
    Returns:
        DoE asset
    """
    asset = await doe_asset.get_by_access_token(db, access_token=access_token)
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DoE asset not found or link expired",
        )
    
    return asset


@router.get("/{asset_id}/export", response_model=Dict[str, str])
async def export_doe_asset(
    asset_id: int,
    format: str = Query(..., regex="^(md|xlsx)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Export a DoE asset to a file.
    
    Args:
        asset_id: DoE asset ID
        format: Export format (md or xlsx)
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Export data
    """
    asset = await doe_asset.get(db, id=asset_id)
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DoE asset not found",
        )
    
    if asset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Get current version data
    current_version = asset.current_version
    
    if not current_version or not current_version.scenarios_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No scenarios generated for this asset",
        )
    
    # Choose data based on reduction
    scenarios_data = (
        current_version.reduced_scenarios_data 
        if current_version.reduced_scenarios_data 
        else current_version.scenarios_data
    )
    
    # Format export based on requested format
    if format == "md":
        # Convert JSONB data to python dict
        parameter_sets = current_version.parameter_data.get("parameter_sets", [])
        scenarios = scenarios_data.get("scenarios", [])
        
        content = DoEGenerator.format_to_markdown(scenarios, parameter_sets)
        
        # Generate a sanitized filename
        filename = "".join(
            c if c.isalnum() else "_" for c in asset.name
        )
        
        return {
            "content": content,
            "filename": f"{filename}.md",
            "content_type": "text/markdown"
        }
    
    elif format == "xlsx":
        # For Excel, we'll return a download URL (handled in frontend)
        # This is just a placeholder; in a real implementation, you'd store the file
        # and return a URL or base64 encoded content
        
        # Generate a sanitized filename
        filename = "".join(
            c if c.isalnum() else "_" for c in asset.name
        )
        
        # Convert to DataFrame and return as JSON (frontend will convert to Excel)
        parameter_sets = current_version.parameter_data.get("parameter_sets", [])
        scenarios = scenarios_data.get("scenarios", [])
        
        df = DoEGenerator.format_to_dataframe(scenarios, parameter_sets)
        
        return {
            "content": df.to_json(orient="records"),
            "filename": f"{filename}.xlsx",
            "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        } 