"""
Authentication dependencies for FastAPI
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Any
from uuid import UUID

from app.core.database_factory import get_db_session as get_db
from .service import AuthService
from app.domains.staff.models import Staff, StaffRole
from .schemas import TokenData


security = HTTPBearer()
auth_service = AuthService()


async def get_current_staff(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Any = Depends(get_db)
) -> Staff:
    """Get the current authenticated staff member"""
    token = credentials.credentials
    token_data = auth_service.decode_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    staff = auth_service.get_staff_by_id(db, UUID(token_data.user_id))
    if staff is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Staff member not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not staff.is_active or not staff.can_login:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff member is inactive or not allowed to login"
        )
    
    return staff


async def get_current_staff_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Any = Depends(get_db)
) -> Optional[Staff]:
    """Get the current staff member if authenticated, otherwise None"""
    if not credentials:
        return None
    
    try:
        return await get_current_staff(credentials, db)
    except HTTPException:
        return None


async def require_admin(
    current_staff: Staff = Depends(get_current_staff)
) -> Staff:
    """Require the current staff member to be an admin"""
    if current_staff.role not in [StaffRole.admin, StaffRole.super_admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_staff


async def require_manager_or_admin(
    current_staff: Staff = Depends(get_current_staff)
) -> Staff:
    """Require the current staff member to be a manager or admin"""
    if current_staff.role not in [StaffRole.admin, StaffRole.super_admin, StaffRole.manager, StaffRole.supervisor]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager or admin access required"
        )
    return current_staff


# Backwards compatibility aliases
get_current_user = get_current_staff
get_current_user_optional = get_current_staff_optional