"""
Work Order repository for data access layer
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import and_, or_, func, extract
from sqlalchemy.orm import Session
from datetime import datetime
import logging
from uuid import UUID

from .base import SQLAlchemyRepository
from ..work_order.models import WorkOrder, WorkOrderStatus
from ..core.interfaces import DatabaseSession

logger = logging.getLogger(__name__)


class WorkOrderRepository(SQLAlchemyRepository[WorkOrder, UUID]):
    """Repository for Work Order data access"""
    
    def __init__(self, session: DatabaseSession):
        super().__init__(session, WorkOrder)
    
    def get_latest_work_order_by_year(self, year: int) -> Optional[Dict[str, Any]]:
        """
        Get the latest work order for a specific year
        
        Args:
            year: Year to search for
            
        Returns:
            Latest work order dictionary or None
        """
        try:
            result = (
                self.db_session.query(WorkOrder)
                .filter(extract('year', WorkOrder.created_at) == year)
                .filter(WorkOrder.work_order_number.like(f"WO-{str(year)[2:]}-%"))
                .order_by(WorkOrder.created_at.desc())
                .first()
            )
            
            return self._convert_to_dict(result) if result else None
            
        except Exception as e:
            logger.error(f"Error getting latest work order by year: {e}")
            raise
    
    def work_order_number_exists(self, work_order_number: str) -> bool:
        """
        Check if work order number already exists
        
        Args:
            work_order_number: Work order number to check
            
        Returns:
            True if exists, False otherwise
        """
        try:
            result = (
                self.db_session.query(WorkOrder)
                .filter(WorkOrder.work_order_number == work_order_number)
                .first()
            )
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Error checking work order number existence: {e}")
            return False
    
    def get_with_filters(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get work orders with advanced filtering
        
        Args:
            filters: Dictionary of filters
            
        Returns:
            List of work order dictionaries
        """
        try:
            query = self.db_session.query(WorkOrder)
            
            # Apply filters
            if 'search' in filters:
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        WorkOrder.work_order_number.ilike(search_term),
                        WorkOrder.client_name.ilike(search_term),
                        WorkOrder.client_email.ilike(search_term),
                        WorkOrder.client_phone.ilike(search_term),
                        WorkOrder.work_description.ilike(search_term),
                        WorkOrder.job_site_address.ilike(search_term)
                    )
                )
            
            if 'status' in filters:
                query = query.filter(WorkOrder.status == filters['status'])
            
            if 'company_id' in filters:
                query = query.filter(WorkOrder.company_id == filters['company_id'])
            
            if 'assigned_to_staff_id' in filters:
                query = query.filter(WorkOrder.assigned_to_staff_id == filters['assigned_to_staff_id'])
            
            if 'created_by_staff_id' in filters:
                query = query.filter(WorkOrder.created_by_staff_id == filters['created_by_staff_id'])
            
            if 'document_type' in filters:
                query = query.filter(WorkOrder.document_type == filters['document_type'])
            
            if 'priority' in filters:
                query = query.filter(WorkOrder.priority == filters['priority'])
            
            if 'is_active' in filters:
                query = query.filter(WorkOrder.is_active == filters['is_active'])
            
            if 'date_from' in filters:
                query = query.filter(WorkOrder.created_at >= filters['date_from'])
            
            if 'date_to' in filters:
                query = query.filter(WorkOrder.created_at <= filters['date_to'])
            
            # Order by created_at descending by default
            query = query.order_by(WorkOrder.created_at.desc())
            
            results = query.all()
            return [self._convert_to_dict(result) for result in results]
            
        except Exception as e:
            logger.error(f"Error getting work orders with filters: {e}")
            raise
    
    def get_work_orders_by_staff(self, staff_id: UUID) -> List[Dict[str, Any]]:
        """
        Get work orders created by or assigned to a staff member
        
        Args:
            staff_id: Staff member UUID
            
        Returns:
            List of work order dictionaries
        """
        try:
            results = (
                self.db_session.query(WorkOrder)
                .filter(
                    or_(
                        WorkOrder.created_by_staff_id == staff_id,
                        WorkOrder.assigned_to_staff_id == staff_id
                    )
                )
                .order_by(WorkOrder.created_at.desc())
                .all()
            )
            
            return [self._convert_to_dict(result) for result in results]
            
        except Exception as e:
            logger.error(f"Error getting work orders by staff: {e}")
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
            base_query = self.db_session.query(WorkOrder)
            
            if company_id:
                base_query = base_query.filter(WorkOrder.company_id == company_id)
            
            # Total counts by status
            status_counts = {}
            for status in WorkOrderStatus:
                count = base_query.filter(WorkOrder.status == status).count()
                status_counts[status.value] = count
            
            # Total active work orders
            total_active = base_query.filter(WorkOrder.is_active == True).count()
            
            # This month's work orders
            current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            this_month = base_query.filter(WorkOrder.created_at >= current_month).count()
            
            # Overdue work orders (scheduled end date passed but not completed)
            overdue = base_query.filter(
                and_(
                    WorkOrder.scheduled_end_date < datetime.now(),
                    WorkOrder.status.notin_([WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED])
                )
            ).count()
            
            # Priority distribution
            priority_counts = {}
            for priority in ['low', 'medium', 'high', 'urgent']:
                count = base_query.filter(WorkOrder.priority == priority).count()
                priority_counts[priority] = count
            
            # Recent activity (last 7 days)
            seven_days_ago = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            from datetime import timedelta
            seven_days_ago = seven_days_ago - timedelta(days=7)
            recent_activity = base_query.filter(WorkOrder.updated_at >= seven_days_ago).count()
            
            return {
                'total_active': total_active,
                'status_counts': status_counts,
                'this_month': this_month,
                'overdue': overdue,
                'priority_counts': priority_counts,
                'recent_activity': recent_activity,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            raise
    
    def get_work_orders_by_date_range(self, start_date: datetime, 
                                     end_date: datetime,
                                     company_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """
        Get work orders within a date range
        
        Args:
            start_date: Start date
            end_date: End date
            company_id: Optional company filter
            
        Returns:
            List of work order dictionaries
        """
        try:
            query = self.db_session.query(WorkOrder).filter(
                and_(
                    WorkOrder.created_at >= start_date,
                    WorkOrder.created_at <= end_date
                )
            )
            
            if company_id:
                query = query.filter(WorkOrder.company_id == company_id)
            
            query = query.order_by(WorkOrder.created_at.desc())
            results = query.all()
            
            return [self._convert_to_dict(result) for result in results]
            
        except Exception as e:
            logger.error(f"Error getting work orders by date range: {e}")
            raise
    
    def get_work_orders_by_status(self, status: WorkOrderStatus,
                                 company_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """
        Get work orders by status
        
        Args:
            status: Work order status
            company_id: Optional company filter
            
        Returns:
            List of work order dictionaries
        """
        try:
            query = self.db_session.query(WorkOrder).filter(WorkOrder.status == status)
            
            if company_id:
                query = query.filter(WorkOrder.company_id == company_id)
            
            query = query.order_by(WorkOrder.created_at.desc())
            results = query.all()
            
            return [self._convert_to_dict(result) for result in results]
            
        except Exception as e:
            logger.error(f"Error getting work orders by status: {e}")
            raise
    
    def update_status_batch(self, work_order_ids: List[UUID], 
                           status: WorkOrderStatus) -> int:
        """
        Update status for multiple work orders
        
        Args:
            work_order_ids: List of work order IDs
            status: New status
            
        Returns:
            Number of updated records
        """
        try:
            updated = (
                self.db_session.query(WorkOrder)
                .filter(WorkOrder.id.in_(work_order_ids))
                .update(
                    {
                        'status': status,
                        'updated_at': datetime.utcnow()
                    },
                    synchronize_session=False
                )
            )
            
            return updated
            
        except Exception as e:
            logger.error(f"Error updating work order status batch: {e}")
            raise