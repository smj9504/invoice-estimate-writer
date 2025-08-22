"""
FastAPI Backend for MJ Estimate Generator
Main application entry point
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime
import logging

from app.api import companies, documents, estimates
from app.api import invoices, plumber_reports
from app.core.config import settings
from app.database import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)

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

# Custom validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom handler for validation errors to provide more details"""
    logger = logging.getLogger(__name__)
    logger.error(f"Validation error: {exc.errors()}")
    logger.error(f"Request body: {exc.body}")
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": str(exc.body),
            "message": "Request validation failed"
        }
    )

# Include routers
app.include_router(companies.router, prefix="/api/companies", tags=["Companies"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(estimates.router, prefix="/api/estimates", tags=["Estimates"])
app.include_router(invoices.router, prefix="/api", tags=["Invoices"])
app.include_router(plumber_reports.router, prefix="/api/plumber-reports", tags=["Plumber Reports"])

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