"""
Company API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from typing import Optional

from app.core.database_factory import get_database
from .schemas import (
    CompanyCreate, 
    CompanyUpdate, 
    CompanyResponse, 
    CompanyFilter,
    CompanyPaginatedResponse
)
from .service import CompanyService

def get_company_service():
    """Get company service instance"""
    return CompanyService(get_database())

router = APIRouter(
    tags=["companies"]
)


@router.get("/", response_model=CompanyPaginatedResponse)
async def get_companies(
    search: Optional[str] = Query(None, description="Search term for name, address, email, or phone"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_default: Optional[bool] = Query(None, description="Filter by default status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    service: CompanyService = Depends(get_company_service)
):
    """Get all companies with optional filters and pagination"""
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Create filter params
    filter_params = CompanyFilter(
        search=search,
        city=city,
        state=state,
        is_active=is_active,
        is_default=is_default
    )
    
    # Get companies with filters
    result = service.get_companies_with_filters(
        filter_params=filter_params,
        limit=per_page,
        offset=offset
    )
    
    companies = result.get('companies', [])
    total = result.get('total', len(companies))
    pages = (total + per_page - 1) // per_page  # Calculate total pages
    
    return CompanyPaginatedResponse(
        items=companies,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: str, 
    service: CompanyService = Depends(get_company_service)
):
    """Get single company by ID"""
    company = service.get_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyResponse(**company)


@router.post("/", response_model=CompanyResponse, status_code=201)
async def create_company(
    company: CompanyCreate, 
    service: CompanyService = Depends(get_company_service)
):
    """Create new company"""
    try:
        new_company = service.create(company)
        return CompanyResponse(**new_company)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str, 
    company: CompanyUpdate, 
    service: CompanyService = Depends(get_company_service)
):
    """Update company"""
    try:
        updated_company = service.update(company_id, company)
        if not updated_company:
            raise HTTPException(status_code=404, detail="Company not found")
        return CompanyResponse(**updated_company)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Update failed: {str(e)}")


@router.delete("/{company_id}", status_code=204)
async def delete_company(
    company_id: str, 
    service: CompanyService = Depends(get_company_service)
):
    """Delete company"""
    try:
        success = service.delete(company_id)
        if not success:
            raise HTTPException(status_code=404, detail="Company not found")
        return None  # 204 No Content
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{company_id}/logo", response_model=dict)
async def upload_logo(
    company_id: str, 
    file: UploadFile = File(...), 
    service: CompanyService = Depends(get_company_service)
):
    """Upload company logo as base64"""
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Validate file size (5MB limit)
    content = await file.read()
    file_size = len(content)
    if file_size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 5MB")
    
    # Reset file position
    await file.seek(0)
    
    try:
        result = await service.upload_logo(company_id, file)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{company_id}/set-default", response_model=CompanyResponse)
async def set_default_company(
    company_id: str,
    service: CompanyService = Depends(get_company_service)
):
    """Set a company as the default company"""
    try:
        updated_company = service.set_default_company(company_id)
        if not updated_company:
            raise HTTPException(status_code=404, detail="Company not found")
        return CompanyResponse(**updated_company)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats", response_model=list[dict])
async def get_companies_with_stats(
    service: CompanyService = Depends(get_company_service)
):
    """Get companies with invoice and estimate counts"""
    try:
        companies = service.get_companies_with_stats()
        return companies
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))