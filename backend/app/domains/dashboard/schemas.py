"""
Dashboard API schemas
"""

from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime
from decimal import Decimal


class WorkOrderStatusCount(BaseModel):
    """Work order count by status"""
    status: str
    count: int
    percentage: float


class RevenueByPeriod(BaseModel):
    """Revenue statistics by time period"""
    period: str  # 'week', 'month', 'quarter', 'year'
    start_date: datetime
    end_date: datetime
    total_revenue: Decimal
    document_counts: Dict[str, int]  # document_type -> count
    credit_used: Decimal
    net_revenue: Decimal  # total_revenue - credit_used


class WorkOrderMetrics(BaseModel):
    """Work order key metrics"""
    total_leads: int  # PENDING status
    revision_requests: int  # revision_requested = True
    completed_orders: int  # COMPLETED status
    pending_payments: Decimal  # payments with PENDING status
    active_orders: int  # IN_PROGRESS status


class CompanyStats(BaseModel):
    """Company-specific statistics"""
    company_id: str
    company_name: str
    total_orders: int
    completed_orders: int
    total_revenue: Decimal
    credit_balance: Decimal
    last_order_date: Optional[datetime]


class CreditUsageStats(BaseModel):
    """Credit system usage statistics"""
    total_credits_allocated: Decimal
    total_credits_used: Decimal
    total_credits_remaining: Decimal
    credits_by_company: List[Dict[str, Any]]
    recent_transactions: List[Dict[str, Any]]


class DashboardOverview(BaseModel):
    """Complete dashboard overview"""
    work_order_metrics: WorkOrderMetrics
    revenue_current_month: Decimal
    revenue_previous_month: Decimal
    revenue_growth_percentage: float
    top_companies: List[CompanyStats]
    recent_activities: List[Dict[str, Any]]


class PeriodFilter(BaseModel):
    """Period filter for dashboard data"""
    period_type: str  # 'week', 'month', 'quarter', 'year'
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    company_id: Optional[str] = None


class DashboardFilters(BaseModel):
    """Dashboard filtering options"""
    period: PeriodFilter
    company_ids: Optional[List[str]] = None
    document_types: Optional[List[str]] = None
    show_completed: bool = True