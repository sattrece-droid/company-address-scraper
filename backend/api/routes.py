"""
FastAPI routes for job creation, status polling, and results download.
"""
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Depends
from fastapi.responses import FileResponse
from api.auth import require_api_key
import uuid
import os
import re
from typing import Dict, List, Any
from pathlib import Path
from datetime import datetime

from api.models import JobCreatedResponse, JobStatusResponse
from utils.excel import ExcelHandler
from utils.job_store import JobStore
from services.job_processor import processor
from config import settings

router = APIRouter()

jobs = JobStore(os.path.join(os.path.dirname(__file__), "../../data/jobs"))

_UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')

def _validate_job_id(job_id: str) -> None:
    if not _UUID_RE.match(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID format.")


async def run_batch_job(job_id: str, companies: List[Dict[str, Any]]):
    """Background task to process a batch of companies."""
    try:
        jobs.update(job_id, {"status": "processing"})

        results = []
        total = len(companies)

        for i, company in enumerate(companies):
            try:
                result = await processor.process_company(
                    company.get("company_name"),
                    company.get("zip_code"),
                    company.get("website"),
                    company.get("mode")
                )
                results.append(result)

                # Persist progress after each company
                jobs.update(job_id, {
                    "companies_processed": i + 1,
                    "progress": ((i + 1) / total) * 100
                })
            except Exception as e:
                print(f"Error in background task for {company.get('company_name')}: {e}")
                results.append({
                    "company_name": company.get("company_name"),
                    "status": "error",
                    "error": str(e)
                })

        # Generate output Excel
        output_filename = f"results_{job_id}.xlsx"
        output_path = os.path.join(settings.data_dir, output_filename)
        ExcelHandler.generate_output_file(results, output_path)

        # Compute statistics
        total_addresses = sum(len(r.get("addresses", [])) for r in results)
        status_breakdown = {}
        for result in results:
            status = result.get("status", "unknown")
            status_breakdown[status] = status_breakdown.get(status, 0) + 1

        cached_results = sum(1 for r in results if r.get("cached", False))

        statistics = {
            "total_addresses_found": total_addresses,
            "status_breakdown": status_breakdown,
            "cached_results": cached_results,
            "average_addresses_per_company": total_addresses / total if total > 0 else 0
        }

        jobs.update(job_id, {
            "status": "completed",
            "results": results,
            "progress": 100.0,
            "completed_at": datetime.now().isoformat(),
            "download_url": f"/api/jobs/{job_id}/download",
            "statistics": statistics
        })
    except Exception as e:
        print(f"Fatal error in background task for job {job_id}: {e}")
        jobs.update(job_id, {
            "status": "failed",
            "error": str(e),
            "progress": 0.0
        })


@router.post("/upload", response_model=JobCreatedResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    _: str = Depends(require_api_key)
):
    """Upload Excel file and start processing job."""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload an Excel file.")
    
    # Save temporary file — use only the basename to prevent path traversal
    safe_name = Path(file.filename).name
    temp_path = os.path.join(settings.data_dir, f"temp_{uuid.uuid4()}_{safe_name}")
    os.makedirs(settings.data_dir, exist_ok=True)
    
    with open(temp_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    try:
        # Parse companies from Excel
        companies = ExcelHandler.parse_input_file(temp_path)
        
        if len(companies) > settings.max_companies_per_request:
            raise HTTPException(
                status_code=400, 
                detail=f"Maximum {settings.max_companies_per_request} companies allowed per request in free tier."
            )
        
        # Create job entry
        job_id = str(uuid.uuid4())
        jobs.set(job_id, {
            "id": job_id,
            "status": "pending",
            "progress": 0.0,
            "companies_processed": 0,
            "total_companies": len(companies),
            "results": None
        })
        
        # Start background processing
        background_tasks.add_task(run_batch_job, job_id, companies)

        return JobCreatedResponse(
            job_id=job_id,
            total_companies=len(companies),
            message=f"Job created successfully with {len(companies)} companies."
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, _: str = Depends(require_api_key)):
    """Poll for job status and progress."""
    _validate_job_id(job_id)
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=job["id"],
        status=job["status"],
        progress=job["progress"],
        companies_processed=job["companies_processed"],
        total_companies=job["total_companies"],
        results=job.get("results"),
        download_url=job.get("download_url"),
        completed_at=job.get("completed_at"),
        statistics=job.get("statistics")
    )


@router.get("/{job_id}/download")
async def download_results(job_id: str, _: str = Depends(require_api_key)):
    """Download the generated Excel results file."""
    _validate_job_id(job_id)
    job = jobs.get(job_id)
    if job is None or job["status"] != "completed":
        raise HTTPException(status_code=404, detail="Results not found or job not completed")
    
    filename = f"results_{job_id}.xlsx"
    file_path = os.path.join(settings.data_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File no longer exists")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
