#!/usr/bin/env python
"""
Production-ready server runner with SQLAdmin properly integrated
"""

import uvicorn
from app.main import app
from app.core.database_factory import get_database
from app.admin_app import create_admin
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize admin after app is created but before server starts
database = get_database()
if hasattr(database, 'engine'):
    try:
        # Initialize database tables
        database.init_database()
        # Create admin interface
        admin = create_admin(app, database.engine)
        logger.info("✅ SQLAdmin initialized successfully")
        logger.info("📝 Admin URL: http://localhost:8000/admin")
        logger.info("🔑 Login: username='admin', password='admin123'")
    except Exception as e:
        logger.error(f"Failed to initialize admin: {e}", exc_info=True)
else:
    logger.warning("SQLAdmin not available - database doesn't support SQLAlchemy")

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting MJ Estimate API Server")
    logger.info("=" * 60)
    logger.info("📍 API Documentation: http://localhost:8000/docs")
    logger.info("🔧 Admin Panel: http://localhost:8000/admin")
    logger.info("💾 Database: SQLite (Development Mode)")
    logger.info("=" * 60)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )