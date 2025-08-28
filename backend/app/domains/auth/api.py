"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any
from typing import List

from app.core.database_factory import get_db_session as get_db
from .schemas import LoginRequest, UserCreate, UserResponse, Token, UserUpdate, ChangePasswordRequest
from .service import AuthService
from .dependencies import get_current_user, require_admin
from .models import User


router = APIRouter()
auth_service = AuthService()


@router.post("/register", response_model=UserResponse)
async def register(
    user_create: UserCreate,
    db: Any = Depends(get_db)
):
    """Register a new user"""
    # Check if user exists
    if auth_service.get_user_by_username(db, user_create.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    if auth_service.get_user_by_email(db, user_create.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    try:
        user = auth_service.create_user(db, user_create)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login(
    login_request: LoginRequest,
    db: Any = Depends(get_db)
):
    """Login with username/email and password"""
    user = auth_service.authenticate_user(
        db, 
        login_request.username, 
        login_request.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = auth_service.create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "role": user.role
        }
    )
    
    return Token(
        access_token=access_token,
        user=UserResponse.from_orm(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """Update current user information"""
    # Users cannot change their own role
    user_update.role = None
    
    updated_user = auth_service.update_user(db, current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return updated_user


@router.post("/me/change-password", response_model=dict)
async def change_password(
    password_change: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """Change current user's password"""
    success = auth_service.change_password(
        db,
        current_user.id,
        password_change.current_password,
        password_change.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    return {"message": "Password changed successfully"}


@router.get("/users", response_model=List[UserResponse])
async def get_users(
    current_user: User = Depends(require_admin),
    db: Any = Depends(get_db)
):
    """Get all users (admin only)"""
    # Handle both raw Session and DatabaseSession wrapper
    if hasattr(db, '_session'):
        session = db._session
    elif hasattr(db, 'query'):
        session = db
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid database session"
        )
    
    users = session.query(User).all()
    return users


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Any = Depends(get_db)
):
    """Update a user (admin only)"""
    updated_user = auth_service.update_user(db, user_id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return updated_user


@router.post("/init-admin", response_model=dict)
async def initialize_admin(
    db: Any = Depends(get_db)
):
    """Initialize the admin user (only works if no admin exists)"""
    admin = auth_service.create_initial_admin(db)
    if admin:
        return {"message": "Admin user created successfully"}
    else:
        return {"message": "Admin user already exists"}