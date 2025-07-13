"""
GDPR compliance and data management Pydantic schemas.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field, validator
from enum import Enum

from .base import PaginationParams


class DataExportFormat(str, Enum):
    """Data export format options."""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    XML = "xml"


class DataProcessingPurpose(str, Enum):
    """Data processing purpose categories."""
    TRAVEL_BOOKING = "travel_booking"
    CUSTOMER_SERVICE = "customer_service"
    ANALYTICS = "analytics"
    MARKETING = "marketing"
    LEGAL_COMPLIANCE = "legal_compliance"
    SECURITY = "security"


class DataCategory(str, Enum):
    """Categories of personal data."""
    PERSONAL_INFO = "personal_info"
    CONTACT_INFO = "contact_info"
    TRAVEL_DOCUMENTS = "travel_documents"
    PAYMENT_INFO = "payment_info"
    TRAVEL_HISTORY = "travel_history"
    PREFERENCES = "preferences"
    TECHNICAL_DATA = "technical_data"
    COMMUNICATION_DATA = "communication_data"


class LegalBasis(str, Enum):
    """GDPR legal basis for processing."""
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"


class DataExportRequest(BaseModel):
    """Request to export user data (Right to data portability)."""
    format: DataExportFormat = Field(default=DataExportFormat.JSON, description="Export format")
    include_categories: Optional[List[DataCategory]] = Field(None, description="Specific data categories to include")
    date_from: Optional[date] = Field(None, description="Include data from this date")
    date_to: Optional[date] = Field(None, description="Include data up to this date")
    include_deleted: bool = Field(default=False, description="Include soft-deleted data")
    include_metadata: bool = Field(default=True, description="Include processing metadata")
    encryption_requested: bool = Field(default=False, description="Request encrypted export")

    @validator('date_from', 'date_to')
    def validate_dates(cls, v):
        if v and v > date.today():
            raise ValueError('Date cannot be in the future')
        return v

    @validator('date_to')
    def validate_date_range(cls, v, values):
        if v and 'date_from' in values and values['date_from']:
            if v < values['date_from']:
                raise ValueError('End date must be after start date')
        return v


class DataExportResponse(BaseModel):
    """Response for data export request."""
    export_id: str = Field(..., description="Unique export identifier")
    status: str = Field(..., description="Export status")
    download_url: Optional[str] = Field(None, description="Download URL when ready")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    record_count: Optional[int] = Field(None, description="Number of records exported")
    categories_included: List[DataCategory] = Field(..., description="Data categories in export")
    created_at: datetime = Field(..., description="Export creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Download link expiration")
    encryption_info: Optional[Dict[str, str]] = Field(None, description="Encryption details if requested")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DataDeletionRequest(BaseModel):
    """Request to delete user data (Right to erasure)."""
    reason: str = Field(..., description="Reason for deletion request")
    delete_categories: Optional[List[DataCategory]] = Field(None, description="Specific categories to delete")
    retain_for_legal: bool = Field(default=True, description="Retain data required for legal compliance")
    retain_anonymized: bool = Field(default=False, description="Retain anonymized data for analytics")
    confirmation_required: bool = Field(default=True, description="Require email confirmation")

    @validator('reason')
    def validate_reason(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('Deletion reason must be at least 10 characters')
        return v.strip()


class AnonymizationRequest(BaseModel):
    """Request to anonymize user data."""
    categories: List[DataCategory] = Field(..., description="Data categories to anonymize")
    retain_analytics: bool = Field(default=True, description="Retain for analytics purposes")
    pseudonymize: bool = Field(default=False, description="Use pseudonymization instead of full anonymization")
    reason: str = Field(..., description="Reason for anonymization")

    @validator('categories')
    def validate_categories(cls, v):
        if not v:
            raise ValueError('At least one category must be specified')
        return v

    @validator('reason')
    def validate_reason(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError('Reason must be at least 5 characters')
        return v.strip()


class ConsentRecord(BaseModel):
    """Record of user consent."""
    consent_id: str = Field(..., description="Unique consent identifier")
    user_id: int = Field(..., description="User ID")
    purpose: DataProcessingPurpose = Field(..., description="Purpose of data processing")
    legal_basis: LegalBasis = Field(..., description="Legal basis for processing")
    consented: bool = Field(..., description="Whether consent was given")
    consent_text: str = Field(..., description="Text of consent request")
    consent_version: str = Field(..., description="Version of consent form")
    timestamp: datetime = Field(..., description="When consent was given/withdrawn")
    ip_address: Optional[str] = Field(None, description="IP address of consent")
    user_agent: Optional[str] = Field(None, description="User agent string")
    expires_at: Optional[datetime] = Field(None, description="When consent expires")
    withdrawn_at: Optional[datetime] = Field(None, description="When consent was withdrawn")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DataProcessingRecord(BaseModel):
    """Record of data processing activity."""
    processing_id: str = Field(..., description="Unique processing identifier")
    user_id: int = Field(..., description="User ID")
    activity: str = Field(..., description="Processing activity")
    purpose: DataProcessingPurpose = Field(..., description="Purpose of processing")
    legal_basis: LegalBasis = Field(..., description="Legal basis")
    data_categories: List[DataCategory] = Field(..., description="Categories of data processed")
    processor: str = Field(..., description="Who processed the data")
    timestamp: datetime = Field(..., description="When processing occurred")
    retention_period: Optional[int] = Field(None, description="Retention period in days")
    third_parties: Optional[List[str]] = Field(None, description="Third parties data shared with")
    security_measures: Optional[List[str]] = Field(None, description="Security measures applied")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DataSubjectRequest(BaseModel):
    """General data subject request."""
    request_type: str = Field(..., description="Type of request (access, rectification, erasure, etc.)")
    subject: str = Field(..., description="Subject line of request")
    description: str = Field(..., description="Detailed description of request")
    preferred_response_method: str = Field(default="email", description="How to respond (email, postal, etc.)")
    urgency: str = Field(default="normal", description="Request urgency level")

    @validator('description')
    def validate_description(cls, v):
        if not v or len(v.strip()) < 20:
            raise ValueError('Description must be at least 20 characters')
        return v.strip()


class ComplianceReport(BaseModel):
    """Compliance status report."""
    report_id: str = Field(..., description="Report identifier")
    user_id: int = Field(..., description="User ID")
    generated_at: datetime = Field(..., description="Report generation timestamp")
    
    # Data inventory
    data_categories: Dict[DataCategory, int] = Field(..., description="Count of records per category")
    total_records: int = Field(..., description="Total number of data records")
    
    # Consent status
    active_consents: int = Field(..., description="Number of active consents")
    expired_consents: int = Field(..., description="Number of expired consents")
    withdrawn_consents: int = Field(..., description="Number of withdrawn consents")
    
    # Retention compliance
    overdue_deletions: int = Field(..., description="Records overdue for deletion")
    upcoming_deletions: int = Field(..., description="Records due for deletion soon")
    
    # Processing activities
    recent_processing: List[DataProcessingRecord] = Field(..., description="Recent processing activities")
    
    # Security status
    encryption_status: Dict[str, bool] = Field(..., description="Encryption status by data type")
    access_logs: int = Field(..., description="Number of access log entries")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DataRetentionPolicy(BaseModel):
    """Data retention policy configuration."""
    category: DataCategory = Field(..., description="Data category")
    retention_period_days: int = Field(..., description="Retention period in days")
    legal_basis: LegalBasis = Field(..., description="Legal basis for retention")
    auto_delete: bool = Field(default=True, description="Automatically delete when expired")
    notification_days: int = Field(default=30, description="Days before deletion to notify")
    exceptions: Optional[List[str]] = Field(None, description="Exceptions to retention policy")

    @validator('retention_period_days')
    def validate_retention_period(cls, v):
        if v <= 0:
            raise ValueError('Retention period must be positive')
        if v > 3650:  # 10 years
            raise ValueError('Retention period cannot exceed 10 years')
        return v


class PrivacySettings(BaseModel):
    """User privacy settings."""
    data_processing_consent: Dict[DataProcessingPurpose, bool] = Field(..., description="Consent by purpose")
    marketing_consent: bool = Field(default=False, description="Marketing communications consent")
    analytics_consent: bool = Field(default=False, description="Analytics data processing consent")
    third_party_sharing: bool = Field(default=False, description="Allow sharing with third parties")
    data_retention_preference: str = Field(default="standard", description="Preferred retention period")
    communication_preferences: Dict[str, bool] = Field(default_factory=dict, description="Communication preferences")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }