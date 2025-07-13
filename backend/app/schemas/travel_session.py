"""
Travel session schemas
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel

class TravelSessionBase(BaseModel):
    status: Optional[str] = "active"
    session_data: Optional[Dict[str, Any]] = {}
    context_data: Optional[Dict[str, Any]] = {}

class TravelSessionCreate(TravelSessionBase):
    user_id: str

class TravelSessionUpdate(TravelSessionBase):
    pass

class TravelSessionInDBBase(TravelSessionBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TravelSession(TravelSessionInDBBase):
    pass

class TravelSessionResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]