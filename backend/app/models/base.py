from datetime import datetime
from typing import Any
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, DateTime, Integer


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    Provides common columns and methods.
    """
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @declared_attr
    def __tablename__(cls) -> str:
        """
        Generate __tablename__ automatically based on class name.
        """
        return cls.__name__.lower() 