"""
Company API endpoints using the new modular database system.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from typing import List, Optional
import logging

from app.schemas.company import Company, CompanyCreate, CompanyUpdate, CompanyResponse, CompaniesResponse
from app.services.service_factory import get_company_service_dependency
from app.services.company_service import CompanyService
from app.core.interfaces import DatabaseException, ValidationError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=CompaniesResponse)
async def get_companies(
    search: Optional[str] = Query(None, description="Search term for name, address, email, or phone"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state"),
    limit: Optional[int] = Query(None, description="Maximum number of results", ge=1, le=1000),
    offset: Optional[int] = Query(None, description="Number of results to skip", ge=0),
    include_stats: bool = Query(False, description="Include statistics for each company"),
    service: CompanyService = Depends(get_company_service_dependency)
):
    """
    Get all companies with optional search, filters, and pagination.
    
    - **search**: Search across name, address, email, and phone
    - **city**: Filter by city name
    - **state**: Filter by state
    - **limit**: Maximum number of results (default: no limit)
    - **offset**: Number of results to skip for pagination
    - **include_stats**: Include invoice/estimate counts
    """
    try:
        if include_stats:
            companies = service.get_companies_with_stats()
            
            # Apply filters if provided
            if search or city or state:
                filtered_data = service.get_companies_with_filters(
                    search=search, city=city, state=state
                )
                # Match stats with filtered companies
                filtered_ids = {comp['id'] for comp in filtered_data['companies']}
                companies = [comp for comp in companies if comp['id'] in filtered_ids]
            
            # Apply pagination
            if offset:
                companies = companies[offset:]
            if limit:
                companies = companies[:limit]
            
            return CompaniesResponse(data=companies, total=len(companies))
        else:
            result = service.get_companies_with_filters(
                search=search,
                city=city,
                state=state,
                limit=limit,
                offset=offset
            )
            return CompaniesResponse(
                data=result['companies'],
                total=result['total'],
                count=result['count']
            )
            
    except DatabaseException as e:
        logger.error(f"Database error in get_companies: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error in get_companies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search", response_model=CompaniesResponse)
async def search_companies(
    q: str = Query(..., description="Search query", min_length=1),
    limit: Optional[int] = Query(50, description="Maximum number of results", ge=1, le=1000),
    service: CompanyService = Depends(get_company_service_dependency)
):
    """
    Search companies by name, address, email, or phone.
    
    - **q**: Search query (minimum 1 character)
    - **limit**: Maximum number of results
    """
    try:
        companies = service.search_companies(q)
        
        # Apply limit
        if limit and len(companies) > limit:
            companies = companies[:limit]
        
        return CompaniesResponse(data=companies, total=len(companies))
        
    except DatabaseException as e:
        logger.error(f"Database error in search_companies: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error in search_companies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: str,
    include_summary: bool = Query(False, description="Include comprehensive summary with statistics"),
    service: CompanyService = Depends(get_company_service_dependency)
):
    """
    Get single company by ID.
    
    - **company_id**: Unique company identifier
    - **include_summary**: Include related statistics and summary data
    """
    try:
        if include_summary:
            company = service.get_company_summary(company_id)
        else:
            company = service.get_by_id(company_id)
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        return CompanyResponse(data=company)
        
    except HTTPException:
        raise
    except DatabaseException as e:
        logger.error(f"Database error in get_company: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error in get_company: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/by-email/{email}", response_model=CompanyResponse)
async def get_company_by_email(
    email: str,
    service: CompanyService = Depends(get_company_service_dependency)
):
    """
    Get company by email address.
    
    - **email**: Company email address
    """
    try:
        company = service.get_by_email(email)
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        return CompanyResponse(data=company)
        
    except HTTPException:
        raise
    except DatabaseException as e:
        logger.error(f"Database error in get_company_by_email: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error in get_company_by_email: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=CompanyResponse)
async def create_company(
    company: CompanyCreate,
    service: CompanyService = Depends(get_company_service_dependency)
):
    """
    Create new company.
    
    - **name**: Company name (required)
    - **address**: Company address
    - **phone**: Phone number
    - **email**: Email address
    - **website**: Website URL
    - **city**: City
    - **state**: State
    - **zip_code**: ZIP code
    - **license_number**: License number
    - **insurance_info**: Insurance information
    """
    try:
        company_data = company.dict(exclude_none=True)
        new_company = service.create(company_data)
        
        return CompanyResponse(
            data=new_company,
            message="Company created successfully"
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseException as e:
        logger.error(f"Database error in create_company: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error in create_company: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    company: CompanyUpdate,
    service: CompanyService = Depends(get_company_service_dependency)
):
    """
    Update company.
    
    - **company_id**: Unique company identifier
    - All company fields are optional for update
    """
    try:
        update_data = company.dict(exclude_none=True)
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No data provided for update")
        
        updated_company = service.update(company_id, update_data)
        
        if not updated_company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        return CompanyResponse(
            data=updated_company,
            message="Company updated successfully"
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except DatabaseException as e:
        logger.error(f"Database error in update_company: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error in update_company: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{company_id}")
async def delete_company(
    company_id: str,
    force: bool = Query(False, description="Force delete even with dependent records"),
    service: CompanyService = Depends(get_company_service_dependency)
):
    """
    Delete company.
    
    - **company_id**: Unique company identifier
    - **force**: Force delete even if company has invoices or estimates
    """
    try:
        if force:
            success = service.delete(company_id)
        else:
            success = service.delete_with_validation(company_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Company not found")
        
        return {"message": "Company deleted successfully"}
        
    except ValueError as e:
        # This occurs when company has dependent records
        raise HTTPException(status_code=409, detail=str(e))
    except HTTPException:
        raise
    except DatabaseException as e:
        logger.error(f"Database error in delete_company: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error in delete_company: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{company_id}/logo")
async def upload_logo(
    company_id: str,
    file: UploadFile = File(...),
    service: CompanyService = Depends(get_company_service_dependency)
):
    """
    Upload company logo as base64.
    
    - **company_id**: Unique company identifier
    - **file**: Image file (PNG, JPG, GIF, etc.)
    
    File size limit: 5MB
    """
    try:
        result = await service.upload_logo(company_id, file)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseException as e:
        logger.error(f"Database error in upload_logo: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error in upload_logo: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats/summary")
async def get_companies_summary(
    service: CompanyService = Depends(get_company_service_dependency)
):
    """
    Get summary statistics for all companies.
    
    Returns counts and totals across all companies.
    """
    try:
        companies_with_stats = service.get_companies_with_stats()
        
        total_companies = len(companies_with_stats)
        total_invoices = sum(comp.get('invoice_count', 0) for comp in companies_with_stats)
        total_estimates = sum(comp.get('estimate_count', 0) for comp in companies_with_stats)
        
        # Companies by state
        state_counts = {}
        for company in companies_with_stats:
            state = company.get('state', 'Unknown')
            state_counts[state] = state_counts.get(state, 0) + 1
        
        return {
            'total_companies': total_companies,
            'total_invoices': total_invoices,
            'total_estimates': total_estimates,
            'companies_by_state': state_counts,
            'average_invoices_per_company': total_invoices / total_companies if total_companies > 0 else 0,
            'average_estimates_per_company': total_estimates / total_companies if total_companies > 0 else 0
        }
        
    except DatabaseException as e:
        logger.error(f"Database error in get_companies_summary: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error in get_companies_summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")