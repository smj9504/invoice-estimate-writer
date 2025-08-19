"""
Company API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List
from app.schemas.company import Company, CompanyCreate, CompanyUpdate, CompanyResponse, CompaniesResponse
from app.services.company_service import CompanyService
from app.core.database import get_db

router = APIRouter()

@router.get("/", response_model=CompaniesResponse)
async def get_companies(db=Depends(get_db)):
    """Get all companies"""
    service = CompanyService(db)
    companies = service.get_all()
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
        updated_company = service.update(company_id, company.dict(exclude_none=True))
        if not updated_company:
            raise HTTPException(status_code=404, detail="Company not found")
        return CompanyResponse(data=updated_company, message="Company updated successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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
    """Upload company logo"""
    service = CompanyService(db)
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        logo_url = await service.upload_logo(company_id, file)
        return {"url": logo_url, "message": "Logo uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))