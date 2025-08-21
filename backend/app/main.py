"""
FastAPI Backend for MJ Estimate Generator
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.api import companies, documents, estimates
from app.api import invoices
from app.core.config import settings
from app.database import init_db

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="MJ Estimate API",
    description="API for MJ Estimate Generator",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(companies.router, prefix="/api/companies", tags=["Companies"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(estimates.router, prefix="/api/estimates", tags=["Estimates"])
app.include_router(invoices.router, prefix="/api", tags=["Invoices"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "MJ Estimate API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs"
    }

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "mj-estimate-api"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )