"""
Estimate API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from app.schemas.estimate import Estimate, EstimateCreate, EstimateUpdate, EstimateResponse
from app.services.estimate_service import EstimateService
from app.core.database import get_db

router = APIRouter()

@router.post("/", response_model=EstimateResponse)
async def create_estimate(estimate: EstimateCreate, db=Depends(get_db)):
    """Create new estimate"""
    service = EstimateService(db)
    try:
        new_estimate = service.create(estimate.dict())
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