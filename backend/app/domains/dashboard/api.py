"""
Dashboard API endpoints
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database_factory import get_database
from .service import DashboardService
from .schemas import (
    DashboardOverview,
    WorkOrderMetrics,
    RevenueByPeriod,
    CompanyStats,
    CreditUsageStats,
    PeriodFilter
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverview)
async def get_dashboard_overview(
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    db: Session = Depends(get_database)
):
    """Get complete dashboard overview with key metrics"""
    try:
        service = DashboardService(db)
        return service.get_dashboard_overview(company_id=company_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard overview: {str(e)}")


@router.get("/metrics", response_model=WorkOrderMetrics)
async def get_work_order_metrics(
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    db: Session = Depends(get_database)
):
    """Get work order key metrics"""
    try:
        service = DashboardService(db)
        return service.get_work_order_metrics(
            company_id=company_id,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch work order metrics: {str(e)}")


@router.get("/revenue", response_model=List[RevenueByPeriod])
async def get_revenue_stats(
    period_type: str = Query("month", description="Period type: week, month, quarter, year"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    db: Session = Depends(get_database)
):
    """Get revenue statistics by time period"""
    
    valid_periods = ['week', 'month', 'quarter', 'year']
    if period_type not in valid_periods:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid period_type. Must be one of: {', '.join(valid_periods)}"
        )
    
    try:
        service = DashboardService(db)
        return service.get_revenue_by_period(
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
            company_id=company_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch revenue stats: {str(e)}")


@router.get("/companies", response_model=List[CompanyStats])
async def get_company_statistics(
    limit: int = Query(10, description="Number of top companies to return"),
    db: Session = Depends(get_database)
):
    """Get top companies by revenue and activity"""
    try:
        service = DashboardService(db)
        return service.get_company_stats(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch company stats: {str(e)}")


@router.get("/credits", response_model=CreditUsageStats)
async def get_credit_usage_statistics(
    db: Session = Depends(get_database)
):
    """Get credit system usage statistics"""
    try:
        service = DashboardService(db)
        return service.get_credit_usage_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch credit usage stats: {str(e)}")


@router.get("/revenue/current-month")
async def get_current_month_revenue(
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    db: Session = Depends(get_database)
):
    """Get current month revenue summary"""
    try:
        service = DashboardService(db)
        
        # Get current month data
        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)
        
        # Calculate end of current month
        if now.month == 12:
            end_date = datetime(now.year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            next_month = datetime(now.year, now.month + 1, 1)
            end_date = next_month - datetime.timedelta(days=1)
        
        revenue_data = service.get_revenue_by_period(
            period_type='month',
            start_date=start_date,
            end_date=end_date,
            company_id=company_id
        )
        
        return {
            "current_month": revenue_data[0] if revenue_data else None,
            "period": f"{now.strftime('%B %Y')}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch current month revenue: {str(e)}")


@router.get("/revenue/comparison")
async def get_revenue_comparison(
    period_type: str = Query("month", description="Period type for comparison"),
    periods_back: int = Query(3, description="Number of periods to compare"),
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    db: Session = Depends(get_database)
):
    """Get revenue comparison across multiple periods"""
    
    valid_periods = ['week', 'month', 'quarter', 'year']
    if period_type not in valid_periods:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid period_type. Must be one of: {', '.join(valid_periods)}"
        )
    
    try:
        service = DashboardService(db)
        now = datetime.now()
        results = []
        
        for i in range(periods_back):
            if period_type == 'month':
                if now.month - i <= 0:
                    target_month = 12 + (now.month - i)
                    target_year = now.year - 1
                else:
                    target_month = now.month - i
                    target_year = now.year
                
                start_date = datetime(target_year, target_month, 1)
                if target_month == 12:
                    end_date = datetime(target_year + 1, 1, 1) - datetime.timedelta(days=1)
                else:
                    next_month = datetime(target_year, target_month + 1, 1)
                    end_date = next_month - datetime.timedelta(days=1)
            
            # Add other period types as needed
            else:
                # Default to current month for now
                start_date = datetime(now.year, now.month, 1)
                end_date = datetime(now.year, now.month + 1, 1) - datetime.timedelta(days=1)
            
            period_data = service.get_revenue_by_period(
                period_type=period_type,
                start_date=start_date,
                end_date=end_date,
                company_id=company_id
            )
            
            if period_data:
                results.append({
                    "period": i,
                    "period_name": start_date.strftime('%B %Y') if period_type == 'month' else str(start_date.date()),
                    "data": period_data[0]
                })
        
        return {
            "comparison_data": results,
            "period_type": period_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch revenue comparison: {str(e)}")