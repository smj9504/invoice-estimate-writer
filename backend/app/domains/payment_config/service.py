"""
Payment configuration service
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from .models import PaymentMethod, PaymentFrequency
from .schemas import (
    PaymentMethodCreate, PaymentMethodUpdate,
    PaymentFrequencyCreate, PaymentFrequencyUpdate
)

logger = logging.getLogger(__name__)


class PaymentConfigService:
    """Service for managing payment configuration"""
    
    # Payment Method operations
    def get_payment_methods(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[PaymentMethod]:
        """Get all payment methods"""
        query = db.query(PaymentMethod)
        if active_only:
            query = query.filter(PaymentMethod.is_active == True)
        return query.order_by(PaymentMethod.display_order, PaymentMethod.name).offset(skip).limit(limit).all()
    
    def get_payment_method(self, db: Session, method_id: str) -> Optional[PaymentMethod]:
        """Get payment method by ID"""
        return db.query(PaymentMethod).filter(PaymentMethod.id == method_id).first()
    
    def get_payment_method_by_code(self, db: Session, code: str) -> Optional[PaymentMethod]:
        """Get payment method by code"""
        return db.query(PaymentMethod).filter(PaymentMethod.code == code).first()
    
    def create_payment_method(self, db: Session, method: PaymentMethodCreate) -> PaymentMethod:
        """Create new payment method"""
        # Check if code already exists
        existing = self.get_payment_method_by_code(db, method.code)
        if existing:
            raise ValueError(f"Payment method with code '{method.code}' already exists")
        
        # If setting as default, unset other defaults
        if method.is_default:
            db.query(PaymentMethod).update({'is_default': False})
        
        db_method = PaymentMethod(**method.dict())
        db.add(db_method)
        db.commit()
        db.refresh(db_method)
        logger.info(f"Created payment method: {method.code}")
        return db_method
    
    def update_payment_method(
        self,
        db: Session,
        method_id: str,
        method: PaymentMethodUpdate
    ) -> Optional[PaymentMethod]:
        """Update payment method"""
        db_method = self.get_payment_method(db, method_id)
        if not db_method:
            return None
        
        update_data = method.dict(exclude_unset=True)
        
        # If setting as default, unset other defaults
        if update_data.get('is_default'):
            db.query(PaymentMethod).filter(PaymentMethod.id != method_id).update({'is_default': False})
        
        update_data['updated_at'] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(db_method, field, value)
        
        db.commit()
        db.refresh(db_method)
        logger.info(f"Updated payment method: {db_method.code}")
        return db_method
    
    def delete_payment_method(self, db: Session, method_id: str) -> bool:
        """Delete payment method"""
        db_method = self.get_payment_method(db, method_id)
        if not db_method:
            return False
        
        db.delete(db_method)
        db.commit()
        logger.info(f"Deleted payment method: {db_method.code}")
        return True
    
    # Payment Frequency operations
    def get_payment_frequencies(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[PaymentFrequency]:
        """Get all payment frequencies"""
        query = db.query(PaymentFrequency)
        if active_only:
            query = query.filter(PaymentFrequency.is_active == True)
        return query.order_by(PaymentFrequency.display_order, PaymentFrequency.name).offset(skip).limit(limit).all()
    
    def get_payment_frequency(self, db: Session, frequency_id: str) -> Optional[PaymentFrequency]:
        """Get payment frequency by ID"""
        return db.query(PaymentFrequency).filter(PaymentFrequency.id == frequency_id).first()
    
    def get_payment_frequency_by_code(self, db: Session, code: str) -> Optional[PaymentFrequency]:
        """Get payment frequency by code"""
        return db.query(PaymentFrequency).filter(PaymentFrequency.code == code).first()
    
    def create_payment_frequency(self, db: Session, frequency: PaymentFrequencyCreate) -> PaymentFrequency:
        """Create new payment frequency"""
        # Check if code already exists
        existing = self.get_payment_frequency_by_code(db, frequency.code)
        if existing:
            raise ValueError(f"Payment frequency with code '{frequency.code}' already exists")
        
        # If setting as default, unset other defaults
        if frequency.is_default:
            db.query(PaymentFrequency).update({'is_default': False})
        
        db_frequency = PaymentFrequency(**frequency.dict())
        db.add(db_frequency)
        db.commit()
        db.refresh(db_frequency)
        logger.info(f"Created payment frequency: {frequency.code}")
        return db_frequency
    
    def update_payment_frequency(
        self,
        db: Session,
        frequency_id: str,
        frequency: PaymentFrequencyUpdate
    ) -> Optional[PaymentFrequency]:
        """Update payment frequency"""
        db_frequency = self.get_payment_frequency(db, frequency_id)
        if not db_frequency:
            return None
        
        update_data = frequency.dict(exclude_unset=True)
        
        # If setting as default, unset other defaults
        if update_data.get('is_default'):
            db.query(PaymentFrequency).filter(PaymentFrequency.id != frequency_id).update({'is_default': False})
        
        update_data['updated_at'] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(db_frequency, field, value)
        
        db.commit()
        db.refresh(db_frequency)
        logger.info(f"Updated payment frequency: {db_frequency.code}")
        return db_frequency
    
    def delete_payment_frequency(self, db: Session, frequency_id: str) -> bool:
        """Delete payment frequency"""
        db_frequency = self.get_payment_frequency(db, frequency_id)
        if not db_frequency:
            return False
        
        db.delete(db_frequency)
        db.commit()
        logger.info(f"Deleted payment frequency: {db_frequency.code}")
        return True
    
    def initialize_default_payment_configs(self, db: Session):
        """Initialize default payment methods and frequencies"""
        # Default payment methods
        default_methods = [
            {"code": "zelle", "name": "Zelle", "description": "Bank transfer via Zelle", "display_order": 1},
            {"code": "stripe", "name": "Stripe", "description": "Credit/Debit card via Stripe", "display_order": 2},
            {"code": "check", "name": "Check", "description": "Payment by check", "display_order": 3},
            {"code": "cash", "name": "Cash", "description": "Cash payment", "display_order": 4},
            {"code": "wire", "name": "Wire Transfer", "description": "Bank wire transfer", "display_order": 5},
        ]
        
        for i, method_data in enumerate(default_methods):
            if not self.get_payment_method_by_code(db, method_data["code"]):
                method = PaymentMethodCreate(
                    **method_data,
                    is_default=(i == 0)  # First one is default
                )
                self.create_payment_method(db, method)
        
        # Default payment frequencies
        default_frequencies = [
            {"code": "per_job", "name": "Per Job", "description": "Payment upon job completion", "display_order": 1},
            {"code": "weekly", "name": "Weekly", "description": "Weekly payment", "days_interval": 7, "display_order": 2},
            {"code": "biweekly", "name": "Bi-Weekly", "description": "Payment every two weeks", "days_interval": 14, "display_order": 3},
            {"code": "monthly", "name": "Monthly", "description": "Monthly payment", "days_interval": 30, "display_order": 4},
            {"code": "prepaid", "name": "Prepaid", "description": "Payment in advance", "display_order": 5},
        ]
        
        for i, freq_data in enumerate(default_frequencies):
            if not self.get_payment_frequency_by_code(db, freq_data["code"]):
                frequency = PaymentFrequencyCreate(
                    **freq_data,
                    is_default=(i == 0)  # First one is default
                )
                self.create_payment_frequency(db, frequency)
        
        logger.info("Initialized default payment configurations")