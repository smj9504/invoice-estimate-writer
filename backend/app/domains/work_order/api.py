"""
Work Order API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from .schemas import (
    WorkOrder, WorkOrderCreate, WorkOrderUpdate, WorkOrderResponse, 
    WorkOrdersResponse, WorkOrderFilter
)
from .service import WorkOrderService
from .models import WorkOrderStatus, DocumentType
from app.core.database_factory import get_database
from app.domains.auth.dependencies import get_current_staff
from app.domains.staff.models import Staff

router = APIRouter()


def get_work_order_service():
    """Dependency to get work order service"""
    return WorkOrderService(get_database())


@router.get("/", response_model=WorkOrdersResponse)
async def get_work_orders(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search term for work order number, client name, email, phone, or description"),
    status: Optional[WorkOrderStatus] = Query(None, description="Filter by status"),
    company_id: Optional[UUID] = Query(None, description="Filter by company ID"),
    assigned_to_staff_id: Optional[UUID] = Query(None, description="Filter by assigned staff ID"),
    created_by_staff_id: Optional[UUID] = Query(None, description="Filter by creator staff ID"),
    document_type: Optional[DocumentType] = Query(None, description="Filter by document type"),
    priority: Optional[str] = Query(None, description="Filter by priority (low, medium, high, urgent)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    service: WorkOrderService = Depends(get_work_order_service)
):
    """Get all work orders with optional filters"""
    try:
        # Build filter dictionary from query parameters
        filters = {}
        
        if status:
            filters['status'] = status
        if company_id:
            filters['company_id'] = company_id
        if assigned_to_staff_id:
            filters['assigned_to_staff_id'] = assigned_to_staff_id
        if created_by_staff_id:
            filters['created_by_staff_id'] = created_by_staff_id
        if document_type:
            filters['document_type'] = document_type
        if priority:
            filters['priority'] = priority
        if is_active is not None:
            filters['is_active'] = is_active
            
        # Handle date filters separately (not supported by base repository yet)
        # TODO: Add date range filtering support
        
        # Calculate pagination
        offset = (page - 1) * page_size
        
        # Get work orders from service with pagination
        if search:
            # Use search method if search term provided
            # TODO: Implement search in service
            work_orders = []
            total = 0
        else:
            # Regular filtering
            work_orders = service.get_all(
                filters=filters,
                order_by='-created_at',
                limit=page_size,
                offset=offset
            )
            
            # Get total count without pagination
            all_work_orders = service.get_all(filters=filters)
            total = len(all_work_orders)
        
        return WorkOrdersResponse(data=work_orders, total=total)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving work orders: {str(e)}")


@router.get("/{work_order_id}", response_model=WorkOrderResponse)
async def get_work_order(
    work_order_id: UUID, 
    service: WorkOrderService = Depends(get_work_order_service)
):
    """Get single work order by ID"""
    try:
        work_order = service.get_by_id(work_order_id)
        if not work_order:
            raise HTTPException(status_code=404, detail="Work order not found")
        return WorkOrderResponse(data=work_order)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving work order: {str(e)}")


@router.post("/", response_model=WorkOrderResponse)
async def create_work_order(
    work_order: WorkOrderCreate, 
    service: WorkOrderService = Depends(get_work_order_service),
    current_staff: Staff = Depends(get_current_staff)
):
    """Create new work order"""
    try:
        # Set the created_by_staff_id to the current authenticated staff
        work_order.created_by_staff_id = str(current_staff.id)
        new_work_order = service.create_work_order(work_order)
        return WorkOrderResponse(
            data=new_work_order, 
            message="Work order created successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating work order: {str(e)}")


@router.put("/{work_order_id}", response_model=WorkOrderResponse)
async def update_work_order(
    work_order_id: UUID, 
    work_order: WorkOrderUpdate, 
    service: WorkOrderService = Depends(get_work_order_service),
    current_staff: Staff = Depends(get_current_staff)
):
    """Update work order"""
    try:
        update_data = work_order.dict(exclude_none=True)
        
        # Remove protected fields
        protected_fields = ['id', 'created_at', 'created_by_staff_id']
        for field in protected_fields:
            update_data.pop(field, None)
        
        updated_work_order = service.update(work_order_id, update_data)
        if not updated_work_order:
            raise HTTPException(status_code=404, detail="Work order not found or update failed")
            
        return WorkOrderResponse(
            data=updated_work_order, 
            message="Work order updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Update failed: {str(e)}")


@router.delete("/{work_order_id}")
async def delete_work_order(
    work_order_id: UUID, 
    service: WorkOrderService = Depends(get_work_order_service),
    current_staff: Staff = Depends(get_current_staff)
):
    """Delete work order"""
    try:
        success = service.delete(work_order_id)
        if not success:
            raise HTTPException(status_code=404, detail="Work order not found")
        return {"message": "Work order deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error deleting work order: {str(e)}")


@router.patch("/{work_order_id}/status", response_model=WorkOrderResponse)
async def update_work_order_status(
    work_order_id: UUID,
    status: WorkOrderStatus,
    notes: Optional[str] = Query(None, description="Optional notes about the status change"),
    service: WorkOrderService = Depends(get_work_order_service),
    current_staff: Staff = Depends(get_current_staff)
):
    """Update work order status with timestamp tracking"""
    try:
        updated_work_order = service.update_work_order_status(
            work_order_id, status, str(current_staff.id), notes
        )
        
        if not updated_work_order:
            raise HTTPException(status_code=404, detail="Work order not found")
            
        return WorkOrderResponse(
            data=updated_work_order,
            message=f"Work order status updated to {status.value}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating status: {str(e)}")


@router.get("/company/{company_id}", response_model=WorkOrdersResponse)
async def get_work_orders_by_company(
    company_id: UUID,
    status: Optional[WorkOrderStatus] = Query(None, description="Filter by status"),
    service: WorkOrderService = Depends(get_work_order_service)
):
    """Get all work orders for a specific company"""
    try:
        work_orders = service.get_work_orders_by_company(company_id, status)
        return WorkOrdersResponse(data=work_orders, total=len(work_orders))
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving work orders: {str(e)}")


@router.get("/staff/{staff_id}", response_model=WorkOrdersResponse)
async def get_work_orders_by_staff(
    staff_id: UUID,
    assigned_only: bool = Query(False, description="Only return assigned work orders"),
    service: WorkOrderService = Depends(get_work_order_service)
):
    """Get work orders associated with a staff member"""
    try:
        work_orders = service.get_work_orders_by_staff(staff_id, assigned_only)
        return WorkOrdersResponse(data=work_orders, total=len(work_orders))
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving work orders: {str(e)}")


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    company_id: Optional[UUID] = Query(None, description="Filter by company ID"),
    service: WorkOrderService = Depends(get_work_order_service)
):
    """Get dashboard statistics for work orders"""
    try:
        stats = service.get_dashboard_stats(company_id)
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")


@router.post("/generate-number")
async def generate_work_order_number(
    company_id: UUID = Query(..., description="Company ID for work order"),
    service: WorkOrderService = Depends(get_work_order_service)
):
    """Generate a new work order number"""
    try:
        work_order_number = service.generate_work_order_number(company_id)
        return {"work_order_number": work_order_number}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating work order number: {str(e)}")


@router.get("/statuses/list")
async def get_work_order_statuses():
    """Get list of available work order statuses"""
    return {
        "statuses": [
            {"value": status.value, "label": status.value.replace("_", " ").title()}
            for status in WorkOrderStatus
        ]
    }


@router.get("/document-types/list")
async def get_document_types():
    """Get list of available document types"""
    return {
        "document_types": [
            {"value": doc_type.value, "label": doc_type.value.replace("_", " ").title()}
            for doc_type in DocumentType
        ]
    }


@router.get("/priorities/list")
async def get_priority_levels():
    """Get list of available priority levels"""
    return {
        "priorities": [
            {"value": "low", "label": "Low"},
            {"value": "medium", "label": "Medium"},
            {"value": "high", "label": "High"},
            {"value": "urgent", "label": "Urgent"}
        ]
    }