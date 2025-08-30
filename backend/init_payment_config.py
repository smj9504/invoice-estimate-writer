"""
Initialize default payment configurations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.domains.payment_config.service import PaymentConfigService

def init_payment_config():
    """Initialize default payment methods and frequencies"""
    db = SessionLocal()
    try:
        service = PaymentConfigService()
        service.initialize_default_payment_configs(db)
        print("Payment configurations initialized successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    init_payment_config()