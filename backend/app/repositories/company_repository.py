"""
Company repository implementations for different database providers.
"""

from typing import Any, Dict, List, Optional
import logging

from app.repositories.base import SQLAlchemyRepository, SupabaseRepository
from app.core.interfaces import DatabaseSession
from app.models.sqlalchemy_models import Company
from app.core.config import settings

logger = logging.getLogger(__name__)


class CompanyRepositoryMixin:
    """Mixin with company-specific methods"""
    
    def search_companies(self, search_term: str) -> List[Dict[str, Any]]:
        """Search companies by name, address, email, or phone"""
        # This will be implemented differently for each database type
        raise NotImplementedError("Subclasses must implement search_companies")
    
    def get_by_filters(self, 
                       search: Optional[str] = None,
                       city: Optional[str] = None,
                       state: Optional[str] = None,
                       limit: Optional[int] = None,
                       offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get companies with search and location filters"""
        filters = {}
        
        # Add city and state filters
        if city:
            filters['city'] = city
        if state:
            filters['state'] = state
        
        # If no search term, use regular filtering
        if not search:
            return self.get_all(filters=filters, limit=limit, offset=offset, order_by='name')
        
        # If search term is provided, use search functionality
        return self.search_companies(search)
    
    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get company by email address"""
        companies = self.get_all(filters={'email': email}, limit=1)
        return companies[0] if companies else None
    
    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get company by exact name match"""
        companies = self.get_all(filters={'name': name}, limit=1)
        return companies[0] if companies else None


class CompanySQLAlchemyRepository(SQLAlchemyRepository, CompanyRepositoryMixin):
    """SQLAlchemy-based company repository for SQLite/PostgreSQL"""
    
    def __init__(self, session: DatabaseSession):
        super().__init__(session, Company)
    
    def search_companies(self, search_term: str) -> List[Dict[str, Any]]:
        """Search companies using SQL LIKE queries"""
        try:
            search_pattern = f"%{search_term.lower()}%"
            
            entities = self.db_session.query(Company).filter(
                (Company.name.ilike(search_pattern)) |
                (Company.address.ilike(search_pattern)) |
                (Company.email.ilike(search_pattern)) |
                (Company.phone.ilike(search_pattern))
            ).order_by(Company.name).all()
            
            return [self._convert_to_dict(entity) for entity in entities]
            
        except Exception as e:
            logger.error(f"Error searching companies: {e}")
            raise Exception(f"Failed to search companies: {e}")
    
    def get_companies_with_stats(self) -> List[Dict[str, Any]]:
        """Get companies with additional statistics"""
        try:
            from app.models.sqlalchemy_models import Invoice, Estimate
            
            # Query companies with related counts
            result = self.db_session.query(
                Company,
                self.db_session.query(Invoice).filter(Invoice.company_id == Company.id).count().label('invoice_count'),
                self.db_session.query(Estimate).filter(Estimate.company_id == Company.id).count().label('estimate_count')
            ).all()
            
            companies_with_stats = []
            for company, invoice_count, estimate_count in result:
                company_dict = self._convert_to_dict(company)
                company_dict['invoice_count'] = invoice_count
                company_dict['estimate_count'] = estimate_count
                companies_with_stats.append(company_dict)
            
            return companies_with_stats
            
        except Exception as e:
            logger.error(f"Error getting companies with stats: {e}")
            return self.get_all()


class CompanySupabaseRepository(SupabaseRepository, CompanyRepositoryMixin):
    """Supabase-based company repository"""
    
    def __init__(self, session: DatabaseSession):
        super().__init__(session, "companies", Company)
    
    def search_companies(self, search_term: str) -> List[Dict[str, Any]]:
        """Search companies using Supabase text search"""
        try:
            # Get all companies first, then filter in Python
            # This is a limitation of the current Supabase client
            all_companies = self.get_all()
            
            search_lower = search_term.lower()
            filtered_companies = [
                company for company in all_companies
                if (
                    search_lower in (company.get('name', '') or '').lower() or
                    search_lower in (company.get('address', '') or '').lower() or
                    search_lower in (company.get('email', '') or '').lower() or
                    search_lower in (company.get('phone', '') or '').lower()
                )
            ]
            
            # Sort by name
            filtered_companies.sort(key=lambda x: x.get('name', ''))
            
            return filtered_companies
            
        except Exception as e:
            logger.error(f"Error searching companies in Supabase: {e}")
            raise Exception(f"Failed to search companies: {e}")
    
    def get_companies_with_stats(self) -> List[Dict[str, Any]]:
        """Get companies with additional statistics (basic implementation)"""
        try:
            # For now, just return companies without stats
            # Could be enhanced with stored procedures or additional queries
            companies = self.get_all()
            
            for company in companies:
                # Add placeholder stats
                company['invoice_count'] = 0
                company['estimate_count'] = 0
            
            return companies
            
        except Exception as e:
            logger.error(f"Error getting companies with stats from Supabase: {e}")
            return self.get_all()
    
    def create(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create company with Supabase-specific handling"""
        # Remove fields that might cause issues in Supabase
        clean_data = entity_data.copy()
        
        # Remove None values
        clean_data = {k: v for k, v in clean_data.items() if v is not None}
        
        # Remove timestamp fields (they're auto-managed by Supabase)
        clean_data.pop('created_at', None)
        clean_data.pop('updated_at', None)
        
        return super().create(clean_data)
    
    def update(self, entity_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update company with Supabase-specific handling"""
        # Remove fields that might cause issues in Supabase
        clean_data = update_data.copy()
        
        # Remove None values
        clean_data = {k: v for k, v in clean_data.items() if v is not None}
        
        # Remove timestamp fields and ID
        clean_data.pop('created_at', None)
        clean_data.pop('updated_at', None)
        clean_data.pop('id', None)
        
        if not clean_data:
            logger.warning(f"No valid data to update for company {entity_id}")
            return self.get_by_id(entity_id)
        
        return super().update(entity_id, clean_data)


def get_company_repository(session: DatabaseSession) -> CompanyRepositoryMixin:
    """Factory function to get appropriate company repository based on database type"""
    
    # Determine which repository to use based on session type or configuration
    if hasattr(session, 'query'):
        # SQLAlchemy session
        return CompanySQLAlchemyRepository(session)
    else:
        # Assume Supabase client
        return CompanySupabaseRepository(session)