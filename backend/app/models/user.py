from sqlalchemy import Column, String, Integer, Boolean, Float
from sqlalchemy.orm import relationship

from app.models.base import Base


class User(Base):
    """
    User model for authentication and storage management.
    Uses Google Auth for authentication.
    """
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)
    google_id = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Storage management
    storage_used_bytes = Column(Integer, default=0)
    
    # Relationships
    doe_assets = relationship("DoEAsset", back_populates="owner", cascade="all, delete-orphan")
    
    @property
    def storage_used_mb(self) -> float:
        """
        Get storage used in megabytes
        """
        return round(self.storage_used_bytes / (1024 * 1024), 2)
    
    @property
    def formatted_storage_used(self) -> str:
        """
        Get formatted storage used (KB, MB, etc)
        """
        if self.storage_used_bytes < 1024:
            return f"{self.storage_used_bytes} B"
        elif self.storage_used_bytes < 1024 * 1024:
            return f"{round(self.storage_used_bytes / 1024, 2)} KB"
        else:
            return f"{self.storage_used_mb} MB" 