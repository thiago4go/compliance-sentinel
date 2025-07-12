"""
Data models and schemas for the InsightHarvesterAgent
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, validator

class UrgencyLevel(str, Enum):
    """Urgency levels for regulatory changes"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ComplianceDomain(str, Enum):
    """Compliance domains"""
    DATA_PRIVACY = "data_privacy"
    FINANCIAL = "financial"
    ENVIRONMENTAL = "environmental"
    HEALTHCARE = "healthcare"
    EMPLOYMENT = "employment"
    CYBERSECURITY = "cybersecurity"
    GENERAL = "general"

class SourceType(str, Enum):
    """Types of regulatory sources"""
    GOVERNMENT_WEBSITE = "government_website"
    REGULATORY_AGENCY = "regulatory_agency"
    INDUSTRY_PUBLICATION = "industry_publication"
    NEWS_FEED = "news_feed"
    LEGAL_DATABASE = "legal_database"

class ComplianceAnalysisInput(BaseModel):
    """Input schema for compliance analysis requests"""
    analysis_id: str = Field(..., description="Unique identifier for this analysis")
    content: str = Field(..., description="Text content to analyze")
    source_url: Optional[HttpUrl] = Field(None, description="Source URL of the content")
    source_type: SourceType = Field(SourceType.GOVERNMENT_WEBSITE, description="Type of source")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Request timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class RegulatoryInsight(BaseModel):
    """Structured regulatory insight extracted from content"""
    insight_id: str = Field(..., description="Unique identifier for this insight")
    title: str = Field(..., description="Title or summary of the regulatory change")
    description: str = Field(..., description="Detailed description of the change")
    domain: ComplianceDomain = Field(..., description="Compliance domain")
    urgency_level: UrgencyLevel = Field(..., description="Urgency level of the change")
    effective_date: Optional[datetime] = Field(None, description="When the regulation becomes effective")
    deadline: Optional[datetime] = Field(None, description="Compliance deadline if applicable")
    affected_entities: List[str] = Field(default_factory=list, description="Types of entities affected")
    key_requirements: List[str] = Field(default_factory=list, description="Key compliance requirements")
    potential_impact: str = Field("", description="Potential impact assessment")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in the analysis")
    extracted_concepts: List[str] = Field(default_factory=list, description="Key concepts extracted")
    source_reference: str = Field("", description="Reference to the source")
    
    @validator('confidence_score')
    def validate_confidence_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence score must be between 0.0 and 1.0')
        return v

class InsightHarvesterOutput(BaseModel):
    """Output schema from the InsightHarvesterAgent"""
    regulatory_insight: RegulatoryInsight = Field(..., description="The extracted regulatory insight")
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When processing completed")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in the output")
    next_agent: str = Field("problem-framing-agent", description="Next agent in the workflow")
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PotentialRegulationChangeEvent(BaseModel):
    """Event published when a potential regulation change is detected"""
    event_id: str = Field(..., description="Unique event identifier")
    snippet: str = Field(..., description="Text snippet containing the change")
    source: str = Field(..., description="Source of the information")
    domain: str = Field(..., description="Compliance domain")
    urgency_level: UrgencyLevel = Field(..., description="Urgency level")
    detected_at: datetime = Field(default_factory=datetime.utcnow, description="Detection timestamp")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    keywords: List[str] = Field(default_factory=list, description="Detected keywords")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class RegulatoryFeedItem(BaseModel):
    """Individual item from a regulatory feed"""
    item_id: str = Field(..., description="Unique identifier for the feed item")
    title: str = Field(..., description="Title of the item")
    content: str = Field(..., description="Full content")
    published_date: datetime = Field(..., description="Publication date")
    source_url: HttpUrl = Field(..., description="Source URL")
    source_name: str = Field(..., description="Name of the source")
    tags: List[str] = Field(default_factory=list, description="Associated tags")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class MonitoringConfig(BaseModel):
    """Configuration for regulatory monitoring"""
    sources: List[Dict[str, Any]] = Field(..., description="List of sources to monitor")
    check_interval: int = Field(300, description="Check interval in seconds")
    keywords: List[str] = Field(default_factory=list, description="Keywords to monitor")
    domains: List[ComplianceDomain] = Field(default_factory=list, description="Domains to focus on")
    enabled: bool = Field(True, description="Whether monitoring is enabled")

class ProcessingResult(BaseModel):
    """Result of processing a regulatory item"""
    item_id: str = Field(..., description="ID of the processed item")
    is_significant: bool = Field(..., description="Whether the item is significant")
    significance_score: float = Field(..., ge=0.0, le=1.0, description="Significance score")
    extracted_insights: List[RegulatoryInsight] = Field(default_factory=list, description="Extracted insights")
    processing_time: float = Field(..., description="Processing time in seconds")
    errors: List[str] = Field(default_factory=list, description="Any processing errors")

class HealthStatus(BaseModel):
    """Health status of the harvester service"""
    status: str = Field(..., description="Overall status")
    service: str = Field(..., description="Service name")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Status timestamp")
    monitoring_active: bool = Field(..., description="Whether monitoring is active")
    last_successful_harvest: Optional[datetime] = Field(None, description="Last successful harvest")
    error_count: int = Field(0, description="Recent error count")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
