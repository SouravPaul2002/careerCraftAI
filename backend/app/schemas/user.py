from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    """Data required when a new user registers."""

    email: EmailStr
    full_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=6, max_length=72)


class UserLogin(BaseModel):
    """Data required when a user logs in."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Safe user data returned by the API (never includes password)."""

    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime

    # Allows Pydantic to read values directly from a SQLAlchemy User object
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """JWT access token and user details returned after login."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
