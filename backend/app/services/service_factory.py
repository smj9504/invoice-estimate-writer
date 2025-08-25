"""
Service Factory for managing service instances and dependency injection.
Provides centralized service creation and lifecycle management.
"""

from typing import Dict, Type, TypeVar, Optional, Any
from abc import ABC
import logging
import threading
from contextlib import contextmanager

from app.core.interfaces import DatabaseProvider, ServiceInterface
from app.core.database_factory import get_database
from app.services.company_service import CompanyService
from app.services.invoice_service import InvoiceService
from app.services.estimate_service import EstimateService
from app.work_order.service import WorkOrderService
from app.payment.service import PaymentService
from app.credit.service import CreditService
from app.staff.service import StaffService

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=ServiceInterface)


class ServiceRegistry:
    """
    Registry for service types and their implementations.
    Allows for easy swapping of service implementations.
    """
    
    def __init__(self):
        self._services: Dict[str, Type[ServiceInterface]] = {}
        self._lock = threading.Lock()
    
    def register(self, service_name: str, service_class: Type[ServiceInterface]):
        """
        Register a service implementation.
        
        Args:
            service_name: Name of the service
            service_class: Service implementation class
        """
        with self._lock:
            self._services[service_name] = service_class
            logger.debug(f"Registered service: {service_name} -> {service_class.__name__}")
    
    def get(self, service_name: str) -> Optional[Type[ServiceInterface]]:
        """
        Get a registered service class.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service class or None if not found
        """
        return self._services.get(service_name)
    
    def list_services(self) -> Dict[str, Type[ServiceInterface]]:
        """
        Get all registered services.
        
        Returns:
            Dictionary of service names to classes
        """
        return self._services.copy()


class ServiceFactory:
    """
    Factory for creating and managing service instances.
    Provides singleton pattern and dependency injection.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self._services: Dict[str, ServiceInterface] = {}
        self._database: Optional[DatabaseProvider] = None
        self._registry = ServiceRegistry()
        self._initialize_default_services()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def _initialize_default_services(self):
        """Register default service implementations"""
        self._registry.register('company', CompanyService)
        self._registry.register('invoice', InvoiceService)
        self._registry.register('estimate', EstimateService)
        self._registry.register('work_order', WorkOrderService)
        self._registry.register('payment', PaymentService)
        self._registry.register('credit', CreditService)
        self._registry.register('staff', StaffService)
    
    def set_database(self, database: DatabaseProvider):
        """
        Set the database provider for all services.
        
        Args:
            database: Database provider instance
        """
        self._database = database
        # Clear existing service instances to force recreation with new database
        self._services.clear()
        logger.info(f"Database provider set to: {database.provider_name}")
    
    def get_database(self) -> DatabaseProvider:
        """
        Get the current database provider.
        
        Returns:
            Database provider instance
        """
        if self._database is None:
            self._database = get_database()
        return self._database
    
    def get_service(self, service_name: str) -> ServiceInterface:
        """
        Get a service instance (singleton pattern).
        
        Args:
            service_name: Name of the service ('company', 'invoice', 'estimate', etc.)
            
        Returns:
            Service instance
            
        Raises:
            ValueError: If service is not registered
        """
        if service_name not in self._services:
            with self._lock:
                if service_name not in self._services:
                    service_class = self._registry.get(service_name)
                    if service_class is None:
                        raise ValueError(f"Service '{service_name}' is not registered")
                    
                    # Create service instance with database dependency
                    database = self.get_database()
                    self._services[service_name] = service_class(database)
                    logger.debug(f"Created service instance: {service_name}")
        
        return self._services[service_name]
    
    def create_service(self, service_name: str, database: DatabaseProvider = None) -> ServiceInterface:
        """
        Create a new service instance (not singleton).
        
        Args:
            service_name: Name of the service
            database: Optional database provider (uses default if None)
            
        Returns:
            New service instance
            
        Raises:
            ValueError: If service is not registered
        """
        service_class = self._registry.get(service_name)
        if service_class is None:
            raise ValueError(f"Service '{service_name}' is not registered")
        
        db = database or self.get_database()
        return service_class(db)
    
    def register_service(self, service_name: str, service_class: Type[ServiceInterface]):
        """
        Register a new service implementation.
        
        Args:
            service_name: Name of the service
            service_class: Service implementation class
        """
        self._registry.register(service_name, service_class)
        
        # Remove existing instance if present to force recreation
        self._services.pop(service_name, None)
    
    def reset(self):
        """
        Reset all service instances.
        Useful for testing or when changing database providers.
        """
        with self._lock:
            self._services.clear()
            self._database = None
        logger.info("Service factory reset")
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about registered and active services.
        
        Returns:
            Dictionary with service information
        """
        registered_services = list(self._registry.list_services().keys())
        active_services = list(self._services.keys())
        
        return {
            'registered_services': registered_services,
            'active_services': active_services,
            'database_provider': self.get_database().provider_name,
            'total_registered': len(registered_services),
            'total_active': len(active_services)
        }


class ServiceManager:
    """
    Context manager for service lifecycle management.
    Provides transactional service operations.
    """
    
    def __init__(self, factory: ServiceFactory = None):
        self.factory = factory or get_service_factory()
        self._services_used: Dict[str, ServiceInterface] = {}
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup if needed
        self._services_used.clear()
    
    def get_service(self, service_name: str) -> ServiceInterface:
        """
        Get a service within the managed context.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service instance
        """
        if service_name not in self._services_used:
            self._services_used[service_name] = self.factory.get_service(service_name)
        
        return self._services_used[service_name]
    
    @contextmanager
    def transaction(self):
        """
        Execute operations within a transaction context.
        Note: Only works with databases that support transactions.
        """
        database = self.factory.get_database()
        
        if hasattr(database, 'get_unit_of_work'):
            with database.get_unit_of_work() as uow:
                # Temporarily replace services with transaction-aware versions
                original_services = self._services_used.copy()
                try:
                    # Create transaction-aware services
                    for service_name in self._services_used.keys():
                        # This would require services to support transaction contexts
                        pass
                    
                    yield uow
                finally:
                    self._services_used = original_services
        else:
            # Fallback for databases without transaction support
            yield None


# Global service factory instance
_service_factory = None
_factory_lock = threading.Lock()


def get_service_factory() -> ServiceFactory:
    """
    Get the global service factory instance.
    
    Returns:
        ServiceFactory instance
    """
    global _service_factory
    if _service_factory is None:
        with _factory_lock:
            if _service_factory is None:
                _service_factory = ServiceFactory()
    return _service_factory


def get_company_service() -> CompanyService:
    """
    Get company service instance.
    
    Returns:
        CompanyService instance
    """
    return get_service_factory().get_service('company')


def get_invoice_service() -> InvoiceService:
    """
    Get invoice service instance.
    
    Returns:
        InvoiceService instance
    """
    return get_service_factory().get_service('invoice')


def get_estimate_service() -> EstimateService:
    """
    Get estimate service instance.
    
    Returns:
        EstimateService instance
    """
    return get_service_factory().get_service('estimate')


def get_work_order_service() -> WorkOrderService:
    """
    Get work order service instance.
    
    Returns:
        WorkOrderService instance
    """
    return get_service_factory().get_service('work_order')


def get_payment_service() -> PaymentService:
    """
    Get payment service instance.
    
    Returns:
        PaymentService instance
    """
    return get_service_factory().get_service('payment')


def get_credit_service() -> CreditService:
    """
    Get credit service instance.
    
    Returns:
        CreditService instance
    """
    return get_service_factory().get_service('credit')


def get_staff_service() -> StaffService:
    """
    Get staff service instance.
    
    Returns:
        StaffService instance
    """
    return get_service_factory().get_service('staff')


@contextmanager
def get_service_manager():
    """
    Get service manager context.
    
    Yields:
        ServiceManager instance
    """
    with ServiceManager() as manager:
        yield manager


# Dependency injection functions for FastAPI
def get_company_service_dependency() -> CompanyService:
    """FastAPI dependency for company service"""
    return get_company_service()


def get_invoice_service_dependency() -> InvoiceService:
    """FastAPI dependency for invoice service"""
    return get_invoice_service()


def get_estimate_service_dependency() -> EstimateService:
    """FastAPI dependency for estimate service"""
    return get_estimate_service()


def get_work_order_service_dependency() -> WorkOrderService:
    """FastAPI dependency for work order service"""
    return get_work_order_service()


def get_payment_service_dependency() -> PaymentService:
    """FastAPI dependency for payment service"""
    return get_payment_service()


def get_credit_service_dependency() -> CreditService:
    """FastAPI dependency for credit service"""
    return get_credit_service()


def get_staff_service_dependency() -> StaffService:
    """FastAPI dependency for staff service"""
    return get_staff_service()


def get_service_factory_dependency() -> ServiceFactory:
    """FastAPI dependency for service factory"""
    return get_service_factory()