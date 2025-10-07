"""
User models for authentication and authorization.
"""
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from pydantic import EmailStr


class UserBase(SQLModel):
    """Base user model with shared fields."""
    email: str = Field(unique=True, index=True, description="User email address")
    full_name: Optional[str] = Field(default=None, description="User full name")
    is_active: bool = Field(default=True, description="Whether user account is active")
    is_verified: bool = Field(default=False, description="Whether email is verified")


class User(UserBase, table=True):
    """
    User database model.

    Stores user account information and authentication data.
    Related to subscriptions via one-to-many relationship.
    """
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str = Field(description="Bcrypt hashed password")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    # Relationships
    subscriptions: List["Subscription"] = Relationship(back_populates="user")
    api_usage: List["APIUsage"] = Relationship(back_populates="user")


class UserCreate(UserBase):
    """User creation model with plaintext password."""
    password: str = Field(min_length=8, description="User password (8+ characters)")


class UserUpdate(SQLModel):
    """User update model - all fields optional."""
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=8)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """User response model - excludes sensitive data."""
    id: int
    created_at: datetime
    has_active_subscription: bool = Field(default=False, description="Whether user has active subscription")


class Token(SQLModel):
    """JWT token response model."""
    access_token: str = Field(description="JWT access token")
    refresh_token: str = Field(description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")


class TokenPayload(SQLModel):
    """JWT token payload model."""
    sub: int = Field(description="User ID (subject)")
    exp: datetime = Field(description="Token expiration timestamp")
    type: str = Field(description="Token type (access or refresh)")


class LoginRequest(SQLModel):
    """Login request model."""
    email: str = Field(description="User email")
    password: str = Field(description="User password")
