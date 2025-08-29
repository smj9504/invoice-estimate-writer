"""
Dashboard service layer
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
import calendar

from app.domains.work_order.models import WorkOrder, WorkOrderStatus, DocumentType
from app.domains.company.models import Company
from app.domains.payment.models import Payment, PaymentStatus
from app.domains.credit.models import CustomerCredit, CreditTransaction
from app.domains.document_types.models import DocumentType as DocType

from .schemas import (
    WorkOrderMetrics,
    RevenueByPeriod,
    CompanyStats,
    CreditUsageStats,
    DashboardOverview,
    WorkOrderStatusCount,
    PeriodFilter
)


class DashboardService:
    """Dashboard business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_work_order_metrics(
        self, 
        company_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> WorkOrderMetrics:
        """Get key work order metrics"""
        
        # Base query
        query = self.db.query(WorkOrder).filter(WorkOrder.is_active == True)
        
        # Apply filters
        if company_id:
            query = query.filter(WorkOrder.company_id == company_id)
        if start_date:
            query = query.filter(WorkOrder.created_at >= start_date)
        if end_date:
            query = query.filter(WorkOrder.created_at <= end_date)
        
        # Get counts by status
        total_leads = query.filter(WorkOrder.status == WorkOrderStatus.PENDING).count()
        revision_requests = query.filter(WorkOrder.revision_requested == True).count()
        completed_orders = query.filter(WorkOrder.status == WorkOrderStatus.COMPLETED).count()
        active_orders = query.filter(WorkOrder.status == WorkOrderStatus.IN_PROGRESS).count()
        
        # Get pending payments amount
        pending_payments_query = self.db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
            Payment.status == PaymentStatus.PENDING
        )
        if company_id:
            pending_payments_query = pending_payments_query.join(WorkOrder).filter(
                WorkOrder.company_id == company_id
            )
        
        pending_payments = Decimal(str(pending_payments_query.scalar() or 0))
        
        return WorkOrderMetrics(
            total_leads=total_leads,
            revision_requests=revision_requests,
            completed_orders=completed_orders,
            pending_payments=pending_payments,
            active_orders=active_orders
        )
    
    def get_revenue_by_period(
        self,
        period_type: str,  # 'week', 'month', 'quarter', 'year'
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        company_id: Optional[str] = None
    ) -> List[RevenueByPeriod]:
        """Calculate revenue statistics by period"""
        
        if not start_date or not end_date:
            # Default to current year
            now = datetime.now()
            if period_type == 'year':
                start_date = datetime(now.year, 1, 1)
                end_date = datetime(now.year, 12, 31)
            elif period_type == 'quarter':
                quarter = (now.month - 1) // 3 + 1
                start_date = datetime(now.year, (quarter - 1) * 3 + 1, 1)
                end_date = datetime(now.year, quarter * 3, 
                                 calendar.monthrange(now.year, quarter * 3)[1])
            elif period_type == 'month':
                start_date = datetime(now.year, now.month, 1)
                end_date = datetime(now.year, now.month, 
                                 calendar.monthrange(now.year, now.month)[1])
            else:  # week
                days_since_monday = now.weekday()
                start_date = now - timedelta(days=days_since_monday)
                end_date = start_date + timedelta(days=6)
        
        # Query completed work orders with their document types and pricing
        query = self.db.query(
            WorkOrder,
            func.coalesce(DocType.base_price, 0).label('base_price')
        ).outerjoin(
            DocType, WorkOrder.document_type == DocType.name
        ).filter(
            and_(
                WorkOrder.status == WorkOrderStatus.COMPLETED,
                WorkOrder.actual_end_date >= start_date,
                WorkOrder.actual_end_date <= end_date,
                WorkOrder.is_active == True
            )
        )
        
        if company_id:
            query = query.filter(WorkOrder.company_id == company_id)
        
        work_orders = query.all()
        
        # Calculate revenue
        total_revenue = Decimal('0')
        document_counts = {}
        
        for work_order, base_price in work_orders:
            # Use actual_cost if available, otherwise use base_price
            order_revenue = Decimal('0')
            if work_order.actual_cost:
                try:
                    order_revenue = Decimal(str(work_order.actual_cost))
                except:
                    order_revenue = Decimal(str(base_price or 0))
            else:
                order_revenue = Decimal(str(base_price or 0))
            
            total_revenue += order_revenue
            
            # Count document types
            doc_type = work_order.document_type.value if work_order.document_type else 'unknown'
            document_counts[doc_type] = document_counts.get(doc_type, 0) + 1
        
        # Calculate credit used in this period
        credit_used_query = self.db.query(
            func.coalesce(func.sum(CreditTransaction.amount), 0)
        ).filter(
            and_(
                CreditTransaction.transaction_type == 'use',
                CreditTransaction.created_at >= start_date,
                CreditTransaction.created_at <= end_date
            )
        )
        
        if company_id:
            credit_used_query = credit_used_query.join(CustomerCredit).filter(
                CustomerCredit.company_id == company_id
            )
        
        credit_used = Decimal(str(credit_used_query.scalar() or 0))
        net_revenue = total_revenue - credit_used
        
        return [RevenueByPeriod(
            period=period_type,
            start_date=start_date,
            end_date=end_date,
            total_revenue=total_revenue,
            document_counts=document_counts,
            credit_used=credit_used,
            net_revenue=net_revenue
        )]
    
    def get_company_stats(self, limit: int = 10) -> List[CompanyStats]:
        """Get top companies by revenue"""
        
        # Query companies with their work order counts and revenue
        company_stats = self.db.query(
            Company,
            func.count(WorkOrder.id).label('total_orders'),
            func.count(
                func.nullif(WorkOrder.status != WorkOrderStatus.COMPLETED, True)
            ).label('completed_orders'),
            func.max(WorkOrder.created_at).label('last_order_date')
        ).outerjoin(
            WorkOrder, Company.id == WorkOrder.company_id
        ).group_by(
            Company.id
        ).order_by(
            func.count(WorkOrder.id).desc()
        ).limit(limit).all()
        
        result = []
        for company, total_orders, completed_orders, last_order_date in company_stats:
            # Calculate total revenue for this company
            revenue_query = self.db.query(
                func.coalesce(func.sum(
                    func.coalesce(
                        func.cast(WorkOrder.actual_cost, func.numeric(10,2)), 
                        DocType.base_price, 
                        0
                    )
                ), 0)
            ).outerjoin(
                DocType, WorkOrder.document_type == DocType.name
            ).filter(
                and_(
                    WorkOrder.company_id == company.id,
                    WorkOrder.status == WorkOrderStatus.COMPLETED
                )
            )
            
            total_revenue = Decimal(str(revenue_query.scalar() or 0))
            
            # Get credit balance
            credit_balance_query = self.db.query(
                func.coalesce(func.sum(CustomerCredit.remaining_amount), 0)
            ).filter(CustomerCredit.company_id == company.id)
            
            credit_balance = Decimal(str(credit_balance_query.scalar() or 0))
            
            result.append(CompanyStats(
                company_id=str(company.id),
                company_name=company.name,
                total_orders=total_orders or 0,
                completed_orders=completed_orders or 0,
                total_revenue=total_revenue,
                credit_balance=credit_balance,
                last_order_date=last_order_date
            ))
        
        return result
    
    def get_credit_usage_stats(self) -> CreditUsageStats:
        """Get credit system usage statistics"""
        
        # Total credits allocated
        total_allocated = self.db.query(
            func.coalesce(func.sum(CustomerCredit.original_amount), 0)
        ).scalar()
        
        # Total credits used
        total_used = self.db.query(
            func.coalesce(func.sum(CustomerCredit.used_amount), 0)
        ).scalar()
        
        # Total remaining
        total_remaining = self.db.query(
            func.coalesce(func.sum(CustomerCredit.remaining_amount), 0)
        ).scalar()
        
        # Credits by company
        credits_by_company = self.db.query(
            Company.name,
            Company.id,
            func.coalesce(func.sum(CustomerCredit.remaining_amount), 0).label('balance')
        ).outerjoin(
            CustomerCredit, Company.id == CustomerCredit.company_id
        ).group_by(
            Company.id, Company.name
        ).order_by(
            func.coalesce(func.sum(CustomerCredit.remaining_amount), 0).desc()
        ).limit(10).all()
        
        # Recent transactions
        recent_transactions = self.db.query(CreditTransaction).order_by(
            CreditTransaction.created_at.desc()
        ).limit(20).all()
        
        return CreditUsageStats(
            total_credits_allocated=Decimal(str(total_allocated or 0)),
            total_credits_used=Decimal(str(total_used or 0)),
            total_credits_remaining=Decimal(str(total_remaining or 0)),
            credits_by_company=[
                {
                    'company_name': name,
                    'company_id': str(company_id),
                    'balance': float(balance)
                }
                for name, company_id, balance in credits_by_company
            ],
            recent_transactions=[
                {
                    'id': str(tx.id),
                    'type': tx.transaction_type,
                    'amount': float(tx.amount),
                    'date': tx.created_at,
                    'company_id': str(tx.customer_credit.company_id) if tx.customer_credit else None
                }
                for tx in recent_transactions
            ]
        )
    
    def get_dashboard_overview(
        self,
        company_id: Optional[str] = None
    ) -> DashboardOverview:
        """Get complete dashboard overview"""
        
        # Current metrics
        work_order_metrics = self.get_work_order_metrics(company_id=company_id)
        
        # Current month revenue
        now = datetime.now()
        current_month_start = datetime(now.year, now.month, 1)
        current_month_end = datetime(now.year, now.month, 
                                   calendar.monthrange(now.year, now.month)[1])
        
        current_revenue = self.get_revenue_by_period(
            'month', current_month_start, current_month_end, company_id
        )[0].net_revenue
        
        # Previous month revenue
        if now.month == 1:
            prev_month = 12
            prev_year = now.year - 1
        else:
            prev_month = now.month - 1
            prev_year = now.year
        
        prev_month_start = datetime(prev_year, prev_month, 1)
        prev_month_end = datetime(prev_year, prev_month, 
                                calendar.monthrange(prev_year, prev_month)[1])
        
        prev_revenue = self.get_revenue_by_period(
            'month', prev_month_start, prev_month_end, company_id
        )[0].net_revenue
        
        # Growth percentage
        growth_percentage = 0.0
        if prev_revenue > 0:
            growth_percentage = float((current_revenue - prev_revenue) / prev_revenue * 100)
        
        # Top companies
        top_companies = self.get_company_stats(limit=5)
        
        # Recent activities (recent work orders)
        recent_activities_query = self.db.query(WorkOrder).order_by(
            WorkOrder.updated_at.desc()
        ).limit(10)
        
        if company_id:
            recent_activities_query = recent_activities_query.filter(
                WorkOrder.company_id == company_id
            )
        
        recent_work_orders = recent_activities_query.all()
        recent_activities = [
            {
                'id': str(wo.id),
                'type': 'work_order',
                'description': f"Work Order #{wo.work_order_number} - {wo.client_name}",
                'status': wo.status.value,
                'date': wo.updated_at,
                'company_name': wo.company_id  # This would need a join for actual name
            }
            for wo in recent_work_orders
        ]
        
        return DashboardOverview(
            work_order_metrics=work_order_metrics,
            revenue_current_month=current_revenue,
            revenue_previous_month=prev_revenue,
            revenue_growth_percentage=growth_percentage,
            top_companies=top_companies,
            recent_activities=recent_activities
        )