"""
Initialize admin user for development environment
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database_factory import get_database
from app.auth.service import AuthService
from app.auth.schemas import UserCreate
from app.auth.models import UserRole

def init_admin():
    """Initialize admin user if not exists"""
    db = get_database()
    
    with db.get_session() as session:
        auth_service = AuthService()
        
        # Check if admin already exists
        existing_admin = auth_service.create_initial_admin(session)
        if existing_admin:
            print("Admin user created successfully:")
            print(f"  Username: admin")
            print(f"  Password: admin123")
            print(f"  Email: admin@mjestimate.com")
        else:
            print("Admin user already exists")

if __name__ == "__main__":
    init_admin()