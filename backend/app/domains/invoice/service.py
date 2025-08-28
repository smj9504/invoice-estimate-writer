"""
Invoice domain service with comprehensive business logic and validation.
"""

from typing import Any, Dict, List, Optional
import logging
from datetime import datetime, date
from decimal import Decimal

from app.common.base_service import TransactionalService
from app.domains.invoice.repository import get_invoice_repository
from app.core.interfaces import DatabaseProvider
from app.core.database_factory import get_database

logger = logging.getLogger(__name__)


class InvoiceService(TransactionalService[Dict[str, Any], str]):
    """
    Service for invoice-related business operations.
    Provides comprehensive CRUD operations with validation and business logic.
    """
    
    def __init__(self, database: DatabaseProvider = None):
        super().__init__(database)
    
    def get_repository(self):
        """Get the invoice repository"""
        pass
    
    def _get_repository_instance(self, session):
        """Get invoice repository instance with the given session"""
        return get_invoice_repository(session)
    
    def get_by_invoice_number(self, invoice_number: str) -> Optional[Dict[str, Any]]:
        """
        Get invoice by invoice number.
        
        Args:
            invoice_number: Invoice number
            
        Returns:
            Invoice dictionary or None if not found
        """
        try:
            with self.database.get_session() as session:
                repository = self._get_repository_instance(session)
                return repository.get_by_invoice_number(invoice_number)
        except Exception as e:
            logger.error(f"Error getting invoice by number: {e}")
            raise
    
    def get_invoices_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Get invoices by status.
        
        Args:
            status: Invoice status
            
        Returns:
            List of invoice dictionaries
        """
        try:
            with self.database.get_session() as session:
                repository = self._get_repository_instance(session)
                return repository.get_invoices_by_status(status)
        except Exception as e:
            logger.error(f"Error getting invoices by status: {e}")
            raise
    
    def get_invoices_by_company(self, company_id: str) -> List[Dict[str, Any]]:
        """
        Get invoices for a specific company.
        
        Args:
            company_id: Company ID
            
        Returns:
            List of invoice dictionaries
        """
        try:
            with self.database.get_session() as session:
                repository = self._get_repository_instance(session)
                return repository.get_invoices_by_company(company_id)
        except Exception as e:
            logger.error(f"Error getting invoices by company: {e}")
            raise
    
    def get_invoices_by_date_range(self, 
                                   start_date: date, 
                                   end_date: date) -> List[Dict[str, Any]]:
        """
        Get invoices within a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of invoice dictionaries
        """
        try:
            with self.database.get_session() as session:
                repository = self._get_repository_instance(session)
                return repository.get_invoices_by_date_range(start_date, end_date)
        except Exception as e:
            logger.error(f"Error getting invoices by date range: {e}")
            raise
    
    def get_overdue_invoices(self) -> List[Dict[str, Any]]:
        """
        Get overdue invoices.
        
        Returns:
            List of overdue invoice dictionaries
        """
        try:
            with self.database.get_session() as session:
                repository = self._get_repository_instance(session)
                return repository.get_overdue_invoices()
        except Exception as e:
            logger.error(f"Error getting overdue invoices: {e}")
            raise
    
    def get_with_items(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """
        Get invoice with its items.
        
        Args:
            invoice_id: Invoice ID
            
        Returns:
            Invoice dictionary with items or None if not found
        """
        try:
            with self.database.get_session() as session:
                repository = self._get_repository_instance(session)
                return repository.get_with_items(invoice_id)
        except Exception as e:
            logger.error(f"Error getting invoice with items: {e}")
            raise
    
    def create_with_items(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create invoice with items in a single transaction.
        
        Args:
            invoice_data: Invoice data including items
            
        Returns:
            Created invoice dictionary with items
        """
        def _create_operation(session_or_uow, data):
            repository = self._get_repository_instance(session_or_uow)
            return repository.create_with_items(data)
        
        # Validate data
        validated_data = self._validate_create_data(invoice_data)
        
        # Generate invoice number if not provided
        if not validated_data.get('invoice_number'):
            validated_data['invoice_number'] = self._generate_invoice_number()
        
        return self.execute_in_transaction(_create_operation, validated_data)
    
    def update_with_items(self, invoice_id: str, invoice_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update invoice with items.
        
        Args:
            invoice_id: Invoice ID
            invoice_data: Updated invoice data including items
            
        Returns:
            Updated invoice dictionary with items
        """
        def _update_operation(session, invoice_id, data):
            repository = self._get_repository_instance(session)
            
            # Use the repository's update_with_items method
            return repository.update_with_items(invoice_id, data)
        
        validated_data = self._validate_update_data(invoice_data)
        
        return self.execute_in_transaction(_update_operation, invoice_id, validated_data)
    
    def mark_as_paid(self, invoice_id: str, payment_date: datetime = None) -> Optional[Dict[str, Any]]:
        """
        Mark invoice as paid.
        
        Args:
            invoice_id: Invoice ID
            payment_date: Payment date (defaults to now)
            
        Returns:
            Updated invoice dictionary
        """
        payment_date = payment_date or datetime.utcnow()
        
        return self.update(invoice_id, {
            'status': 'paid',
            'payment_date': payment_date
        })
    
    def mark_as_overdue(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """
        Mark invoice as overdue.
        
        Args:
            invoice_id: Invoice ID
            
        Returns:
            Updated invoice dictionary
        """
        return self.update(invoice_id, {'status': 'overdue'})
    
    def calculate_totals(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate invoice totals based on items.
        
        Args:
            items: List of invoice items
            
        Returns:
            Dictionary with calculated totals
        """
        try:
            subtotal = Decimal('0')
            total_tax = Decimal('0')
            
            for item in items:
                quantity = Decimal(str(item.get('quantity', 1)))
                rate = Decimal(str(item.get('rate', 0)))
                tax_rate = Decimal(str(item.get('tax_rate', 0)))
                
                item_amount = quantity * rate
                item_tax = item_amount * (tax_rate / 100)
                
                subtotal += item_amount
                total_tax += item_tax
            
            return {
                'subtotal': float(subtotal),
                'tax_amount': float(total_tax),
                'total_amount': float(subtotal + total_tax)
            }
            
        except Exception as e:
            logger.error(f"Error calculating invoice totals: {e}")
            raise
    
    def get_invoice_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive invoice summary statistics.
        
        Returns:
            Dictionary with invoice statistics
        """
        try:
            all_invoices = self.get_all()
            
            # Group by status
            status_counts = {}
            status_amounts = {}
            
            for invoice in all_invoices:
                status = invoice.get('status', 'unknown')
                amount = float(invoice.get('total_amount', 0))
                
                status_counts[status] = status_counts.get(status, 0) + 1
                status_amounts[status] = status_amounts.get(status, 0) + amount
            
            # Calculate overdue
            overdue_invoices = self.get_overdue_invoices()
            overdue_amount = sum(float(inv.get('total_amount', 0)) for inv in overdue_invoices)
            
            # Calculate totals
            total_amount = sum(float(inv.get('total_amount', 0)) for inv in all_invoices)
            paid_amount = status_amounts.get('paid', 0)
            outstanding_amount = total_amount - paid_amount
            
            return {
                'total_invoices': len(all_invoices),
                'total_amount': total_amount,
                'paid_amount': paid_amount,
                'outstanding_amount': outstanding_amount,
                'overdue_count': len(overdue_invoices),
                'overdue_amount': overdue_amount,
                'status_counts': status_counts,
                'status_amounts': status_amounts,
                'average_invoice_amount': total_amount / len(all_invoices) if all_invoices else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting invoice summary: {e}")
            raise
    
    def _generate_invoice_number(self) -> str:
        """Generate unique invoice number"""
        try:
            # Get current year and month
            now = datetime.utcnow()
            prefix = f"INV-{now.year}{now.month:02d}"
            
            # Get existing invoices for this month
            existing_invoices = self.get_all(
                filters={'invoice_number__startswith': prefix}
            )
            
            # Find the next sequence number
            sequence = len(existing_invoices) + 1
            
            return f"{prefix}-{sequence:04d}"
            
        except Exception as e:
            logger.error(f"Error generating invoice number: {e}")
            # Fallback to timestamp-based number
            timestamp = int(datetime.utcnow().timestamp())
            return f"INV-{timestamp}"
    
    def _validate_create_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for invoice creation"""
        if not data.get('client_name'):
            raise ValueError("Client name is required")
        
        validated_data = data.copy()
        
        # Remove None values
        validated_data = {k: v for k, v in validated_data.items() if v is not None}
        
        # Validate items
        items = validated_data.get('items', [])
        if not items:
            raise ValueError("At least one invoice item is required")
        
        for item in items:
            if not item.get('description'):
                raise ValueError("Item description is required")
            if float(item.get('rate', 0)) < 0:
                raise ValueError("Item rate cannot be negative")
            if float(item.get('quantity', 0)) <= 0:
                raise ValueError("Item quantity must be positive")
        
        # Calculate totals
        totals = self.calculate_totals(items)
        validated_data.update(totals)
        
        return validated_data
    
    def _validate_update_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for invoice update"""
        validated_data = data.copy()
        
        # Remove None values
        validated_data = {k: v for k, v in validated_data.items() if v is not None}
        
        # Remove system fields and ID
        for field in ['created_at', 'updated_at', 'id']:
            validated_data.pop(field, None)
        
        if not validated_data:
            raise ValueError("No valid data provided for update")
        
        # Validate items if provided
        items = validated_data.get('items')
        if items is not None:
            if not items:
                raise ValueError("At least one invoice item is required")
            
            for item in items:
                if not item.get('description'):
                    raise ValueError("Item description is required")
                if float(item.get('rate', 0)) < 0:
                    raise ValueError("Item rate cannot be negative")
                if float(item.get('quantity', 0)) <= 0:
                    raise ValueError("Item quantity must be positive")
            
            # Calculate totals
            totals = self.calculate_totals(items)
            validated_data.update(totals)
        
        return validated_data