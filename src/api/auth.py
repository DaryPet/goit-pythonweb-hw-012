from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import (
    OAuth2PasswordRequestForm,
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request

from src.database.db import get_db
from src.repository import users as repository_users
from src.schemas.users import UserCreate, UserResponse, TokenModel
from src.security.passwords import get_password_hash, verify_password
from src.security.tokens import create_access_token, create_refresh_token
from src.services.auth import verify_refresh_token, get_email_from_token
from src.services.email import send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


@router.post(
    "/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def signup(
    body: UserCreate, request: Request, db: AsyncSession = Depends(get_db)
):
    """
    User sighnup.
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
    User authentification
    Verify email (in username field) and password.
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
):
    """
    Refresh access_token using a refresh_token.
    Pass the refresh token in the Authorization header: Bearer <token>
    """
    token = credentials.credentials
    user = await verify_refresh_token(token, db)
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
    Confirm user's email address using verification token.

    Extracts email from the verification token, finds the user in database,
    and marks their email as verified. If user is already verified or token
    is invalid, returns appropriate error message.

    :param token: Email verification token received by user
    :param db: Database session dependency
    :return: Success or error message
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
