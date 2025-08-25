"""
Company API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from typing import List, Optional
from app.schemas.company import Company, CompanyCreate, CompanyUpdate, CompanyResponse, CompaniesResponse
from app.services.service_factory import get_company_service_dependency
from app.services.company_service import CompanyService

router = APIRouter()

@router.get("/", response_model=CompaniesResponse)
async def get_companies(
    search: Optional[str] = Query(None, description="Search term for name, address, email, or phone"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state"),
    service: CompanyService = Depends(get_company_service_dependency)
):
    """Get all companies with optional filters"""
    # Use the specialized method for company filtering
    if search or city or state:
        result = service.get_companies_with_filters(
            search=search,
            city=city,
            state=state
        )
        companies = result.get('companies', [])
    else:
        companies = service.get_all()
    
    return CompaniesResponse(data=companies, total=len(companies))

@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: str, service: CompanyService = Depends(get_company_service_dependency)):
    """Get single company by ID"""
    company = service.get_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyResponse(data=company)

@router.post("/", response_model=CompanyResponse)
async def create_company(company: CompanyCreate, service: CompanyService = Depends(get_company_service_dependency)):
    """Create new company"""
    try:
        new_company = service.create(company.dict())
        return CompanyResponse(data=new_company, message="Company created successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(company_id: str, company: CompanyUpdate, service: CompanyService = Depends(get_company_service_dependency)):
    """Update company"""
    try:
        update_data = company.dict(exclude_none=True)
        update_data.pop('created_at', None)
        update_data.pop('updated_at', None)
        
        updated_company = service.update(company_id, update_data)
        if not updated_company:
            raise HTTPException(status_code=404, detail="Company not found or update failed")
        return CompanyResponse(data=updated_company, message="Company updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Update error: {e}")
        raise HTTPException(status_code=400, detail=f"Update failed: {str(e)}")

@router.delete("/{company_id}")
async def delete_company(company_id: str, service: CompanyService = Depends(get_company_service_dependency)):
    """Delete company"""
    try:
        success = service.delete(company_id)
        if not success:
            raise HTTPException(status_code=404, detail="Company not found")
        return {"message": "Company deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{company_id}/logo")
async def upload_logo(company_id: str, file: UploadFile = File(...), service: CompanyService = Depends(get_company_service_dependency)):
    """Upload company logo as base64"""
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Validate file size (5MB limit)
    content = await file.read()
    file_size = len(content)
    if file_size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 5MB")
    
    # Reset file position
    await file.seek(0)
    
    try:
        logo_data = await service.upload_logo(company_id, file)
        return {"logo": logo_data, "message": "Logo uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))