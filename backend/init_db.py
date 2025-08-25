"""
Initialize database tables and create initial data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database_factory import db_factory, Base
from app.models.sqlalchemy_models import (
    Company, Invoice, InvoiceItem, 
    Estimate, EstimateItem, PlumberReport, Document
)
from app.core.config import settings

def init_database():
    """Create all tables in the database"""
    print(f"Initializing database in {settings.ENVIRONMENT} mode...")
    
    if settings.ENVIRONMENT == "development":
        print(f"Using SQLite database: {settings.SQLITE_DB_PATH}")
    else:
        print("Using configured database")
    
    # Initialize database
    database = db_factory.get_database()
    database.init_database()
    print("Database tables created successfully!")
    
    # You can add initial data here if needed
    # Example:
    # database = db_factory.get_database()
    # with database.get_session() as session:
    #     # Add initial company
    #     company = Company(
    #         name="MJ Estimate Inc.",
    #         address="123 Main St",
    #         phone="555-0100",
    #         email="info@mjestimate.com",
    #         city="New York",
    #         state="NY",
    #         zipcode="10001",
    #         company_code="MJES"
    #     )
    #     session.add(company)
    #     session.commit()
    #     print("Initial data created successfully!")

if __name__ == "__main__":
    init_database()