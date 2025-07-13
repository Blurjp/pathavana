"""
Base Pydantic schemas for common request/response patterns.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ErrorDetail(BaseModel):
    """Individual error detail."""
    code: str = Field(..., description="Error code identifier")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field that caused the error")


class ResponseMetadata(BaseModel):
    """Standard metadata included in all API responses."""
    session_id: Optional[str] = Field(None, description="UUID of the travel session")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    version: str = Field(default="2.0", description="API version")
    request_id: Optional[str] = Field(None, description="Unique request identifier")


class BaseResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)
    errors: Optional[List[ErrorDetail]] = Field(None, description="List of errors if success is false")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaginationParams(BaseModel):
    """Standard pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.limit


class PaginationInfo(BaseModel):
    """Pagination information in responses."""
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total number of items")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


class SortOrder(str, Enum):
    """Sort order options."""
    ASC = "asc"
    DESC = "desc"


class DateRange(BaseModel):
    """Date range for filtering."""
    start_date: Optional[datetime] = Field(None, description="Start date (inclusive)")
    end_date: Optional[datetime] = Field(None, description="End date (inclusive)")


class LocationInfo(BaseModel):
    """Location information."""
    city: Optional[str] = Field(None, description="City name")
    country: Optional[str] = Field(None, description="Country name")
    iata_code: Optional[str] = Field(None, description="Airport IATA code")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")


class PriceInfo(BaseModel):
    """Price information with currency."""
    amount: float = Field(..., description="Price amount")
    currency: str = Field(..., description="Currency code (ISO 4217)")
    formatted: Optional[str] = Field(None, description="Human-readable formatted price")