"""
API dependencies for dependency injection.
Handles database sessions, authentication, and authorization.
"""
from typing import Annotated
from uuid import UUID
from fastapi import Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.models.user import User, UserRole


# Security scheme for JWT bearer token
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    session: Annotated[Session, Depends(get_session)]
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    
    Usage in endpoints:
        async def my_endpoint(current_user: Annotated[User, Depends(get_current_user)]):
            ...
    """
    token = credentials.credentials
    user_id = decode_access_token(token)
    
    if not user_id:
        raise UnauthorizedException(detail="Invalid or expired token")
    
    # Fetch user from database
    query = select(User).where(User.id == UUID(user_id))
    result = session.exec(query)
    user = result.one_or_none()
    
    if not user:
        raise UnauthorizedException(detail="User not found")
    
    if not user.is_active:
        raise UnauthorizedException(detail="Inactive user account")
    
    return user


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Dependency to ensure current user is an admin.
    
    Usage in admin endpoints:
        async def admin_endpoint(admin: Annotated[User, Depends(get_current_admin)]):
            ...
    """
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenException(detail="Admin privileges required")
    
    return current_user


# Type aliases for cleaner endpoint signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]
DBSession = Annotated[Session, Depends(get_session)]