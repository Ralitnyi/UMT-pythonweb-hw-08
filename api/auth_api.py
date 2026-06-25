"""Authentication API routes.

This module defines the FastAPI router for authentication endpoints
including user registration, login, email verification, password reset,
and profile management with avatar upload.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from service.auth_service import AuthService
from service.auth_deps import get_current_user, require_role
from service.email_service import send_verification_email, send_reset_password_email
from service.cloudinary_service import upload_avatar
from schemas.auth import (
    UserCreate, UserResponse, TokenResponse,
    LoginRequest, RequestEmail, PasswordResetRequest, PasswordResetConfirm,
)
from models.user import User


limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix='/api/auth', tags=['auth'])


@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user account.

    Creates a new user with the provided credentials and sends a
    verification email. Returns the created user data.

    Args:
        user_data: Registration data (username, email, password).
        db: Async database session.

    Returns:
        UserResponse: The newly created user data.

    Raises:
        HTTPException 409: If the email or username already exists.
    """
    auth_service = AuthService(db)
    try:
        user = await auth_service.register(user_data)
        # Send verification email (fire and forget - don't block registration)
        try:
            await send_verification_email(user.email, user.verification_token)
        except Exception:
            pass
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post('/login', response_model=TokenResponse)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate a user and return a JWT access token.

    Validates email and password credentials and returns a JWT token
    for subsequent authenticated requests.

    Args:
        login_data: Login credentials (email, password).
        db: Async database session.

    Returns:
        TokenResponse: JWT access token.

    Raises:
        HTTPException 401: If the email or password is invalid.
    """
    auth_service = AuthService(db)
    try:
        return await auth_service.login(login_data.email, login_data.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get('/confirm_email/{token}', response_model=UserResponse)
async def confirm_email(token: str, db: AsyncSession = Depends(get_db)):
    """Verify a user's email address using a verification token.

    Args:
        token: The email verification token from the confirmation link.
        db: Async database session.

    Returns:
        UserResponse: The updated user with verified status.

    Raises:
        HTTPException 400: If the verification token is invalid.
    """
    auth_service = AuthService(db)
    try:
        return await auth_service.verify_email(token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post('/request_email')
async def request_email(body: RequestEmail, db: AsyncSession = Depends(get_db)):
    """Request a new email verification link.

    Sends a verification email if the user exists and is not yet verified.
    Returns a generic message to prevent email enumeration.

    Args:
        body: Request containing the email address.
        db: Async database session.

    Returns:
        dict: Confirmation message.
    """
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
    """Get the profile of the currently authenticated user.

    Rate-limited to 5 requests per minute.

    Args:
        request: The incoming HTTP request (for rate limiting).
        current_user: The authenticated user from JWT token.

    Returns:
        UserResponse: The current user's profile data.
    """
    return UserResponse.model_validate(current_user)


@router.patch('/avatar', response_model=UserResponse)
async def update_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role('admin')),
    db: AsyncSession = Depends(get_db),
):
    """Update the avatar for the current user (admin only).

    Accepts an image file, uploads it to Cloudinary, and updates
    the user's avatar URL. Only users with the 'admin' role can
    access this endpoint.

    Args:
        file: The image file to upload as avatar.
        current_user: The authenticated admin user.
        db: Async database session.

    Returns:
        UserResponse: Updated user data with new avatar URL.

    Raises:
        HTTPException 400: If the file is not an image.
        HTTPException 500: If the upload or update fails.
    """
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


@router.post('/password-reset/request')
async def password_reset_request(body: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    """Request a password reset link.

    Generates a reset token and sends it via email if the user exists.
    Returns a generic message to prevent email enumeration.

    Args:
        body: Request containing the email address.
        db: Async database session.

    Returns:
        dict: Confirmation message.
    """
    auth_service = AuthService(db)
    token = await auth_service.request_password_reset(body.email)
    if token:
        try:
            await send_reset_password_email(body.email, token)
        except Exception:
            pass
    return {'message': 'If the email exists, a password reset link has been sent.'}


@router.post('/password-reset/confirm', response_model=UserResponse)
async def password_reset_confirm(body: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    """Confirm a password reset with a token and new password.

    Validates the reset token and updates the user's password.

    Args:
        body: Reset confirmation data (token and new password).
        db: Async database session.

    Returns:
        UserResponse: Updated user data.

    Raises:
        HTTPException 400: If the token is invalid or expired.
    """
    auth_service = AuthService(db)
    try:
        return await auth_service.reset_password(body.token, body.new_password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))