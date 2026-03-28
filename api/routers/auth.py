from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from api.schemas import (
    RegisterRequest, LoginRequest, LoginResponse,
    ChangePasswordRequest, UserProfile
)
from api.deps import get_current_user
from services.auth_service import auth_service
from services.banking_service import BankingService
from persistence.database import get_db
from typing import Optional

router = APIRouter()

@router.post("/register", response_model=UserProfile)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user"""
    success, message, user = auth_service.register_user(
        db=db,
        name=request.name,
        user_id=request.user_id,
        password=request.password,
        role=request.role or "customer",
        email=request.email,
        phone=request.phone
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    # Create default account for new user
    banking_service = BankingService(db)
    account = banking_service.create_account(request.user_id, initial_balance=100.0)

    return UserProfile(
        name=request.name,
        user_id=request.user_id,
        role=request.role or "customer",
        email=request.email,
        phone=request.phone
    )

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login user and return access token"""
    success, message, token = auth_service.login_user(db, request.user_id, request.password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )

    return LoginResponse(access_token=token, token_type="bearer")

@router.post("/change-password")
async def change_password(request: ChangePasswordRequest, payload: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Change current user's password"""
    user_id = payload['user_id']

    success, message = auth_service.change_password(
        db=db,
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
    auth_service.logout_user(payload.get('token', ''))
    return {"message": "Logged out successfully"}