from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from api.schemas import UserStatus, ResetPasswordResponse
from api.deps import require_admin
from services.auth_service import auth_service
from services.banking_service import BankingService
from persistence.database import get_db
from persistence.models import UserDB
from typing import List, Optional

router = APIRouter()

@router.get("/users", response_model=List[UserStatus])
async def get_all_users(payload: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """Get all users with their auth status (admin only)"""
    users_status = []

    # Get all users from database
    users = db.query(UserDB).all()
    for user in users:
        status_info = auth_service.get_user_status(db, user.user_id)
        if status_info:
            users_status.append(UserStatus(
                user_id=user.user_id,
                name=user.name,
                role=user.role,
                locked=status_info['locked'],
                failed_attempts=status_info['failed_attempts']
            ))

    return users_status

@router.post("/users/{user_id}/lock")
async def lock_user(user_id: str, payload: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """Lock user account (admin only)"""
    success, message = auth_service.lock_user(db, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    return {"message": message}

@router.post("/users/{user_id}/unlock")
async def unlock_user(user_id: str, payload: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """Unlock user account (admin only)"""
    success, message = auth_service.unlock_user(db, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    return {"message": message}

@router.post("/users/{user_id}/reset-password", response_model=ResetPasswordResponse)
async def reset_user_password(user_id: str, payload: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """Reset user password and return temporary password (admin only)"""
    success, message, temp_password = auth_service.reset_user_password(db, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    return ResetPasswordResponse(temporary_password=temp_password)