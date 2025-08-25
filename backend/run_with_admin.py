#!/usr/bin/env python
"""
Run the application with admin interface properly initialized
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    print("Starting MJ Estimate API with Admin Interface")
    print("API Docs: http://localhost:8000/docs")
    print("Admin Interface: http://localhost:8000/admin")
    print("Login: admin / admin123")
    print("-" * 50)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )