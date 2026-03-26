from auth import auth_system, PasswordValidator
from user import User
from bank import Bank
from persistence.store import save_data
from typing import Optional, Tuple

class AuthService:
    """Service layer for authentication operations"""

    @staticmethod
    def register_user(name: str, user_id: str, password: str, role: str = "customer",
                     email: Optional[str] = None, phone: Optional[str] = None,
                     bank: Optional[Bank] = None) -> Tuple[bool, str, Optional[User]]:
        """Register a new user and create User object"""

        # Create auth credential
        success, message = auth_system.create_user(user_id, password)
        if not success:
            return False, message, None

        # Update role in auth system
        if user_id in auth_system.user_credentials:
            auth_system.user_credentials[user_id]['role'] = role

        # Create User object
        user = User(name, user_id, role)
        if email:
            user.set_email(email)
        if phone:
            user.set_phone(phone)

        # Save to persistence if bank provided
        if bank is not None:
            save_data(bank)

        return True, "User registered successfully", user

    @staticmethod
    def login_user(user_id: str, password: str) -> Tuple[bool, str, Optional[str]]:
        """Login user and return token"""
        success, token, message = auth_system.login(user_id, password)
        return success, message, token if success else None

    @staticmethod
    def change_password(user_id: str, current_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password"""
        return auth_system.change_password(user_id, current_password, new_password)

    @staticmethod
    def logout_user(token: str):
        """Logout user by invalidating token"""
        auth_system.logout(token)

    @staticmethod
    def get_user_status(user_id: str) -> Optional[dict]:
        """Get user auth status for admin"""
        if user_id not in auth_system.user_credentials:
            return None

        creds = auth_system.user_credentials[user_id]
        return {
            'user_id': user_id,
            'role': creds.get('role', 'customer'),
            'locked': creds.get('locked_until') is not None,
            'failed_attempts': creds.get('failed_attempts', 0)
        }

    @staticmethod
    def lock_user(user_id: str) -> Tuple[bool, str]:
        """Lock user account (admin only)"""
        if user_id not in auth_system.user_credentials:
            return False, "User not found"

        import datetime
        auth_system.user_credentials[user_id]['locked_until'] = datetime.datetime.now() + datetime.timedelta(hours=1)
        return True, f"User {user_id} locked for 1 hour"

    @staticmethod
    def unlock_user(user_id: str) -> Tuple[bool, str]:
        """Unlock user account (admin only)"""
        if user_id not in auth_system.user_credentials:
            return False, "User not found"

        auth_system.user_credentials[user_id]['locked_until'] = None
        auth_system.user_credentials[user_id]['failed_attempts'] = 0
        return True, f"User {user_id} unlocked"

    @staticmethod
    def reset_user_password(user_id: str) -> Tuple[bool, str, Optional[str]]:
        """Reset user password and return temporary password (admin only)"""
        if user_id not in auth_system.user_credentials:
            return False, "User not found", None

        # Generate temporary password
        temp_password = "Temp123!"  # In production, generate secure random

        # Update password hash
        from auth import AuthSystem
        auth_system_instance = AuthSystem()
        new_hash = auth_system_instance.hash_password(temp_password)
        auth_system.user_credentials[user_id]['password_hash'] = new_hash

        # Reset failed attempts and unlock
        auth_system.user_credentials[user_id]['failed_attempts'] = 0
        auth_system.user_credentials[user_id]['locked_until'] = None

        return True, f"Password reset for {user_id}", temp_password

# Global instance
auth_service = AuthService()