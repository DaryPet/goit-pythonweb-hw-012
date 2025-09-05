from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserCreate(BaseModel):
    """
    Pydantic model for creating a new user (registration).
    """

    email: EmailStr
    password: str = Field(min_length=6)


class UserResponse(BaseModel):
    """
    Pydantic model for the API response for a user.
    Excludes sensitive information like the password.
    """

    id: int
    email: EmailStr
    avatar_url: str | None

    model_config = ConfigDict(from_attributes=True)


class TokenModel(BaseModel):
    """
    Pydantic model for the JWT token response.
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
