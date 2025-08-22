"""
Estimate API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from app.schemas.estimate import Estimate, EstimateCreate, EstimateUpdate, EstimateResponse
from app.services.estimate_service import EstimateService
from app.core.database import get_db

router = APIRouter()

@router.post("/", response_model=EstimateResponse)
async def create_estimate(estimate: EstimateCreate, db=Depends(get_db)):
    """Create new estimate"""
    service = EstimateService(db)
    
    # Convert to dict
    estimate_data = estimate.dict()
    
    # Get company code for estimate number generation
    company_code = None
    if estimate_data.get('company_id'):
        try:
            # Get company by ID to get the company_code
            company_response = db.table('companies').select('company_code').eq('id', estimate_data['company_id']).execute()
            if company_response.data and company_response.data[0].get('company_code'):
                company_code = company_response.data[0]['company_code']
        except Exception as e:
            print(f"Error fetching company code: {e}")
    
    # Generate estimate number if not provided
    if not estimate_data.get('estimate_number'):
        if company_code and estimate_data.get('client_address'):
            estimate_data['estimate_number'] = service.generate_estimate_number(
                estimate_data['client_address'],
                company_code
            )
        else:
            # Fallback to timestamp-based number
            estimate_data['estimate_number'] = f"EST-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    try:
        new_estimate = service.create(estimate_data)
        return EstimateResponse(data=new_estimate, message="Estimate created successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{estimate_id}", response_model=EstimateResponse)
async def get_estimate(estimate_id: str, db=Depends(get_db)):
    """Get single estimate"""
    service = EstimateService(db)
    estimate = service.get_by_id(estimate_id)
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    return EstimateResponse(data=estimate)

@router.put("/{estimate_id}", response_model=EstimateResponse)
async def update_estimate(estimate_id: str, estimate: EstimateUpdate, db=Depends(get_db)):
    """Update estimate"""
    service = EstimateService(db)
    try:
        updated_estimate = service.update(estimate_id, estimate.dict(exclude_none=True))
        if not updated_estimate:
            raise HTTPException(status_code=404, detail="Estimate not found")
        return EstimateResponse(data=updated_estimate, message="Estimate updated successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{estimate_id}")
async def delete_estimate(estimate_id: str, db=Depends(get_db)):
    """Delete estimate"""
    service = EstimateService(db)
    try:
        success = service.delete(estimate_id)
        if not success:
            raise HTTPException(status_code=404, detail="Estimate not found")
        return {"message": "Estimate deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))