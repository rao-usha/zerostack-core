"""Base Pydantic models and utilities."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


class BaseSchema(BaseModel):
    """Base schema with common fields."""
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }


class TimestampedSchema(BaseSchema):
    """Schema with timestamps."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class IDSchema(BaseSchema):
    """Schema with ID field."""
    id: UUID = Field(default_factory=uuid4)


class BaseResponse(BaseSchema):
    """Base API response."""
    success: bool = True
    message: Optional[str] = None


class ErrorResponse(BaseSchema):
    """Error response schema."""
    success: bool = False
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None

