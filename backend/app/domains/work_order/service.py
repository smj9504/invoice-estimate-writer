"""
Work Order service for business logic
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
from uuid import UUID

from app.common.base_service import BaseService
from .repository import get_work_order_repository
from .models import WorkOrder, WorkOrderStatus
from .schemas import WorkOrderCreate, WorkOrderUpdate, WorkOrderFilter

logger = logging.getLogger(__name__)


class WorkOrderService(BaseService[WorkOrder, UUID]):
    """
    Service for managing work orders with business logic
    """
    
    def get_repository(self):
        """Get the work order repository"""
        return get_work_order_repository
    
    def _get_repository_instance(self, session):
        """Get repository instance with the given session"""
        return get_work_order_repository(session)
    
    def generate_work_order_number(self, company_id) -> str:
        """
        Generate unique work order number with company code
        Format: WO-[COMPANY_CODE]-YY-NNNN
        
        Args:
            company_id: Company UUID
            
        Returns:
            Generated work order number
        """
        try:
            session = self.database.get_session()
            try:
                # Get company code
                from app.domains.company.repository import CompanyRepository
                company_repo = CompanyRepository(session)
                
                # Convert company_id to string if it's a UUID object
                company_id_str = str(company_id) if hasattr(company_id, 'hex') else company_id
                
                # Debug logging
                logger.info(f"Generating work order number for company_id: {company_id_str} (type: {type(company_id)})")
                
                company = company_repo.get_by_id(company_id_str)
                logger.info(f"Company data retrieved: {company}")
                
                company_code = "XX"  # Default if no company code
                if company and company.get('company_code'):
                    company_code = company['company_code'].upper()
                    logger.info(f"Using company_code from database: {company_code}")
                elif company and company.get('name'):
                    # If no company_code, try to generate from company name
                    # Take first 2-3 characters of company name
                    name_parts = company['name'].strip().upper().split()
                    if len(name_parts) == 1:
                        # Single word company name - take first 3 chars
                        company_code = name_parts[0][:3] if len(name_parts[0]) >= 3 else name_parts[0]
                    else:
                        # Multiple words - take first letter of each word (up to 3)
                        company_code = ''.join([part[0] for part in name_parts[:3]])
                    logger.info(f"Generated company_code from name: {company_code}")
                else:
                    logger.warning(f"No company found or no company_code/name available for company_id: {company_id}")
                
                # Get current year
                current_year = datetime.now().year
                year_suffix = str(current_year)[2:]  # Last 2 digits
                
                # Find the highest existing number for this company and year
                repository = self._get_repository_instance(session)
                # Get work orders for this company to find the latest number
                all_wos = repository.get_by_company(company_id_str)
                
                next_number = 1
                if all_wos:
                    # Filter work orders for current year and extract highest number
                    for wo in all_wos:
                        wo_num = wo.get('work_order_number', '')
                        # Parse format: WO-COMPANY_CODE-YY-NNNN
                        parts = wo_num.split('-')
                        if len(parts) >= 4:
                            try:
                                # Check if it's from the current year and same company code
                                if parts[1] == company_code and parts[2] == year_suffix:
                                    num = int(parts[3])
                                    next_number = max(next_number, num + 1)
                            except (ValueError, IndexError):
                                pass
                
                # Format: WO-COMPANY_CODE-YY-NNNN
                work_order_number = f"WO-{company_code}-{year_suffix}-{next_number:04d}"
                logger.info(f"Generated work order number: {work_order_number}")
                
                # Ensure uniqueness
                counter = 0
                base_number = work_order_number
                while self.work_order_number_exists(work_order_number):
                    counter += 1
                    work_order_number = f"{base_number}-{counter}"
                    logger.info(f"Work order number already exists, trying: {work_order_number}")
                
                logger.info(f"Final work order number: {work_order_number}")
                return work_order_number
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error generating work order number: {e}")
            # Fallback to UUID-based number
            import uuid
            year_suffix = str(datetime.now().year)[2:]
            return f"WO-XX-{year_suffix}-{str(uuid.uuid4())[:8].upper()}"
    
    def work_order_number_exists(self, work_order_number: str) -> bool:
        """
        Check if work order number already exists
        
        Args:
            work_order_number: Work order number to check
            
        Returns:
            True if exists, False otherwise
        """
        try:
            session = self.database.get_session()
            try:
                repository = self._get_repository_instance(session)
                return repository.work_order_number_exists(work_order_number)
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Error checking work order number existence: {e}")
            return False
    
    def create_work_order(self, work_order_data: WorkOrderCreate) -> Dict[str, Any]:
        """
        Create a new work order with auto-generated work order number
        
        Args:
            work_order_data: Work order creation data
            
        Returns:
            Created work order dictionary
        """
        try:
            # Convert Pydantic model to dict
            data = work_order_data.dict()
            
            # Generate work order number if not provided
            if not data.get('work_order_number'):
                data['work_order_number'] = self.generate_work_order_number(data['company_id'])
            
            # created_by_staff_id should be provided by the API endpoint
            # No default staff ID to avoid foreign key constraint errors
            
            # Set initial status
            data['status'] = WorkOrderStatus.DRAFT
            
            # Create the work order
            return self.create(data)
            
        except Exception as e:
            logger.error(f"Error creating work order: {e}")
            raise
    
    def update_work_order_status(self, work_order_id: UUID, status: WorkOrderStatus, 
                                staff_id: UUID, notes: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Update work order status with timestamp tracking
        
        Args:
            work_order_id: Work order ID
            status: New status
            staff_id: Staff member making the change
            notes: Optional notes about the status change
            
        Returns:
            Updated work order or None if not found
        """
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.utcnow()
            }
            
            # Add timestamp based on status
            if status == WorkOrderStatus.IN_PROGRESS and not self.get_by_id(work_order_id).get('actual_start_date'):
                update_data['actual_start_date'] = datetime.utcnow()
            elif status == WorkOrderStatus.COMPLETED:
                update_data['actual_end_date'] = datetime.utcnow()
                if notes:
                    update_data['completion_notes'] = notes
            
            return self.update(work_order_id, update_data)
            
        except Exception as e:
            logger.error(f"Error updating work order status: {e}")
            raise
    
    def get_work_orders_with_filters(self, filters: WorkOrderFilter) -> Dict[str, Any]:
        """
        Get work orders with advanced filtering
        
        Args:
            filters: Filter parameters
            
        Returns:
            Dictionary with work orders and metadata
        """
        try:
            session = self.database.get_session()
            try:
                repository = self._get_repository_instance(session)
                
                # Convert Pydantic filter to dict, excluding None values
                filter_dict = filters.dict(exclude_none=True)
                
                # Use get_all with filters
                work_orders = repository.get_all(filters=filter_dict)
                
                return {
                    'work_orders': work_orders,
                    'total': len(work_orders),
                    'filters_applied': filter_dict
                }
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error getting work orders with filters: {e}")
            raise
    
    def get_work_orders_by_company(self, company_id: UUID, 
                                  status: Optional[WorkOrderStatus] = None) -> List[Dict[str, Any]]:
        """
        Get all work orders for a specific company
        
        Args:
            company_id: Company UUID
            status: Optional status filter
            
        Returns:
            List of work order dictionaries
        """
        try:
            filters = {'company_id': company_id}
            if status:
                filters['status'] = status
            
            return self.get_all(filters=filters, order_by='-created_at')
            
        except Exception as e:
            logger.error(f"Error getting work orders by company: {e}")
            raise
    
    def get_work_orders_by_staff(self, staff_id: UUID, 
                                assigned_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get work orders associated with a staff member
        
        Args:
            staff_id: Staff member UUID
            assigned_only: If True, only return assigned work orders
            
        Returns:
            List of work order dictionaries
        """
        try:
            if assigned_only:
                filters = {'assigned_to_staff_id': staff_id}
            else:
                # Get work orders created by or assigned to the staff member
                session = self.database.get_session()
                try:
                    repository = self._get_repository_instance(session)
                    return repository.get_work_orders_by_staff(staff_id)
                finally:
                    session.close()
            
            return self.get_all(filters=filters, order_by='-created_at')
            
        except Exception as e:
            logger.error(f"Error getting work orders by staff: {e}")
            raise
    
    def search_work_orders(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search work orders by work order number or address fields
        
        Args:
            search_term: Search term to match against work order number and address fields
            
        Returns:
            List of matching work order dictionaries
        """
        try:
            session = self.database.get_session()
            try:
                repository = self._get_repository_instance(session)
                return repository.search_orders(search_term)
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error searching work orders: {e}")
            raise
    
    def get_dashboard_stats(self, company_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Get dashboard statistics for work orders
        
        Args:
            company_id: Optional company filter
            
        Returns:
            Dictionary with various statistics
        """
        try:
            session = self.database.get_session()
            try:
                repository = self._get_repository_instance(session)
                return repository.get_dashboard_stats(company_id)
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            raise
    
    def _validate_create_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate work order creation data"""
        # Ensure required fields
        if not data.get('client_name'):
            raise ValueError("Client name is required")
        
        if not data.get('work_order_number'):
            data['work_order_number'] = self.generate_work_order_number(data['company_id'])
        
        return data
    
    def _validate_update_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate work order update data"""
        # Remove fields that shouldn't be updated directly
        protected_fields = ['id', 'created_at', 'created_by_staff_id']
        for field in protected_fields:
            data.pop(field, None)
        
        return data