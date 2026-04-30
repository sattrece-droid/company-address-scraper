"""
Pydantic models for request and response validation.
"""
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any


class Address(BaseModel):
    """Structured address data."""
    name: Optional[str] = None
    address: str
    city: str
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None


class CompanyResult(BaseModel):
    """Result of processing a single company."""
    company_name: str
    input_zip_code: Optional[str] = None
    website: Optional[str] = None
    status: str
    confidence: str
    addresses: List[Address] = []
    cached: bool = False
    timestamp: str
    error: Optional[str] = None


class JobStatusResponse(BaseModel):
    """Response for job status polling."""
    job_id: str
    status: str
    progress: float
    companies_processed: int
    total_companies: int
    results: Optional[List[CompanyResult]] = None
    completed_at: Optional[str] = None
    download_url: Optional[str] = None
    statistics: Optional[Dict[str, Any]] = None


class BatchJobRequest(BaseModel):
    """Request to process a batch of companies."""
    companies: List[Dict[str, Any]]  # company_name, zip_code, website


class JobCreatedResponse(BaseModel):
    """Response when a job is successfully created."""
    job_id: str
    total_companies: int
    message: str
