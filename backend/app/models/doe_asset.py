from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
import uuid
import json

from app.models.base import Base


class DoEAsset(Base):
    """
    Design of Experiments (DoE) Asset model.
    
    Stores test planning data with user-defined parameters and values.
    Contains both the original data and the generated test scenarios.
    """
    # Basic information
    name = Column(String, nullable=False, index=True)
    unique_url_id = Column(String, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Asset ownership
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    owner = relationship("User", back_populates="doe_assets")
    
    # Asset size tracking
    asset_size_bytes = Column(Integer, default=0)
    md_file_size_bytes = Column(Integer, default=0)
    xlsx_file_size_bytes = Column(Integer, default=0)
    
    # Versioning
    current_version_id = Column(Integer, ForeignKey("doeassetversion.id"), nullable=True)
    previous_version_id = Column(Integer, ForeignKey("doeassetversion.id"), nullable=True)
    
    # Relationships
    versions = relationship("DoEAssetVersion", 
                           foreign_keys="[DoEAssetVersion.asset_id]",
                           back_populates="asset",
                           cascade="all, delete-orphan")
    current_version = relationship("DoEAssetVersion", 
                                  foreign_keys=[current_version_id],
                                  post_update=True)
    previous_version = relationship("DoEAssetVersion", 
                                   foreign_keys=[previous_version_id],
                                   post_update=True)
    shared_links = relationship("ShareableLink", back_populates="asset", cascade="all, delete-orphan")
    
    @property
    def total_size_bytes(self) -> int:
        """
        Get total size in bytes (asset + exports)
        """
        return self.asset_size_bytes + self.md_file_size_bytes + self.xlsx_file_size_bytes
    
    @property
    def formatted_total_size(self) -> str:
        """
        Get formatted total size (KB, MB, etc)
        """
        total_bytes = self.total_size_bytes
        if total_bytes < 1024:
            return f"{total_bytes} B"
        elif total_bytes < 1024 * 1024:
            return f"{round(total_bytes / 1024, 2)} KB"
        else:
            return f"{round(total_bytes / (1024 * 1024), 2)} MB"


class DoEAssetVersion(Base):
    """
    Version of a DoE Asset.
    
    Stores the data for a specific version of a DoE Asset,
    including parameters, scenarios, and reduction settings.
    """
    # Relationship to parent asset
    asset_id = Column(Integer, ForeignKey("doeasset.id", ondelete="CASCADE"), nullable=False)
    asset = relationship("DoEAsset", foreign_keys=[asset_id], back_populates="versions")
    
    # Version metadata
    version_number = Column(Integer, default=1)
    
    # Data storage as JSON
    parameter_data = Column(JSON, nullable=False, default=dict)
    scenarios_data = Column(JSON, nullable=True)
    reduced_scenarios_data = Column(JSON, nullable=True)
    reduction_technique = Column(String, nullable=True)


class ShareableLink(Base):
    """
    Shareable link for a DoE Asset.
    
    Allows sharing assets with other users via a unique URL.
    """
    # Link to asset
    asset_id = Column(Integer, ForeignKey("doeasset.id", ondelete="CASCADE"), nullable=False)
    asset = relationship("DoEAsset", back_populates="shared_links")
    
    # Access control
    access_token = Column(String, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    permission_type = Column(String, default="view")  # view or edit