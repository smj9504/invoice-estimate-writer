"""
Production server runner
"""
import os
import uvicorn

# Set environment to production
os.environ["ENVIRONMENT"] = "production"

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
        workers=4
    )