"""
Authentication endpoints: register, login.
"""
from fastapi import APIRouter, status
from sqlmodel import select

from app.api.deps import DBSession
from app.models.user import User, UserRole
from app.schemas.user import UserRegister, UserLogin, TokenResponse, UserResponse
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.exceptions import ConflictException, UnauthorizedException


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, session: DBSession):
    """
    Register a new user.
    
    - Creates user account with hashed password
    - Default role: CUSTOMER
    - Returns JWT token for immediate authentication
    """
    # Check if email already exists
    query = select(User).where(User.email == user_data.email)
    result = session.exec(query)
    existing_user = result.one_or_none()
    
    if existing_user:
        raise ConflictException(detail="Email already registered")
    
    # Create new user with CUSTOMER role
    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        is_active=True,
        role=UserRole.CUSTOMER
    )
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Generate access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, session: DBSession):
    """
    Authenticate user and return JWT token.
    
    - Validates email and password
    - Returns JWT token on success
    """
    # Find user by email
    query = select(User).where(User.email == credentials.email)
    result = session.exec(query)
    user = result.one_or_none()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise UnauthorizedException(detail="Incorrect email or password")
    
    if not user.is_active:
        raise UnauthorizedException(detail="Account is inactive")
    
    # Generate access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )