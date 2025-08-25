"""
FastAPI Backend for MJ Estimate Generator
Main application entry point with comprehensive database abstraction system
"""

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime
import logging
import sys
from contextlib import asynccontextmanager

# API and core imports
from app.api import companies_modular
from app.api import companies, documents, estimates, invoices
from app.work_order import api as work_order_api
from app.payment import api as payment_api
from app.credit import api as credit_api
from app.staff import api as staff_api
from app.core.config import settings
from app.core.database_factory import get_database, db_factory
from app.services.service_factory import get_service_factory
from app.core.interfaces import DatabaseException, ConnectionError, ConfigurationError

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL or "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log') if settings.ENVIRONMENT == 'production' else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    Handles database initialization and cleanup.
    """
    logger.info(f"Starting MJ Estimate API in {settings.ENVIRONMENT} environment")
    
    try:
        # Initialize database system
        database = get_database()
        logger.info(f"Database system initialized: {database.provider_name}")
        
        # Perform health check
        if database.health_check():
            logger.info("Database health check passed")
        else:
            logger.warning("Database health check failed, but continuing...")
        
        # Initialize service factory
        service_factory = get_service_factory()
        service_factory.set_database(database)
        
        # Initialize database tables
        if hasattr(database, 'init_database'):
            database.init_database()
            logger.info("Database tables initialized")
        
        logger.info("Application startup completed successfully")
        yield
        
    except ConfigurationError as e:
        logger.error(f"Configuration error during startup: {e}")
        raise
    except ConnectionError as e:
        logger.error(f"Database connection error during startup: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during startup: {e}")
        raise
    finally:
        # Cleanup on shutdown
        logger.info("Shutting down application...")
        try:
            db_factory.reset()
            get_service_factory().reset()
            logger.info("Application shutdown completed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Create FastAPI app with lifespan management
app = FastAPI(
    title="MJ Estimate API",
    description="API for MJ Estimate Generator with modular database system",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware for SQLAdmin authentication
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom handler for validation errors to provide more details"""
    logger.error(f"Validation error on {request.url}: {exc.errors()}")
    logger.error(f"Request body: {exc.body}")
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": str(exc.body),
            "message": "Request validation failed",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(DatabaseException)
async def database_exception_handler(request: Request, exc: DatabaseException):
    """Custom handler for database errors"""
    logger.error(f"Database error on {request.url}: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "message": "Database error occurred",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat(),
            "type": "database_error"
        }
    )


@app.exception_handler(ConnectionError)
async def connection_exception_handler(request: Request, exc: ConnectionError):
    """Custom handler for connection errors"""
    logger.error(f"Connection error on {request.url}: {exc}")
    
    return JSONResponse(
        status_code=503,
        content={
            "message": "Database connection error",
            "detail": "Service temporarily unavailable",
            "timestamp": datetime.utcnow().isoformat(),
            "type": "connection_error"
        }
    )


@app.exception_handler(ConfigurationError)
async def configuration_exception_handler(request: Request, exc: ConfigurationError):
    """Custom handler for configuration errors"""
    logger.error(f"Configuration error on {request.url}: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "message": "Configuration error",
            "detail": "Service misconfigured",
            "timestamp": datetime.utcnow().isoformat(),
            "type": "configuration_error"
        }
    )


# Setup SQLAdmin directly on the FastAPI app
# This must happen AFTER middleware setup
database = get_database()
if hasattr(database, 'engine'):
    try:
        from sqladmin import Admin
        from app.admin import (
            AdminAuth, CompanyAdmin, InvoiceAdmin, InvoiceItemAdmin, 
            EstimateAdmin, EstimateItemAdmin, PlumberReportAdmin, DocumentAdmin
        )
        
        # Create authentication backend
        authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)
        
        # Create admin instance directly on the FastAPI app
        # Do NOT specify base_url parameter
        admin = Admin(
            app, 
            database.engine,
            title="MJ Estimate Database Admin",
            authentication_backend=authentication_backend
        )
        
        # Add all model views
        admin.add_view(CompanyAdmin)
        admin.add_view(InvoiceAdmin)
        admin.add_view(InvoiceItemAdmin)
        admin.add_view(EstimateAdmin)
        admin.add_view(EstimateItemAdmin)
        admin.add_view(PlumberReportAdmin)
        admin.add_view(DocumentAdmin)
        
        logger.info("SQLAdmin successfully initialized at /admin")
    except Exception as e:
        logger.error(f"Failed to initialize SQLAdmin: {e}", exc_info=True)
else:
    logger.warning("Database does not have engine attribute - SQLAdmin not initialized")

# Include routers AFTER SQLAdmin setup
# New modular endpoints
app.include_router(
    companies_modular.router, 
    prefix="/api/v2/companies", 
    tags=["Companies (Modular)"]
)

# Legacy endpoints (for backward compatibility)
app.include_router(companies.router, prefix="/api/companies", tags=["Companies (Legacy)"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(estimates.router, prefix="/api/estimates", tags=["Estimates"])
app.include_router(invoices.router, prefix="/api/invoices", tags=["Invoices"])

# New Work Order System endpoints
app.include_router(work_order_api.router, prefix="/api/work-orders", tags=["Work Orders"])
app.include_router(payment_api.router, prefix="/api/payments", tags=["Payments & Billing"])
app.include_router(credit_api.router, prefix="/api/credits", tags=["Credits & Discounts"])
app.include_router(staff_api.router, prefix="/api/staff", tags=["Staff Management"])


# System information endpoints
@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "name": "MJ Estimate API",
        "version": "2.0.0",
        "status": "active",
        "environment": settings.ENVIRONMENT,
        "database": get_database().provider_name,
        "docs": "/docs",
        "api_versions": {
            "v1": "/api",
            "v2": "/api/v2"
        }
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        database = get_database()
        db_healthy = database.health_check()
        
        service_factory = get_service_factory()
        service_info = service_factory.get_service_info()
        
        return {
            "status": "healthy" if db_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "mj-estimate-api",
            "version": "2.0.0",
            "environment": settings.ENVIRONMENT,
            "database": {
                "provider": database.provider_name,
                "healthy": db_healthy,
                "info": db_factory.get_database_info()
            },
            "services": service_info,
            "components": {
                "api": "healthy",
                "database": "healthy" if db_healthy else "unhealthy",
                "services": "healthy"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "mj-estimate-api",
                "error": str(e)
            }
        )


@app.get("/system/info")
async def system_info():
    """Get detailed system information"""
    try:
        database = get_database()
        service_factory = get_service_factory()
        
        return {
            "application": {
                "name": "MJ Estimate API",
                "version": "2.0.0",
                "environment": settings.ENVIRONMENT,
                "debug": settings.DEBUG
            },
            "database": db_factory.get_database_info(),
            "services": service_factory.get_service_info(),
            "configuration": {
                "cors_origins": settings.CORS_ORIGINS,
                "log_level": settings.LOG_LEVEL,
                "api_prefix": settings.API_PREFIX
            },
            "features": {
                "modular_database": True,
                "service_factory": True,
                "error_handling": True,
                "connection_pooling": True,
                "retry_mechanisms": True,
                "health_monitoring": True
            }
        }
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise


@app.get("/system/database/switch/{provider}")
async def switch_database_provider(provider: str):
    """
    Switch database provider (for testing/development only).
    
    WARNING: This endpoint should not be available in production.
    """
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=403, 
            detail="Database switching not allowed in production"
        )
    
    try:
        # Reset current connections
        db_factory.reset()
        get_service_factory().reset()
        
        # Create new database with specified provider
        database = db_factory.create_database(provider)
        service_factory = get_service_factory()
        service_factory.set_database(database)
        
        return {
            "message": f"Successfully switched to {provider} database",
            "provider": database.provider_name,
            "healthy": database.health_check(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to switch database provider: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "message": "Failed to switch database provider",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )




if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower() if settings.LOG_LEVEL else "info"
    )