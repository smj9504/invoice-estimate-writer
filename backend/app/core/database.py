"""
Database connection and management
"""

from typing import Union, Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from supabase import create_client, Client
from app.core.config import settings

Base = declarative_base()

class Database:
    """Database connection manager"""
    
    _instance = None
    _client = None
    _engine = None
    _SessionLocal = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def client(self) -> Union[Client, Session]:
        """Get database client"""
        if settings.USE_SQLITE:
            return self.get_session()
        else:
            if self._client is None:
                if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                    raise ValueError("Supabase URL and Key are required for production")
                self._client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_KEY
                )
            return self._client
    
    def get_engine(self):
        """Get SQLAlchemy engine for SQLite"""
        if self._engine is None:
            database_url = f"sqlite:///{settings.SQLITE_DB_PATH}"
            self._engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False}
            )
            # Import models to ensure they're registered
            from app.domains.staff.models import Staff
            from app.domains.company.models import Company
            from app.domains.work_order.models import WorkOrder
            from app.domains.payment.models import Payment
            Base.metadata.create_all(bind=self._engine)
        return self._engine
    
    def get_session(self) -> Session:
        """Get SQLAlchemy session for SQLite"""
        if self._SessionLocal is None:
            engine = self.get_engine()
            self._SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine
            )
        return self._SessionLocal()
    
    def get_client(self) -> Union[Client, Session]:
        """Get database client (alternative method)"""
        return self.client

# Create database instance
db = Database()

# Dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """Get database dependency for FastAPI"""
    if settings.USE_SQLITE:
        session = db.get_session()
        try:
            yield session
        finally:
            session.close()
    else:
        # For Supabase, return the client directly
        yield db.client