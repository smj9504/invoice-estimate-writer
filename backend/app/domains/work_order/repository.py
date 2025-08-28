"""
Work Order domain repository
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID
import logging

from app.common.base_repository import SQLAlchemyRepository, SupabaseRepository
from app.core.interfaces import DatabaseSession
from .models import WorkOrder, WorkOrderStatus

logger = logging.getLogger(__name__)


class WorkOrderRepositoryMixin:
    """Mixin with work order-specific methods"""
    
    def get_by_status(self, status: WorkOrderStatus) -> List[Dict[str, Any]]:
        """Get work orders by status"""
        return self.get_all(filters={'status': status.value}, order_by='created_at')
    
    def get_by_customer_id(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get work orders for a specific customer"""
        return self.get_all(filters={'customer_id': customer_id}, order_by='created_at')
    
    def get_active_orders(self) -> List[Dict[str, Any]]:
        """Get all active work orders (not completed or cancelled)"""
        # For SQLAlchemy, this would need a custom query
        # For Supabase, we can use filters
        raise NotImplementedError("Subclasses must implement get_active_orders")
    
    def update_status(self, order_id: str, status: WorkOrderStatus) -> Optional[Dict[str, Any]]:
        """Update work order status"""
        return self.update(order_id, {'status': status.value, 'updated_at': datetime.utcnow()})
    
    def search_orders(self, search_term: str) -> List[Dict[str, Any]]:
        """Search work orders by various fields"""
        raise NotImplementedError("Subclasses must implement search_orders")


class WorkOrderSQLAlchemyRepository(SQLAlchemyRepository, WorkOrderRepositoryMixin):
    """SQLAlchemy-based work order repository for SQLite/PostgreSQL"""
    
    def __init__(self, session: DatabaseSession):
        super().__init__(session, WorkOrder)
    
    def get_active_orders(self) -> List[Dict[str, Any]]:
        """Get all active work orders"""
        try:
            entities = self.db_session.query(WorkOrder).filter(
                WorkOrder.status.in_([
                    WorkOrderStatus.PENDING.value,
                    WorkOrderStatus.IN_PROGRESS.value
                ])
            ).order_by(WorkOrder.created_at.desc()).all()
            
            return [self._convert_to_dict(entity) for entity in entities]
        except Exception as e:
            logger.error(f"Error getting active orders: {e}")
            return []
    
    def search_orders(self, search_term: str) -> List[Dict[str, Any]]:
        """Search work orders using SQL LIKE queries"""
        try:
            search_pattern = f"%{search_term.lower()}%"
            
            entities = self.db_session.query(WorkOrder).filter(
                (WorkOrder.order_number.ilike(search_pattern)) |
                (WorkOrder.title.ilike(search_pattern)) |
                (WorkOrder.description.ilike(search_pattern)) |
                (WorkOrder.customer_name.ilike(search_pattern))
            ).order_by(WorkOrder.created_at.desc()).all()
            
            return [self._convert_to_dict(entity) for entity in entities]
        except Exception as e:
            logger.error(f"Error searching work orders: {e}")
            return []


class WorkOrderSupabaseRepository(SupabaseRepository, WorkOrderRepositoryMixin):
    """Supabase-based work order repository"""
    
    def __init__(self, session: DatabaseSession):
        super().__init__(session, 'work_orders')
    
    def get_active_orders(self) -> List[Dict[str, Any]]:
        """Get all active work orders"""
        try:
            response = self.client.table(self.table_name)\
                .select("*")\
                .in_('status', [WorkOrderStatus.PENDING.value, WorkOrderStatus.IN_PROGRESS.value])\
                .order('created_at', desc=True)\
                .execute()
            
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error getting active orders: {e}")
            return []
    
    def search_orders(self, search_term: str) -> List[Dict[str, Any]]:
        """Search work orders in Supabase"""
        try:
            search_lower = search_term.lower()
            
            # Supabase doesn't support OR in the same way, so we need multiple queries
            # This is a simplified version - you might want to combine results
            response = self.client.table(self.table_name)\
                .select("*")\
                .or_(f"order_number.ilike.%{search_lower}%,title.ilike.%{search_lower}%,description.ilike.%{search_lower}%,customer_name.ilike.%{search_lower}%")\
                .order('created_at', desc=True)\
                .execute()
            
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error searching work orders: {e}")
            return []


def get_work_order_repository(session: DatabaseSession) -> WorkOrderRepositoryMixin:
    """
    Factory function to get the appropriate work order repository based on the session type.
    
    Args:
        session: Database session
        
    Returns:
        Appropriate repository implementation
    """
    from sqlalchemy.orm import Session
    
    if isinstance(session, Session):
        return WorkOrderSQLAlchemyRepository(session)
    else:
        # Assume it's a Supabase client
        return WorkOrderSupabaseRepository(session)