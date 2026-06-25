"""FastAPI dependency injection for authentication and authorization.

This module provides dependencies for extracting the current authenticated
user from JWT tokens and enforcing role-based access control.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db, settings
from service.auth_service import AuthService

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """Dependency to extract and validate the current authenticated user.

    Decodes the JWT token from the Authorization header, extracts the
    user ID from the 'sub' claim, and retrieves the user via AuthService
    (with Redis cache support).

    Args:
        credentials: Bearer token from the Authorization header.
        db: Async database session.

    Returns:
        User: The authenticated user.

    Raises:
        HTTPException 401: If the token is invalid or user not found.
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get('sub')
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    auth_service = AuthService(db)
    user = await auth_service.get_current_user(int(user_id))
    if user is None:
        raise credentials_exception

    return user


def require_role(required_role: str):
    """Dependency factory that restricts access to a specific user role.

    Creates a FastAPI dependency that checks if the current user has
    the required role. Returns 403 Forbidden if the role doesn't match.

    Usage:
        @router.get('/admin')
        async def admin_endpoint(user = Depends(require_role('admin'))):
            ...

    Args:
        required_role: The role required to access the endpoint (e.g., 'admin').

    Returns:
        Callable: A FastAPI dependency function.
    """
    async def role_checker(current_user=Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'This action requires {required_role} role',
            )
        return current_user
    return role_checker