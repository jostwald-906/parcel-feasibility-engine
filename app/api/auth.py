"""
Authentication API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import Session, select
from datetime import datetime

from app.models.user import (
    User,
    UserCreate,
    UserUpdate,
    UserResponse,
    Token,
    LoginRequest,
)
from app.models.subscription import Subscription, SubscriptionStatus, SubscriptionPlan
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    validate_password_strength,
)
from app.core.dependencies import get_current_user, security, get_session
from app.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    session: Session = Depends(get_session)
) -> UserResponse:
    """
    Register a new user account.

    Args:
        user_data: User registration data (email, password, full_name)
        session: Database session

    Returns:
        Created user object (without password)

    Raises:
        HTTPException: If email already registered or password too weak
    """
    # Check if email already exists
    statement = select(User).where(User.email == user_data.email)
    existing_user = session.exec(statement).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Validate password strength
    is_valid, error_message = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

    # Create user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        is_active=True,
        is_verified=False  # Email verification can be added later
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    # Create free tier subscription for new user
    subscription = Subscription(
        user_id=db_user.id,
        stripe_customer_id=f"temp_{db_user.id}",  # Will be updated when Stripe customer is created
        status=SubscriptionStatus.INCOMPLETE,
        plan=SubscriptionPlan.FREE
    )

    session.add(subscription)
    session.commit()

    logger.info(f"New user registered: {db_user.email}", extra={"user_id": db_user.id})

    return UserResponse(
        id=db_user.id,
        email=db_user.email,
        full_name=db_user.full_name,
        is_active=db_user.is_active,
        is_verified=db_user.is_verified,
        created_at=db_user.created_at,
        has_active_subscription=False
    )


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    session: Session = Depends(get_session)
) -> Token:
    """
    Authenticate user and return JWT tokens.

    Args:
        login_data: User login credentials (email, password)
        session: Database session

    Returns:
        JWT access and refresh tokens

    Raises:
        HTTPException: If credentials are invalid
    """
    # Get user by email
    statement = select(User).where(User.email == login_data.email)
    user = session.exec(statement).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support."
        )

    # Create tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    logger.info(f"User logged in: {user.email}", extra={"user_id": user.id})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
) -> Token:
    """
    Refresh access token using refresh token.

    Args:
        credentials: HTTP Bearer refresh token
        session: Database session

    Returns:
        New JWT access and refresh tokens

    Raises:
        HTTPException: If refresh token is invalid
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Verify refresh token
    token_payload = verify_token(token, token_type="refresh")
    if token_payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user
    user = session.get(User, token_payload.sub)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new tokens
    access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout user (client should delete tokens).

    Args:
        current_user: Current authenticated user

    Returns:
        Success message

    Note:
        JWT tokens are stateless, so logout is handled client-side by deleting tokens.
        For token blacklisting, implement a token revocation list in the database.
    """
    logger.info(f"User logged out: {current_user.email}", extra={"user_id": current_user.id})

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> UserResponse:
    """
    Get current user profile information.

    Args:
        current_user: Current authenticated user
        session: Database session

    Returns:
        User profile data including subscription status
    """
    # Check if user has active subscription
    statement = select(Subscription).where(
        Subscription.user_id == current_user.id
    ).order_by(Subscription.created_at.desc())

    subscription = session.exec(statement).first()

    has_active_subscription = False
    if subscription:
        has_active_subscription = subscription.status in [
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING
        ]

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        has_active_subscription=has_active_subscription
    )


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> UserResponse:
    """
    Update current user profile.

    Args:
        user_update: Fields to update (email, full_name, password)
        current_user: Current authenticated user
        session: Database session

    Returns:
        Updated user profile

    Raises:
        HTTPException: If email already taken or password invalid
    """
    # Check if email is being updated and if it's already taken
    if user_update.email and user_update.email != current_user.email:
        statement = select(User).where(User.email == user_update.email)
        existing_user = session.exec(statement).first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        current_user.email = user_update.email
        current_user.is_verified = False  # Re-verify email

    # Update full name
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name

    # Update password
    if user_update.password:
        is_valid, error_message = validate_password_strength(user_update.password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )

        current_user.hashed_password = get_password_hash(user_update.password)

    # Update is_active if provided
    if user_update.is_active is not None:
        current_user.is_active = user_update.is_active

    # Update timestamp
    current_user.updated_at = datetime.utcnow()

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    logger.info(f"User profile updated: {current_user.email}", extra={"user_id": current_user.id})

    # Check subscription status
    statement = select(Subscription).where(
        Subscription.user_id == current_user.id
    ).order_by(Subscription.created_at.desc())

    subscription = session.exec(statement).first()

    has_active_subscription = False
    if subscription:
        has_active_subscription = subscription.status in [
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING
        ]

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        has_active_subscription=has_active_subscription
    )
