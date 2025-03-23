from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
import re


class ParameterBase(BaseModel):
    """Base schema for a parameter"""
    name: str
    value: str
    scenarios: List[int] = Field(default_factory=list)
    
    @validator('name')
    def validate_parameter_name(cls, v):
        """Validate parameter name - only alphanumeric, underscore, space, hyphen"""
        if not re.match(r'^[a-zA-Z0-9_\- ]+$', v):
            raise ValueError('Parameter name can only contain letters, numbers, underscores, hyphens, and spaces')
        return v


class ParameterSetBase(BaseModel):
    """Base schema for a set of parameters"""
    name: str
    parameters: List[ParameterBase]


class DoEAssetBase(BaseModel):
    """Base schema for DoE asset"""
    name: str


class DoEAssetCreate(DoEAssetBase):
    """Schema for creating a new DoE asset"""
    parameter_sets: List[ParameterSetBase] = Field(default_factory=list)


class DoEAssetUpdate(BaseModel):
    """Schema for updating a DoE asset"""
    name: Optional[str] = None
    parameter_sets: Optional[List[ParameterSetBase]] = None


class ParameterInDB(ParameterBase):
    """Schema for parameter data from database"""
    pass


class ParameterSetInDB(ParameterSetBase):
    """Schema for parameter set data from database"""
    parameters: List[ParameterInDB]
    
    class Config:
        orm_mode = True


class DoEAssetVersionBase(BaseModel):
    """Base schema for DoE asset version"""
    version_number: int
    parameter_data: Dict[str, Any]
    scenarios_data: Optional[Dict[str, Any]] = None
    reduced_scenarios_data: Optional[Dict[str, Any]] = None
    reduction_technique: Optional[str] = None
    
    class Config:
        orm_mode = True


class ShareableLinkBase(BaseModel):
    """Base schema for shareable link"""
    access_token: str
    permission_type: str
    
    class Config:
        orm_mode = True


class DoEAssetInDB(DoEAssetBase):
    """Schema for DoE asset data from database"""
    id: int
    unique_url_id: str
    user_id: int
    asset_size_bytes: int
    md_file_size_bytes: int
    xlsx_file_size_bytes: int
    current_version_id: Optional[int] = None
    previous_version_id: Optional[int] = None
    
    class Config:
        orm_mode = True


class DoEAsset(DoEAssetInDB):
    """Schema for DoE asset data returned to client"""
    current_version: Optional[DoEAssetVersionBase] = None
    total_size_bytes: int
    formatted_total_size: str
    shared_links: List[ShareableLinkBase] = []


class ScenarioCreate(BaseModel):
    """Schema for generating DoE scenarios"""
    parameter_sets: List[ParameterSetBase]


class ScenarioGenerate(BaseModel):
    """Schema for generating reduced scenarios"""
    technique: str = Field(..., description="Reduction technique: 'pairwise' or 'fractional_factorial'")
    parameters_to_include: List[str] = Field(default_factory=list, description="Parameters that must be included in all test scenarios")


class ShareableLinkCreate(BaseModel):
    """Schema for creating a shareable link"""
    permission_type: str = Field("view", pattern="^(view|edit)$")


class ExportFormat(BaseModel):
    """Schema for export format"""
    format: str = Field(..., pattern="^(md|xlsx)$") 