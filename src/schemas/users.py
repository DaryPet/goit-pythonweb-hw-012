from pydantic import BaseModel, Field, EmailStr, ConfigDict
from enum import Enum


class UserRole(str, Enum):
    """
    Enum for user roles.

    Attributes:
        USER: Regular user role.
        ADMIN: Administrator role.
    """

    USER = "USER"
    ADMIN = "ADMIN"


class UserCreate(BaseModel):
    """
    Pydantic model for creating a new user (registration).
    """

    email: EmailStr
    """User's email address."""
    password: str = Field(min_length=6)
    """User's password, minimum 6 characters."""
    role: UserRole = Field(default=UserRole.USER)
    """User role, default is 'user'."""


class UserResponse(BaseModel):
    """
    Pydantic model for the API response for a user.
    Excludes sensitive information like the password.
    """

    id: int
    """Unique identifier of the user."""
    email: EmailStr
    """User's email address."""
    avatar_url: str | None
    """URL of user's avatar."""
    role: UserRole
    """User role."""
    is_verified: bool
    """Flag indicating if user's email is verified."""

    model_config = ConfigDict(from_attributes=True)


class TokenModel(BaseModel):
    """
    Pydantic model for the JWT token response.
    """

    access_token: str
    """JWT access token."""
    refresh_token: str
    """JWT refresh token."""
    token_type: str = "bearer"
    """Type of the token, default 'bearer'."""


class PasswordResetRequest(BaseModel):
    """
    Pydantic model for password reset request.
    """

    email: EmailStr
    """User's email address for password reset."""


class PasswordResetConfirm(BaseModel):
    """
    Pydantic model for password reset confirmation.
    """

    token: str
    """Password reset token received via email."""
    new_password: str = Field(min_length=6)
    """New password, minimum 6 characters."""
