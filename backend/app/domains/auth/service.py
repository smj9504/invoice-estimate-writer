"""
Authentication service layer
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
import bcrypt
import jwt
from sqlalchemy.orm import Session
from app.core.database_factory import DatabaseSession
from sqlalchemy.exc import IntegrityError

from .models import User, UserRole
from . import schemas
from app.core.config import settings


class AuthService:
    SECRET_KEY = settings.SECRET_KEY
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, AuthService.SECRET_KEY, algorithm=AuthService.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Optional[schemas.TokenData]:
        """Decode and validate a JWT token"""
        try:
            payload = jwt.decode(token, AuthService.SECRET_KEY, algorithms=[AuthService.ALGORITHM])
            user_id = payload.get("sub")
            username = payload.get("username")
            role = payload.get("role")
            
            if user_id is None:
                return None
                
            return schemas.TokenData(
                user_id=user_id,
                username=username,
                role=role
            )
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
    
    def create_user(self, db, user_create: schemas.UserCreate) -> User:
        """Create a new user"""
        hashed_password = self.hash_password(user_create.password)
        
        db_user = User(
            username=user_create.username,
            email=user_create.email,
            full_name=user_create.full_name,
            hashed_password=hashed_password,
            role=user_create.role
        )
        
        try:
            # Handle both raw Session and DatabaseSession wrapper
            if hasattr(db, '_session'):
                session = db._session
            else:
                session = db
            
            session.add(db_user)
            session.commit()
            session.refresh(db_user)
            return db_user
        except IntegrityError:
            if hasattr(db, 'rollback'):
                db.rollback()
            raise ValueError("Username or email already exists")
    
    def authenticate_user(self, db, username: str, password: str) -> Optional[User]:
        """Authenticate a user by username and password"""
        # Handle both raw Session and DatabaseSession wrapper
        if hasattr(db, '_session'):
            session = db._session
        elif hasattr(db, 'query'):
            session = db
        else:
            raise ValueError("Invalid database session type")
            
        user = session.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user:
            return None
            
        if not self.verify_password(password, user.hashed_password):
            return None
            
        # Update last login
        user.last_login = datetime.utcnow()
        if hasattr(db, '_session'):
            db._session.commit()
        else:
            db.commit()
        
        return user
    
    def get_user_by_id(self, db, user_id: UUID) -> Optional[User]:
        """Get a user by ID"""
        # Handle both raw Session and DatabaseSession wrapper
        if hasattr(db, '_session'):
            session = db._session
        elif hasattr(db, 'query'):
            session = db
        else:
            return None
            
        return session.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, db, username: str) -> Optional[User]:
        """Get a user by username"""
        # Handle both raw Session and DatabaseSession wrapper
        if hasattr(db, '_session'):
            session = db._session
        elif hasattr(db, 'query'):
            session = db
        else:
            return None
            
        return session.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, db, email: str) -> Optional[User]:
        """Get a user by email"""
        # Handle both raw Session and DatabaseSession wrapper
        if hasattr(db, '_session'):
            session = db._session
        elif hasattr(db, 'query'):
            session = db
        else:
            return None
            
        return session.query(User).filter(User.email == email).first()
    
    def update_user(self, db, user_id: UUID, user_update: schemas.UserUpdate) -> Optional[User]:
        """Update a user"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return None
        
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        if hasattr(db, '_session'):
            db._session.commit()
            db._session.refresh(user)
        else:
            db.commit()
            db.refresh(user)
        
        return user
    
    def change_password(self, db, user_id: UUID, current_password: str, new_password: str) -> bool:
        """Change a user's password"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return False
        
        if not self.verify_password(current_password, user.hashed_password):
            return False
        
        user.hashed_password = self.hash_password(new_password)
        user.updated_at = datetime.utcnow()
        if hasattr(db, '_session'):
            db._session.commit()
        else:
            db.commit()
        
        return True
    
    def create_initial_admin(self, db) -> Optional[User]:
        """Create the initial admin user if none exists"""
        # Handle both raw Session and DatabaseSession wrapper
        if hasattr(db, '_session'):
            session = db._session
        elif hasattr(db, 'query'):
            session = db
        else:
            return None
            
        admin_exists = session.query(User).filter(User.role == UserRole.ADMIN).first()
        if admin_exists:
            return None
        
        admin_user = schemas.UserCreate(
            username="admin",
            email="admin@mjestimate.com",
            password="admin123",
            full_name="System Administrator",
            role=UserRole.ADMIN
        )
        
        return self.create_user(db, admin_user)