from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class ORMBase(BaseModel):
    """Base Pydantic model configured to read from SQLAlchemy ORM objects."""
    model_config = ConfigDict(from_attributes=True)


class WithTimestamps(BaseModel):
    """Optional timestamp fields many responses will include."""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
