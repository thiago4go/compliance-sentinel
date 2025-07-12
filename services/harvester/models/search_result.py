from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class QueryMetadata(BaseModel):
    """Metadata for search queries"""
    query_hash: int
    timestamp: datetime
    session_id: str
    agent_name: str
    tools_used: List[str] = []
    response_length: int = 0
    processing_time_ms: Optional[int] = None

class SearchResult(BaseModel):
    """Search result data model"""
    query: str
    response: str
    sources: List[str] = Field(default_factory=list)
    metadata: QueryMetadata
    confidence_score: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class SearchResultSummary(BaseModel):
    """Summary of search results for reporting"""
    total_queries: int
    date_range: Dict[str, str]
    top_queries: List[str]
    average_response_length: float
    most_used_sources: List[str]
