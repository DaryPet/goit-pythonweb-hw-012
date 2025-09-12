from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import (
    OAuth2PasswordRequestForm,
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
from redis.asyncio import Redis
from src.services.redis_service import get_redis_client

from src.database.db import get_db
from src.repository import users as repository_users
from src.schemas.users import (
    UserCreate,
    UserResponse,
    TokenModel,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from src.security.passwords import get_password_hash, verify_password
from src.security.tokens import (
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
)
from src.services.auth import (
    verify_refresh_token,
    get_email_from_token,
    verify_password_reset_token,
)
from src.services.email import send_verification_email, send_password_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


@router.post(
    "/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def signup(
    body: UserCreate, request: Request, db: AsyncSession = Depends(get_db)
):
    """
    Creates a new user.

    Args:
        body (UserCreate): The user data to be created.
        request (Request): The incoming request object.
        db (AsyncSession, optional): The database session. Defaults to Depends(get_db).

    Raises:
        HTTPException: If a user with the same email already exists.

    Returns:
        UserResponse: The newly created user object.
    """
    existing_user = await repository_users.get_user_by_email(body.email, db)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    hashed_password = get_password_hash(body.password)
    new_user = await repository_users.create_user(body, hashed_password, db)

    await send_verification_email(new_user.email, new_user.email, str(request.base_url))

    return new_user


@router.post("/login", response_model=TokenModel)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """
    Authenticates a user and provides access and refresh tokens.

    Args:
        form_data (OAuth2PasswordRequestForm, optional): The login credentials. Defaults to Depends().
        db (AsyncSession, optional): The database session. Defaults to Depends(get_db).

    Raises:
        HTTPException: If credentials are incorrect or the user's email is not verified.

    Returns:
        TokenModel: A model containing the access and refresh tokens.
    """
    user = await repository_users.get_user_by_email(form_data.username, db)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your email is not verified. Please check your mailbox.",
        )

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    await repository_users.update_refresh_token(user, refresh_token, db)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh_token", response_model=TokenModel)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
):
    """
    Refreshes the access token using a valid refresh token.

    Args:
        credentials (HTTPAuthorizationCredentials, optional): The refresh token. Defaults to Depends(security).
        db (AsyncSession, optional): The database session. Defaults to Depends(get_db).
        redis (Redis, optional): The Redis client. Defaults to Depends(get_redis_client).

    Raises:
        HTTPException: If the refresh token is invalid.

    Returns:
        TokenModel: A model with new access and refresh tokens.
    """
    token = credentials.credentials
    user = await verify_refresh_token(token, db, redis)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    new_access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)
    await repository_users.update_refresh_token(user, new_refresh_token, db)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Confirms a user's email address using a verification token.

    Args:
        token (str): The email verification token.
        db (AsyncSession, optional): The database session. Defaults to Depends(get_db).

    Raises:
        HTTPException: If the token is invalid or user is not found.

    Returns:
        dict: A success or status message.
    """
    email = await get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.is_verified:
        return {"message": "Your email is already confirmed"}

    await repository_users.verify_user(user, db)
    return {"message": "Email successfully confirmed"}


@router.post("/password-reset-request", status_code=status.HTTP_200_OK)
async def password_reset_request(
    body: PasswordResetRequest, request: Request, db: AsyncSession = Depends(get_db)
):
    """
    Sends a password reset email to a user if their email exists in the database.

    Args:
        body (PasswordResetRequest): The request body containing the user's email.
        request (Request): The incoming request object.
        db (AsyncSession, optional): The database session. Defaults to Depends(get_db).

    Returns:
        dict: A message indicating that password reset instructions have been sent.
    """
    user = await repository_users.get_user_by_email(body.email, db)
    if user:
        reset_token = create_password_reset_token(user.email)
        await send_password_reset_email(
            user.email, user.email, str(request.base_url), reset_token
        )

    return {"message": "If email exists, password reset instructions will be sent"}


@router.post("/password-reset-confirm", status_code=status.HTTP_200_OK)
async def password_reset_confirm(
    body: PasswordResetConfirm, db: AsyncSession = Depends(get_db)
):
    """
    Resets the user's password with a new one using a valid reset token.

    Args:
        body (PasswordResetConfirm): The request body containing the reset token and new password.
        db (AsyncSession, optional): The database session. Defaults to Depends(get_db).

    Raises:
        HTTPException: If the reset token is invalid.

    Returns:
        dict: A message confirming that the password has been reset.
    """
    email = await verify_password_reset_token(body.token)
    user = await repository_users.get_user_by_email(email, db)

    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    hashed_password = get_password_hash(body.new_password)
    user.password_hash = hashed_password
    await db.commit()

    return {"message": "Password successfully reset"}
