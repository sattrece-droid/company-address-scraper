"""
FastAPI application entry point.
Configures CORS, middleware, and includes API routes.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from api.routes import router as api_router
from config import settings

app = FastAPI(
    title="Company Address Scraping Utility",
    description="Automatically find and scrape company physical locations.",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/jobs")

@app.get("/")
async def root():
    return {
        "message": "Company Address Scraping API is running",
        "docs": "/docs",
        "environment": settings.environment
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    """Ensure data directory exists on startup."""
    os.makedirs(settings.data_dir, exist_ok=True)
    print(f"Application started in {settings.environment} mode")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
