from sqlalchemy.orm import Session
from persistence.models import UserDB, AuthDB
from core.auth import auth_system, PasswordValidator
from domain.user import User
from typing import Optional, Tuple
import datetime

class AuthService:
    """Service layer for authentication operations"""

    @staticmethod
    def register_user(db: Session, name: str, user_id: str, password: str, role: str = "customer",
                     email: Optional[str] = None, phone: Optional[str] = None) -> Tuple[bool, str, Optional[User]]:
        """Register a new user and create User record in DB"""

        # Create auth and user record via auth_system
        success, message = auth_system.create_user(
            db=db, 
            name=name, 
            user_id=user_id, 
            password=password, 
            role=role, 
            email=email, 
            phone=phone
        )
        
        if not success:
            return False, message, None

        # Return a User domain object (for compatibility if needed)
        user = User(name, user_id, role)
        if email:
            user.set_email(email)
        if phone:
            user.set_phone(phone)

        return True, "User registered successfully", user

    @staticmethod
    def login_user(db: Session, user_id: str, password: str) -> Tuple[bool, str, Optional[str]]:
        """Login user and return token"""
        success, token, message = auth_system.login(db, user_id, password)
        return success, message, token if success else None

    @staticmethod
    def change_password(db: Session, user_id: str, current_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password"""
        return auth_system.change_password(db, user_id, current_password, new_password)

    @staticmethod
    def logout_user(token: str):
        """Logout user by invalidating token"""
        auth_system.logout(token)

    @staticmethod
    def get_user_status(db: Session, user_id: str) -> Optional[dict]:
        """Get user auth status for admin"""
        user = db.query(UserDB).filter(UserDB.user_id == user_id).first()
        if not user or not user.auth:
            return None

        auth = user.auth
        return {
            'user_id': user_id,
            'role': user.role,
            'locked': auth.locked_until is not None and auth.locked_until > datetime.datetime.now(),
            'failed_attempts': auth.failed_attempts
        }

    @staticmethod
    def lock_user(db: Session, user_id: str) -> Tuple[bool, str]:
        """Lock user account (admin only)"""
        user = db.query(UserDB).filter(UserDB.user_id == user_id).first()
        if not user or not user.auth:
            return False, "User not found"

        user.auth.locked_until = datetime.datetime.now() + datetime.timedelta(hours=1)
        db.commit()
        return True, f"User {user_id} locked for 1 hour"

    @staticmethod
    def unlock_user(db: Session, user_id: str) -> Tuple[bool, str]:
        """Unlock user account (admin only)"""
        user = db.query(UserDB).filter(UserDB.user_id == user_id).first()
        if not user or not user.auth:
            return False, "User not found"

        user.auth.locked_until = None
        user.auth.failed_attempts = 0
        db.commit()
        return True, f"User {user_id} unlocked"

    @staticmethod
    def reset_user_password(db: Session, user_id: str) -> Tuple[bool, str, Optional[str]]:
        """Reset user password and return temporary password (admin only)"""
        user = db.query(UserDB).filter(UserDB.user_id == user_id).first()
        if not user or not user.auth:
            return False, "User not found", None

        # Generate temporary password
        temp_password = "Temp123!"  # In production, generate secure random

        # Update password hash
        new_hash = auth_system.hash_password(temp_password)
        user.auth.password_hash = new_hash

        # Reset failed attempts and unlock
        user.auth.failed_attempts = 0
        user.auth.locked_until = None
        db.commit()

        return True, f"Password reset for {user_id}", temp_password

# Global instance
auth_service = AuthService()
