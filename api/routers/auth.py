from fastapi import APIRouter, HTTPException, status, Depends
from api.schemas import (
    RegisterRequest, LoginRequest, LoginResponse,
    ChangePasswordRequest, UserProfile
)
from api.deps import get_current_user
from services.auth_service import auth_service
from services.banking_service import BankingService
from bank import Bank
from persistence.store import load_data
from typing import Optional

router = APIRouter()

# Global bank instance (in production, use dependency injection)
_bank: Optional[Bank] = None

def get_bank() -> Bank:
    """Get or create bank instance"""
    global _bank
    if _bank is None:
        _bank = load_data() or Bank("Secure Bank")
    return _bank

def get_banking_service() -> BankingService:
    """Get banking service instance"""
    return BankingService(get_bank())

@router.post("/register", response_model=UserProfile)
async def register(request: RegisterRequest):
    """Register a new user"""
    bank = get_bank()

    success, message, user = auth_service.register_user(
        name=request.name,
        user_id=request.user_id,
        password=request.password,
        role=request.role or "customer",
        email=request.email,
        phone=request.phone,
        bank=bank
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    assert user is not None  # Type hint for mypy

    # Create default account for new user
    banking_service = get_banking_service()
    account = banking_service.create_account(user, initial_balance=100.0)

    return UserProfile(
        name=user.get_name(),
        user_id=user.get_user_id(),
        role=user.get_role(),
        email=getattr(user, '_User__email', None),
        phone=getattr(user, '_User__phone', None)
    )

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login user and return access token"""
    success, message, token = auth_service.login_user(request.user_id, request.password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )

    assert token is not None  # Type hint for mypy

    return LoginResponse(access_token=token, token_type="bearer")

@router.post("/change-password")
async def change_password(request: ChangePasswordRequest, payload: dict = Depends(get_current_user)):
    """Change current user's password"""
    user_id = payload['user_id']

    success, message = auth_service.change_password(
        user_id=user_id,
        current_password=request.current_password,
        new_password=request.new_password
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return {"message": message}

@router.post("/logout")
async def logout(payload: dict = Depends(get_current_user)):
    """Logout current user (invalidate token)"""
    # Note: In a stateless JWT system, logout is best-effort
    # The token will naturally expire, but we can track it server-side if needed
    auth_service.logout_user(payload.get('token', ''))
    return {"message": "Logged out successfully"}