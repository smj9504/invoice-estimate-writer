"""
Database connection and management
"""

from supabase import create_client, Client
from app.core.config import settings

class Database:
    """Database connection manager"""
    
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def client(self) -> Client:
        """Get Supabase client"""
        if self._client is None:
            self._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
        return self._client
    
    def get_client(self) -> Client:
        """Get Supabase client (alternative method)"""
        return self.client

# Create database instance
db = Database()

# Dependency for FastAPI
def get_db() -> Client:
    """Get database dependency for FastAPI"""
    return db.client