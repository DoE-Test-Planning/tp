from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.crud import doe_asset
from app.schemas.doe_asset import ScenarioGenerate
from app.schemas.user import User
from app.services.doe_generator import DoEGenerator

router = APIRouter()


@router.post("/{asset_id}/generate", response_model=Dict[str, Any])
async def generate_scenarios(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Generate test scenarios for a DoE asset.
    
    Args:
        asset_id: DoE asset ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Generated scenarios
    """
    # Get asset
    asset = await doe_asset.get(db, id=asset_id)
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DoE asset not found",
        )
    
    # Check permissions
    if asset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Get current version
    if not asset.current_version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Asset has no version data",
        )
    
    # Extract parameter sets from version data
    parameter_sets = asset.current_version.parameter_data.get("parameter_sets", [])
    
    if not parameter_sets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No parameter sets defined",
        )
    
    # Generate all combinations (full factorial design)
    scenarios = DoEGenerator.generate_all_combinations(parameter_sets)
    
    # Update asset with scenarios
    current_version = asset.current_version
    current_version.scenarios_data = {"scenarios": scenarios}
    db.add(current_version)
    
    # Calculate export sizes
    file_sizes = DoEGenerator.calculate_file_sizes(scenarios, parameter_sets)
    await doe_asset.update_export_file_sizes(
        db, asset_id=asset_id, 
        md_size=file_sizes["md_size"], 
        xlsx_size=file_sizes["xlsx_size"]
    )
    
    await db.commit()
    await db.refresh(asset)
    
    return {
        "message": "Scenarios generated successfully",
        "total_scenarios": len(scenarios),
        "scenarios": scenarios
    }


@router.post("/{asset_id}/reduce", response_model=Dict[str, Any])
async def reduce_scenarios(
    asset_id: int,
    reduction_in: ScenarioGenerate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Reduce test scenarios for a DoE asset.
    
    Args:
        asset_id: DoE asset ID
        reduction_in: Reduction technique and parameters to include
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Reduced scenarios
    """
    # Get asset
    asset = await doe_asset.get(db, id=asset_id)
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DoE asset not found",
        )
    
    # Check permissions
    if asset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Get current version
    if not asset.current_version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Asset has no version data",
        )
    
    # Check if scenarios are generated
    if not asset.current_version.scenarios_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No scenarios generated for this asset",
        )
    
    # Extract parameter sets from version data
    parameter_sets = asset.current_version.parameter_data.get("parameter_sets", [])
    
    if not parameter_sets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No parameter sets defined",
        )
    
    # Reduce scenarios based on selected technique
    technique = reduction_in.technique
    parameters_to_include = reduction_in.parameters_to_include
    
    if technique == "pairwise":
        reduced_scenarios = DoEGenerator.reduce_pairwise(
            parameter_sets, parameters_to_include
        )
    elif technique == "fractional_factorial":
        reduced_scenarios = DoEGenerator.reduce_fractional_factorial(
            parameter_sets, parameters_to_include
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reduction technique",
        )
    
    # Update asset with reduced scenarios
    current_version = asset.current_version
    current_version.reduced_scenarios_data = {"scenarios": reduced_scenarios}
    current_version.reduction_technique = technique
    db.add(current_version)
    
    # Calculate export sizes using reduced scenarios
    file_sizes = DoEGenerator.calculate_file_sizes(reduced_scenarios, parameter_sets)
    await doe_asset.update_export_file_sizes(
        db, asset_id=asset_id, 
        md_size=file_sizes["md_size"], 
        xlsx_size=file_sizes["xlsx_size"]
    )
    
    await db.commit()
    await db.refresh(asset)
    
    # Get original scenario count for comparison
    original_scenarios = asset.current_version.scenarios_data.get("scenarios", [])
    
    return {
        "message": "Scenarios reduced successfully",
        "original_count": len(original_scenarios),
        "reduced_count": len(reduced_scenarios),
        "reduction_percentage": round(
            (1 - len(reduced_scenarios) / len(original_scenarios)) * 100, 2
        ) if original_scenarios else 0,
        "technique": technique,
        "scenarios": reduced_scenarios
    } 