#!/usr/bin/env python3
"""
Simplified Data Models for Oncology MCP System
Basic models without security features.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum

class QueryType(Enum):
    """Types of oncology queries."""
    CANCER_INFO = "cancer_info"
    GENE_INFO = "gene_info" 
    DRUG_INFO = "drug_info"
    DRUG_INDIA_INFO = "drug_india_info"
    COMBINED = "combined"
    UNKNOWN = "unknown"

class ChatRequest(BaseModel):
    """Request model for chat interactions."""
    message: Optional[str] = Field(None, description="User's oncology query (alternative to query)")
    query: Optional[str] = Field(None, description="User's oncology query (alternative to message)")
    session_id: Optional[str] = Field(None, description="Optional session identifier")
    
    def get_query_text(self) -> str:
        """Get the query text from either message or query field."""
        return self.message or self.query or ""
    
    class Config:
        schema_extra = {
            "example": {
                "message": "What are the biomarkers for lung cancer?",
                "session_id": "session_123"
            }
        }

class ChatResponse(BaseModel):
    """Response model for chat interactions."""
    response: Dict[str, Any] = Field(..., description="Structured response from agents")
    session_id: Optional[str] = Field(None, description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "response": {
                    "original_query": "What are the biomarkers for lung cancer?",
                    "summary": "Found cancer information for lung cancer",
                    "detailed_results": {}
                },
                "session_id": "session_123",
                "timestamp": "2025-01-07T12:00:00"
            }
        }

class AgentInfo(BaseModel):
    """Information about a specialist agent."""
    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    capabilities: List[str] = Field(..., description="List of available tools/capabilities")
    collection: str = Field(..., description="MongoDB collection the agent manages")

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service health status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
    version: str = Field(..., description="Service version")
    agents_available: List[str] = Field(..., description="List of available agents")

class QueryIntent(BaseModel):
    """Represents a decomposed query intent."""
    query_type: QueryType = Field(..., description="Type of query")
    entity: str = Field(..., description="Target entity (cancer, gene, drug name)")
    specific_field: Optional[str] = Field(None, description="Specific field requested")
    target_agent: str = Field(..., description="Target specialist agent")
    tools_to_use: List[str] = Field(default_factory=list, description="Tools to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")

class AgentResponse(BaseModel):
    """Response from a specialist agent."""
    agent_name: str = Field(..., description="Name of the responding agent")
    query_intent: QueryIntent = Field(..., description="Original query intent")
    result: Dict[str, Any] = Field(..., description="Agent response data")
    success: bool = Field(..., description="Whether the request was successful")
    error_message: Optional[str] = Field(None, description="Error message if unsuccessful")

class CollectionSchema(BaseModel):
    """Schema information for a MongoDB collection."""
    name: str = Field(..., description="Collection name")
    description: str = Field(..., description="Collection purpose")
    key_fields: List[str] = Field(..., description="Important fields in the collection")
    total_documents: Optional[int] = Field(None, description="Number of documents")

class SystemStats(BaseModel):
    """System statistics and metrics."""
    total_queries_processed: int = Field(0, description="Total queries processed")
    active_sessions: int = Field(0, description="Currently active sessions")
    agents_status: Dict[str, bool] = Field(default_factory=dict, description="Agent availability status")
    collections_available: List[str] = Field(default_factory=list, description="Available collections")
    uptime_seconds: float = Field(0, description="System uptime in seconds")

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

# Collection-specific response models
class CancerInfo(BaseModel):
    """Cancer information model."""
    cancer_name: str
    cancer_organ_category: Optional[str] = None
    cancer_biomarkers_tags: List[str] = Field(default_factory=list)
    cancer_incidence_prevalance: Optional[str] = None
    cancer_survival_rates: Optional[str] = None
    nccn_guidelines_titles: List[str] = Field(default_factory=list)
    nccn_guidelines_links: List[str] = Field(default_factory=list)

class GeneInfo(BaseModel):
    """Gene information model."""
    gene_name: str
    ncbi_gene_code_for_gene: Optional[str] = None
    cancer_types: List[str] = Field(default_factory=list)
    drug_name: Optional[str] = None
    prognosis: Optional[str] = None
    efficacy: Optional[str] = None

class DrugInfo(BaseModel):
    """Drug information model."""
    drug_name: str
    target: List[str] = Field(default_factory=list)
    cancer_types: List[str] = Field(default_factory=list)
    biomarkers: List[str] = Field(default_factory=list)
    is_drug_approved: Optional[str] = None
    efficacy: Optional[str] = None
    mechanism_of_action: Optional[str] = None

class DrugIndiaInfo(BaseModel):
    """Drug India information model."""
    drug_name: str
    is_drug_approved_by_cdsco: Optional[str] = None
    brand_name: List[str] = Field(default_factory=list)
    company_name: List[str] = Field(default_factory=list)
    type_of_therapy: Optional[str] = None
    is_chemotherapy_drug: Optional[bool] = None 