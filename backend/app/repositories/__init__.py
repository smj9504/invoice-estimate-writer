"""
Repository layer for database abstraction.
Provides consistent interfaces for data access across different database providers.
"""

from app.repositories.company_repository import (
    CompanyRepositoryMixin,
    CompanySQLAlchemyRepository,
    CompanySupabaseRepository,
    get_company_repository
)

from app.repositories.invoice_repository import (
    InvoiceRepositoryMixin,
    InvoiceSQLAlchemyRepository,
    InvoiceSupabaseRepository,
    get_invoice_repository
)

from app.repositories.estimate_repository import (
    EstimateRepositoryMixin,
    EstimateSQLAlchemyRepository,
    EstimateSupabaseRepository,
    get_estimate_repository
)

from app.repositories.plumber_report_repository import (
    PlumberReportRepositoryMixin,
    PlumberReportSQLAlchemyRepository,
    PlumberReportSupabaseRepository,
    get_plumber_report_repository
)

from app.repositories.base import (
    BaseRepository,
    SQLAlchemyRepository,
    SupabaseRepository
)

__all__ = [
    # Company repositories
    'CompanyRepositoryMixin',
    'CompanySQLAlchemyRepository',
    'CompanySupabaseRepository',
    'get_company_repository',
    
    # Invoice repositories
    'InvoiceRepositoryMixin',
    'InvoiceSQLAlchemyRepository',
    'InvoiceSupabaseRepository',
    'get_invoice_repository',
    
    # Estimate repositories
    'EstimateRepositoryMixin',
    'EstimateSQLAlchemyRepository',
    'EstimateSupabaseRepository',
    'get_estimate_repository',
    
    # Plumber report repositories
    'PlumberReportRepositoryMixin',
    'PlumberReportSQLAlchemyRepository',
    'PlumberReportSupabaseRepository',
    'get_plumber_report_repository',
    
    # Base classes
    'BaseRepository',
    'SQLAlchemyRepository',
    'SupabaseRepository',
]