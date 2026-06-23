from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from service.auth_service import AuthService
from service.auth_deps import get_current_user
from service.email_service import send_verification_email
from service.cloudinary_service import upload_avatar
from schemas.auth import UserCreate, UserResponse, TokenResponse, LoginRequest, RequestEmail
from models.user import User


limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix='/api/auth', tags=['auth'])


@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    auth_service = AuthService(db)
    try:
        user = await auth_service.register(user_data)
        # Send verification email (fire and forget - don't block registration)
        try:
            await send_verification_email(user_data.email, user_data.email)
        except Exception:
            pass
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post('/login', response_model=TokenResponse)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT token"""
    auth_service = AuthService(db)
    try:
        return await auth_service.login(login_data.email, login_data.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get('/confirm_email/{token}', response_model=UserResponse)
async def confirm_email(token: str, db: AsyncSession = Depends(get_db)):
    """Verify user email with token"""
    auth_service = AuthService(db)
    try:
        return await auth_service.verify_email(token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post('/request_email')
async def request_email(body: RequestEmail, db: AsyncSession = Depends(get_db)):
    """Request email verification link again"""
    auth_service = AuthService(db)
    user = await auth_service.repository.get_by_email(body.email)
    if user and not user.is_verified:
        try:
            await send_verification_email(body.email, user.verification_token)
        except Exception:
            pass
    return {'message': 'If the email exists, a verification link has been sent.'}


@router.get('/me', response_model=UserResponse)
@limiter.limit('5/minute')
async def get_me(request: Request, current_user: User = Depends(get_current_user)):
    """Get current authenticated user profile"""
    return UserResponse.model_validate(current_user)


@router.patch('/avatar', response_model=UserResponse)
async def update_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user avatar"""
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='File must be an image',
        )

    auth_service = AuthService(db)
    try:
        file_data = await file.read()
        avatar_url = await upload_avatar(file_data, current_user.id)
        return await auth_service.update_avatar(current_user.id, avatar_url)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )