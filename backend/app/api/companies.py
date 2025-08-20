"""
Company API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from typing import List, Optional
from app.schemas.company import Company, CompanyCreate, CompanyUpdate, CompanyResponse, CompaniesResponse
from app.services.company_service import CompanyService
from app.core.database import get_db

router = APIRouter()

@router.get("/", response_model=CompaniesResponse)
async def get_companies(
    search: Optional[str] = Query(None, description="Search term for name, address, email, or phone"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state"),
    db=Depends(get_db)
):
    """Get all companies with optional search and filters"""
    service = CompanyService(db)
    companies = service.get_all(search=search, city=city, state=state)
    return CompaniesResponse(data=companies, total=len(companies))

@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: str, db=Depends(get_db)):
    """Get single company by ID"""
    service = CompanyService(db)
    company = service.get_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyResponse(data=company)

@router.post("/", response_model=CompanyResponse)
async def create_company(company: CompanyCreate, db=Depends(get_db)):
    """Create new company"""
    service = CompanyService(db)
    try:
        new_company = service.create(company.dict())
        return CompanyResponse(data=new_company, message="Company created successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(company_id: str, company: CompanyUpdate, db=Depends(get_db)):
    """Update company"""
    service = CompanyService(db)
    try:
        # Clean the data - remove None values and timestamps
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
async def delete_company(company_id: str, db=Depends(get_db)):
    """Delete company"""
    service = CompanyService(db)
    try:
        success = service.delete(company_id)
        if not success:
            raise HTTPException(status_code=404, detail="Company not found")
        return {"message": "Company deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{company_id}/logo")
async def upload_logo(company_id: str, file: UploadFile = File(...), db=Depends(get_db)):
    """Upload company logo as base64"""
    service = CompanyService(db)
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Validate file size (5MB limit)
    file_size = 0
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