from fastapi import APIRouter, HTTPException, status, Depends
from api.schemas import UserStatus, ResetPasswordResponse
from api.deps import require_admin
from services.auth_service import auth_service
from services.banking_service import BankingService
from auth import auth_system
from bank import Bank
from persistence.store import load_data
from typing import List, Optional

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

@router.get("/users", response_model=List[UserStatus])
async def get_all_users(payload: dict = Depends(require_admin)):
    """Get all users with their auth status (admin only)"""
    users_status = []

    # Get all auth users
    for user_id in auth_system.user_credentials.keys():
        status_info = auth_service.get_user_status(user_id)
        if status_info:
            # Try to find user name from bank accounts
            bank = get_bank()
            user_name = user_id.capitalize()  # Default
            for account in bank.get_accounts():
                if account.get_user().get_user_id() == user_id:
                    user_name = account.get_user().get_name()
                    break

            users_status.append(UserStatus(
                user_id=user_id,
                name=user_name,
                role=status_info['role'],
                locked=status_info['locked'],
                failed_attempts=status_info['failed_attempts']
            ))

    return users_status

@router.post("/users/{user_id}/lock")
async def lock_user(user_id: str, payload: dict = Depends(require_admin)):
    """Lock user account (admin only)"""
    success, message = auth_service.lock_user(user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    return {"message": message}

@router.post("/users/{user_id}/unlock")
async def unlock_user(user_id: str, payload: dict = Depends(require_admin)):
    """Unlock user account (admin only)"""
    success, message = auth_service.unlock_user(user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    return {"message": message}

@router.post("/users/{user_id}/reset-password", response_model=ResetPasswordResponse)
async def reset_user_password(user_id: str, payload: dict = Depends(require_admin)):
    """Reset user password and return temporary password (admin only)"""
    success, message, temp_password = auth_service.reset_user_password(user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    assert temp_password is not None  # Type hint for mypy

    return ResetPasswordResponse(temporary_password=temp_password)