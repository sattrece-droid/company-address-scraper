"""
FastAPI routes for job creation, status polling, and results download.
"""
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
import uuid
import os
from typing import Dict, List, Any
from pathlib import Path

from api.models import JobCreatedResponse, JobStatusResponse
from utils.excel import ExcelHandler
from services.job_processor import processor
from config import settings

router = APIRouter()

# In-memory job store (replace with Redis/DB in production)
jobs: Dict[str, Dict[str, Any]] = {}


async def run_batch_job(job_id: str, companies: List[Dict[str, Any]]):
    """Background task to process a batch of companies."""
    jobs[job_id]["status"] = "processing"
    
    results = []
    total = len(companies)
    
    for i, company in enumerate(companies):
        try:
            result = await processor.process_company(
                company.get("company_name"),
                company.get("zip_code"),
                company.get("website")
            )
            results.append(result)
            
            # Update job progress
            jobs[job_id]["companies_processed"] = i + 1
            jobs[job_id]["progress"] = ((i + 1) / total) * 100
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
    
    # Update final job state
    jobs[job_id].update({
        "status": "completed",
        "results": results,
        "progress": 100.0,
        "completed_at": Path(output_path).name,
        "download_url": f"/api/jobs/{job_id}/download"
    })


@router.post("/upload", response_model=JobCreatedResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload Excel file and start processing job."""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload an Excel file.")
    
    # Save temporary file
    temp_path = os.path.join(settings.data_dir, f"temp_{uuid.uuid4()}_{file.filename}")
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
        jobs[job_id] = {
            "id": job_id,
            "status": "pending",
            "progress": 0.0,
            "companies_processed": 0,
            "total_companies": len(companies),
            "results": None
        }
        
        # Start background processing
        background_tasks.add_task(run_batch_job, job_id, companies)
        
        return JobCreatedResponse(
            job_id=job_id,
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
async def get_job_status(job_id: str):
    """Poll for job status and progress."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    return JobStatusResponse(
        job_id=job["id"],
        status=job["status"],
        progress=job["progress"],
        companies_processed=job["companies_processed"],
        total_companies=job["total_companies"],
        results=job.get("results"),
        download_url=job.get("download_url")
    )


@router.get("/{job_id}/download")
async def download_results(job_id: str):
    """Download the generated Excel results file."""
    if job_id not in jobs or jobs[job_id]["status"] != "completed":
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
