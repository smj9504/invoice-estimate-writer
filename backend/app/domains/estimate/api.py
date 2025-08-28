"""
Estimate domain API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Response
from typing import List, Optional
from datetime import datetime, timedelta
import tempfile
import os
import json

from app.core.database_factory import get_db_session as get_db
from app.domains.estimate.schemas import (
    EstimateCreate,
    EstimateUpdate,
    EstimateResponse,
    EstimateListResponse,
    EstimateItemResponse,
    EstimatePDFRequest
)
from app.common.services.pdf_service import pdf_service
from app.domains.estimate.service import EstimateService

router = APIRouter()


@router.get("/", response_model=List[EstimateListResponse])
async def list_estimates(
    skip: int = 0,
    limit: int = 100,
    client_name: Optional[str] = None,
    status: Optional[str] = None,
    db=Depends(get_db)
):
    """List all estimates with optional filtering"""
    from app.core.database_factory import get_database
    database = get_database()
    service = EstimateService(database)
    
    # Get estimates
    estimates = service.get_all(limit=limit, offset=skip)
    
    # Filter by status if provided
    if status:
        estimates = [est for est in estimates if est.get('status') == status]
    
    # Filter by client_name if provided
    if client_name:
        estimates = [est for est in estimates if client_name.lower() in est.get('client_name', '').lower()]
    
    # Convert to response format
    return [
        EstimateListResponse(
            id=est['id'],
            estimate_number=est.get('estimate_number', ''),
            company_id=est.get('company_id'),
            client_name=est.get('client_name', ''),
            total_amount=est.get('total_amount', 0),
            status=est.get('status', 'draft'),
            estimate_date=est.get('estimate_date'),
            valid_until=est.get('valid_until'),
            created_at=est.get('created_at'),
            updated_at=est.get('updated_at')
        )
        for est in estimates
    ]


@router.get("/insurance", response_model=List[EstimateListResponse])
async def list_insurance_estimates(
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_db)
):
    """List insurance estimates"""
    from app.core.database_factory import get_database
    database = get_database()
    service = EstimateService(database)
    
    insurance_estimates = service.get_insurance_estimates()
    
    # Apply pagination
    paginated = insurance_estimates[skip:skip + limit]
    
    # Convert to response format
    return [
        EstimateListResponse(
            id=est['id'],
            estimate_number=est.get('estimate_number', ''),
            company_id=est.get('company_id'),
            client_name=est.get('client_name', ''),
            total_amount=est.get('total_amount', 0),
            status=est.get('status', 'draft'),
            estimate_date=est.get('estimate_date'),
            valid_until=est.get('valid_until'),
            created_at=est.get('created_at'),
            updated_at=est.get('updated_at')
        )
        for est in paginated
    ]


@router.get("/{estimate_id}", response_model=EstimateResponse)
async def get_estimate(estimate_id: str, db=Depends(get_db)):
    """Get a specific estimate by ID"""
    from app.core.database_factory import get_database
    database = get_database()
    service = EstimateService(database)
    
    estimate = service.get_with_items(estimate_id)
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    # Parse room_data if it's a string
    if estimate.get('room_data') and isinstance(estimate['room_data'], str):
        try:
            estimate['room_data'] = json.loads(estimate['room_data'])
        except json.JSONDecodeError:
            pass
    
    # Convert to response format
    return EstimateResponse(
        id=estimate['id'],
        estimate_number=estimate.get('estimate_number', ''),
        company_id=estimate.get('company_id'),
        client_name=estimate.get('client_name', ''),
        client_address=estimate.get('client_address'),
        client_phone=estimate.get('client_phone'),
        client_email=estimate.get('client_email'),
        estimate_date=estimate.get('estimate_date'),
        valid_until=estimate.get('valid_until'),
        status=estimate.get('status', 'draft'),
        subtotal=estimate.get('subtotal', 0),
        tax_rate=estimate.get('tax_rate', 0),
        tax_amount=estimate.get('tax_amount', 0),
        discount_amount=estimate.get('discount_amount', 0),
        total_amount=estimate.get('total_amount', 0),
        claim_number=estimate.get('claim_number'),
        policy_number=estimate.get('policy_number'),
        deductible=estimate.get('deductible'),
        depreciation_amount=estimate.get('depreciation_amount', 0),
        acv_amount=estimate.get('acv_amount', 0),
        rcv_amount=estimate.get('rcv_amount', 0),
        notes=estimate.get('notes'),
        terms=estimate.get('terms'),
        room_data=estimate.get('room_data'),
        created_at=estimate.get('created_at'),
        updated_at=estimate.get('updated_at'),
        items=[
            EstimateItemResponse(
                id=item.get('id'),
                estimate_id=item.get('estimate_id'),
                room=item.get('room'),
                description=item.get('description', ''),
                quantity=item.get('quantity', 0),
                unit=item.get('unit', ''),
                rate=item.get('rate', 0),
                amount=item.get('amount', 0),
                tax_rate=item.get('tax_rate', 0),
                tax_amount=item.get('tax_amount', 0),
                category=item.get('category'),
                depreciation_rate=item.get('depreciation_rate', 0),
                depreciation_amount=item.get('depreciation_amount', 0),
                acv_amount=item.get('acv_amount', 0),
                rcv_amount=item.get('rcv_amount', 0),
                order_index=item.get('order_index'),
                created_at=item.get('created_at'),
                updated_at=item.get('updated_at')
            )
            for item in estimate.get('items', [])
        ]
    )


@router.post("/", response_model=EstimateResponse)
async def create_estimate(estimate_data: EstimateCreate, db=Depends(get_db)):
    """Create a new estimate"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Received estimate data: {estimate_data.dict()}")
    
    # Initialize service
    from app.core.database_factory import get_database
    database = get_database()
    service = EstimateService(database)
    
    # Determine company code if company_id is provided
    company_code = None
    if estimate_data.company_id:
        try:
            from app.domains.company.repository import get_company_repository
            company_repo = get_company_repository(db)
            company = company_repo.get_by_id(str(estimate_data.company_id))
            if company:
                company_code = company.get('company_code')
        except Exception as e:
            logger.error(f"Error fetching company: {e}")
    
    # Generate estimate number if not provided
    if not estimate_data.estimate_number:
        if company_code and estimate_data.client_address:
            # Try to generate a location-based estimate number
            try:
                from app.services.document_service import generate_estimate_number
                estimate_data.estimate_number = generate_estimate_number(
                    estimate_data.client_address,
                    company_code
                )
            except:
                # Fallback to timestamp-based number
                estimate_data.estimate_number = f"EST-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        else:
            # Fallback to timestamp-based number
            estimate_data.estimate_number = f"EST-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # Convert dates if provided
    estimate_date = estimate_data.estimate_date or datetime.now()
    valid_until = estimate_data.valid_until or (datetime.now() + timedelta(days=30))
    
    # Prepare data for repository
    estimate_dict = {
        'estimate_number': estimate_data.estimate_number,
        'company_id': str(estimate_data.company_id) if estimate_data.company_id else None,
        'client_name': estimate_data.client_name,
        'client_address': estimate_data.client_address,
        'client_phone': estimate_data.client_phone,
        'client_email': estimate_data.client_email,
        'estimate_date': estimate_date,
        'valid_until': valid_until,
        'status': estimate_data.status or 'draft',
        'notes': estimate_data.notes,
        'terms': estimate_data.terms,
        'claim_number': estimate_data.claim_number,
        'policy_number': estimate_data.policy_number,
        'deductible': estimate_data.deductible,
        'room_data': estimate_data.room_data,
        'items': [
            {
                'room': item.room,
                'description': item.description,
                'quantity': item.quantity,
                'unit': item.unit,
                'rate': item.rate,
                'category': item.category,
                'depreciation_rate': item.depreciation_rate,
                'depreciation_amount': item.depreciation_amount,
                'acv_amount': item.acv_amount,
                'rcv_amount': item.rcv_amount
            }
            for item in estimate_data.items
        ]
    }
    
    # Create estimate using service
    created_estimate = service.create_with_items(estimate_dict)
    
    # Parse room_data if it's a string
    if created_estimate.get('room_data') and isinstance(created_estimate['room_data'], str):
        try:
            created_estimate['room_data'] = json.loads(created_estimate['room_data'])
        except json.JSONDecodeError:
            pass
    
    # Convert to response format
    return EstimateResponse(
        id=created_estimate['id'],
        estimate_number=created_estimate.get('estimate_number', ''),
        company_id=created_estimate.get('company_id'),
        client_name=created_estimate.get('client_name', ''),
        client_address=created_estimate.get('client_address'),
        client_phone=created_estimate.get('client_phone'),
        client_email=created_estimate.get('client_email'),
        estimate_date=created_estimate.get('estimate_date'),
        valid_until=created_estimate.get('valid_until'),
        status=created_estimate.get('status', 'draft'),
        subtotal=created_estimate.get('subtotal', 0),
        tax_rate=created_estimate.get('tax_rate', 0),
        tax_amount=created_estimate.get('tax_amount', 0),
        discount_amount=created_estimate.get('discount_amount', 0),
        total_amount=created_estimate.get('total_amount', 0),
        claim_number=created_estimate.get('claim_number'),
        policy_number=created_estimate.get('policy_number'),
        deductible=created_estimate.get('deductible'),
        depreciation_amount=created_estimate.get('depreciation_amount', 0),
        acv_amount=created_estimate.get('acv_amount', 0),
        rcv_amount=created_estimate.get('rcv_amount', 0),
        notes=created_estimate.get('notes'),
        terms=created_estimate.get('terms'),
        room_data=created_estimate.get('room_data'),
        created_at=created_estimate.get('created_at'),
        updated_at=created_estimate.get('updated_at'),
        items=[
            EstimateItemResponse(
                id=item.get('id'),
                estimate_id=item.get('estimate_id'),
                room=item.get('room'),
                description=item.get('description', ''),
                quantity=item.get('quantity', 0),
                unit=item.get('unit', ''),
                rate=item.get('rate', 0),
                amount=item.get('amount', 0),
                tax_rate=item.get('tax_rate', 0),
                tax_amount=item.get('tax_amount', 0),
                category=item.get('category'),
                depreciation_rate=item.get('depreciation_rate', 0),
                depreciation_amount=item.get('depreciation_amount', 0),
                acv_amount=item.get('acv_amount', 0),
                rcv_amount=item.get('rcv_amount', 0),
                order_index=item.get('order_index'),
                created_at=item.get('created_at'),
                updated_at=item.get('updated_at')
            )
            for item in created_estimate.get('items', [])
        ]
    )


@router.put("/{estimate_id}", response_model=EstimateResponse)
async def update_estimate(
    estimate_id: str,
    estimate_data: EstimateUpdate,
    db=Depends(get_db)
):
    """Update an existing estimate"""
    from app.core.database_factory import get_database
    database = get_database()
    service = EstimateService(database)
    
    # Check if estimate exists
    existing = service.get_by_id(estimate_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    # Prepare update data
    update_dict = estimate_data.dict(exclude_unset=True)
    
    # Update estimate with items
    updated_estimate = service.update_with_items(estimate_id, update_dict)
    if not updated_estimate:
        raise HTTPException(status_code=500, detail="Failed to update estimate")
    
    # Parse room_data if it's a string
    if updated_estimate.get('room_data') and isinstance(updated_estimate['room_data'], str):
        try:
            updated_estimate['room_data'] = json.loads(updated_estimate['room_data'])
        except json.JSONDecodeError:
            pass
    
    # Convert to response format
    return EstimateResponse(
        id=updated_estimate['id'],
        estimate_number=updated_estimate.get('estimate_number', ''),
        company_id=updated_estimate.get('company_id'),
        client_name=updated_estimate.get('client_name', ''),
        client_address=updated_estimate.get('client_address'),
        client_phone=updated_estimate.get('client_phone'),
        client_email=updated_estimate.get('client_email'),
        estimate_date=updated_estimate.get('estimate_date'),
        valid_until=updated_estimate.get('valid_until'),
        status=updated_estimate.get('status', 'draft'),
        subtotal=updated_estimate.get('subtotal', 0),
        tax_rate=updated_estimate.get('tax_rate', 0),
        tax_amount=updated_estimate.get('tax_amount', 0),
        discount_amount=updated_estimate.get('discount_amount', 0),
        total_amount=updated_estimate.get('total_amount', 0),
        claim_number=updated_estimate.get('claim_number'),
        policy_number=updated_estimate.get('policy_number'),
        deductible=updated_estimate.get('deductible'),
        depreciation_amount=updated_estimate.get('depreciation_amount', 0),
        acv_amount=updated_estimate.get('acv_amount', 0),
        rcv_amount=updated_estimate.get('rcv_amount', 0),
        notes=updated_estimate.get('notes'),
        terms=updated_estimate.get('terms'),
        room_data=updated_estimate.get('room_data'),
        created_at=updated_estimate.get('created_at'),
        updated_at=updated_estimate.get('updated_at'),
        items=[
            EstimateItemResponse(
                id=item.get('id'),
                estimate_id=item.get('estimate_id'),
                room=item.get('room'),
                description=item.get('description', ''),
                quantity=item.get('quantity', 0),
                unit=item.get('unit', ''),
                rate=item.get('rate', 0),
                amount=item.get('amount', 0),
                tax_rate=item.get('tax_rate', 0),
                tax_amount=item.get('tax_amount', 0),
                category=item.get('category'),
                depreciation_rate=item.get('depreciation_rate', 0),
                depreciation_amount=item.get('depreciation_amount', 0),
                acv_amount=item.get('acv_amount', 0),
                rcv_amount=item.get('rcv_amount', 0),
                order_index=item.get('order_index'),
                created_at=item.get('created_at'),
                updated_at=item.get('updated_at')
            )
            for item in updated_estimate.get('items', [])
        ]
    )


@router.delete("/{estimate_id}")
async def delete_estimate(estimate_id: str, db=Depends(get_db)):
    """Delete an estimate"""
    from app.core.database_factory import get_database
    database = get_database()
    service = EstimateService(database)
    
    # Check if estimate exists
    existing = service.get_by_id(estimate_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    # Delete estimate
    if not service.delete(estimate_id):
        raise HTTPException(status_code=500, detail="Failed to delete estimate")
    
    return {"message": "Estimate deleted successfully"}


@router.post("/{estimate_id}/accept")
async def accept_estimate(estimate_id: str, db=Depends(get_db)):
    """Accept an estimate"""
    from app.core.database_factory import get_database
    database = get_database()
    service = EstimateService(database)
    
    updated_estimate = service.accept_estimate(estimate_id)
    if not updated_estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    return {"message": "Estimate accepted successfully", "status": "accepted"}


@router.post("/{estimate_id}/reject")
async def reject_estimate(
    estimate_id: str, 
    reason: Optional[str] = None,
    db=Depends(get_db)
):
    """Reject an estimate"""
    from app.core.database_factory import get_database
    database = get_database()
    service = EstimateService(database)
    
    updated_estimate = service.reject_estimate(estimate_id, reason)
    if not updated_estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    
    return {"message": "Estimate rejected", "status": "rejected", "reason": reason}


@router.post("/{estimate_id}/convert-to-invoice")
async def convert_estimate_to_invoice(estimate_id: str, db=Depends(get_db)):
    """Convert estimate to invoice"""
    from app.core.database_factory import get_database
    database = get_database()
    service = EstimateService(database)
    
    try:
        invoice = service.convert_to_invoice(estimate_id)
        return {
            "message": "Estimate converted to invoice successfully",
            "invoice_id": invoice.get('id'),
            "invoice_number": invoice.get('invoice_number')
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{estimate_id}/duplicate", response_model=EstimateResponse)
async def duplicate_estimate(estimate_id: str, db=Depends(get_db)):
    """Duplicate an existing estimate"""
    from app.core.database_factory import get_database
    database = get_database()
    service = EstimateService(database)
    
    # Duplicate estimate
    duplicated = service.duplicate(estimate_id)
    if not duplicated:
        raise HTTPException(status_code=404, detail="Estimate not found or failed to duplicate")
    
    # Parse room_data if it's a string
    if duplicated.get('room_data') and isinstance(duplicated['room_data'], str):
        try:
            duplicated['room_data'] = json.loads(duplicated['room_data'])
        except json.JSONDecodeError:
            pass
    
    # Convert to response format
    return EstimateResponse(
        id=duplicated['id'],
        estimate_number=duplicated.get('estimate_number', ''),
        company_id=duplicated.get('company_id'),
        client_name=duplicated.get('client_name', ''),
        client_address=duplicated.get('client_address'),
        client_phone=duplicated.get('client_phone'),
        client_email=duplicated.get('client_email'),
        estimate_date=duplicated.get('estimate_date'),
        valid_until=duplicated.get('valid_until'),
        status=duplicated.get('status', 'draft'),
        subtotal=duplicated.get('subtotal', 0),
        tax_rate=duplicated.get('tax_rate', 0),
        tax_amount=duplicated.get('tax_amount', 0),
        discount_amount=duplicated.get('discount_amount', 0),
        total_amount=duplicated.get('total_amount', 0),
        claim_number=duplicated.get('claim_number'),
        policy_number=duplicated.get('policy_number'),
        deductible=duplicated.get('deductible'),
        depreciation_amount=duplicated.get('depreciation_amount', 0),
        acv_amount=duplicated.get('acv_amount', 0),
        rcv_amount=duplicated.get('rcv_amount', 0),
        notes=duplicated.get('notes'),
        terms=duplicated.get('terms'),
        room_data=duplicated.get('room_data'),
        created_at=duplicated.get('created_at'),
        updated_at=duplicated.get('updated_at'),
        items=[
            EstimateItemResponse(
                id=item.get('id'),
                estimate_id=item.get('estimate_id'),
                room=item.get('room'),
                description=item.get('description', ''),
                quantity=item.get('quantity', 0),
                unit=item.get('unit', ''),
                rate=item.get('rate', 0),
                amount=item.get('amount', 0),
                tax_rate=item.get('tax_rate', 0),
                tax_amount=item.get('tax_amount', 0),
                category=item.get('category'),
                depreciation_rate=item.get('depreciation_rate', 0),
                depreciation_amount=item.get('depreciation_amount', 0),
                acv_amount=item.get('acv_amount', 0),
                rcv_amount=item.get('rcv_amount', 0),
                order_index=item.get('order_index'),
                created_at=item.get('created_at'),
                updated_at=item.get('updated_at')
            )
            for item in duplicated.get('items', [])
        ]
    )


@router.post("/preview-pdf")
async def preview_estimate_pdf(data: EstimatePDFRequest):
    """Generate a preview PDF from estimate data without saving"""
    import logging
    import traceback
    logger = logging.getLogger(__name__)
    
    if not pdf_service:
        raise HTTPException(status_code=500, detail="PDF service not available")
    
    # Create temporary file for PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        output_path = tmp_file.name
    
    try:
        # Prepare data for PDF generation
        pdf_data = data.dict()
        logger.info(f"Generating PDF preview with data keys: {pdf_data.keys()}")
        
        # Determine document type based on insurance fields
        if pdf_data.get('claim_number') or pdf_data.get('policy_number'):
            # Generate insurance estimate PDF
            pdf_path = pdf_service.generate_insurance_estimate_pdf(pdf_data, output_path)
        else:
            # Generate regular estimate PDF
            pdf_path = pdf_service.generate_estimate_pdf(pdf_data, output_path)
        
        # Read PDF file
        with open(pdf_path, "rb") as pdf_file:
            pdf_content = pdf_file.read()
        
        # Clean up temp file
        os.unlink(pdf_path)
        
        # Return PDF as response
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=preview_estimate.pdf"
            }
        )
    except Exception as e:
        # Clean up on error
        logger.error(f"PDF generation error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        if os.path.exists(output_path):
            os.unlink(output_path)
        raise HTTPException(status_code=500, detail=str(e))