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
    """Dependency to get the current authenticated user from JWT token"""
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