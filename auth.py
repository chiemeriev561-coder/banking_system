import bcrypt
import jwt
import datetime
import re
from typing import Tuple, Dict, Any, Optional

class PasswordValidator:
    """Simple password validator"""
    @staticmethod
    def validate(password: str) -> Tuple[bool, str]:
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r"\d", password):
            return False, "Password must contain at least one number"
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain at least one special character"
        return True, "Password is strong"

class AuthSystem:
    """Authentication system using JWT and bcrypt"""
    def __init__(self):
        self.user_credentials: Dict[str, Dict[str, Any]] = {}
        self.active_sessions: Dict[str, Dict[str, str]] = {}
        self.SECRET_KEY = "super-secret-bank-key-123" # In production, use environment variable
    
    def hash_password(self, password: str) -> bytes:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    def verify_password(self, password: str, hashed: bytes) -> bool:
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed)
        except:
            return False
    
    def create_user(self, user_id: str, password: str, require_strong_password: bool = True) -> Tuple[bool, str]:
        if user_id in self.user_credentials:
            return False, "User already exists"
        
        if require_strong_password:
            is_valid, message = PasswordValidator.validate(password)
            if not is_valid:
                return False, f"Weak password: {message}"
        
        password_hash = self.hash_password(password)
        self.user_credentials[user_id] = {
            'password_hash': password_hash,
            'failed_attempts': 0,
            'locked_until': None,
            'role': 'customer' # Default role
        }
        return True, "User created successfully"
    
    def login(self, user_id: str, password: str) -> Tuple[bool, str, str]:
        if user_id not in self.user_credentials:
            return False, "", "Invalid credentials"
        
        credentials = self.user_credentials[user_id]
        
        # Check if account is locked
        locked_until = credentials.get('locked_until')
        if isinstance(locked_until, datetime.datetime) and locked_until > datetime.datetime.now():
            remaining = (locked_until - datetime.datetime.now()).seconds // 60
            return False, "", f"Account locked. Try again in {remaining} minutes"
        
        # Verify password
        password_hash = credentials.get('password_hash')
        if isinstance(password_hash, bytes) and self.verify_password(password, password_hash):
            # Successful login - reset failed attempts and clear any lock
            credentials['failed_attempts'] = 0
            credentials['locked_until'] = None
            
            # Create JWT token
            token = jwt.encode(
                {
                    'user_id': user_id, 
                    'role': str(credentials.get('role', 'customer')),
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
                },
                self.SECRET_KEY,
                algorithm='HS256'
            )
            self.active_sessions[token] = {'user_id': user_id}
            return True, token, "Login successful"
        else:
            # Failed login
            failed_attempts = int(credentials.get('failed_attempts', 0)) + 1
            credentials['failed_attempts'] = failed_attempts
            
            if failed_attempts >= 5:
                credentials['locked_until'] = datetime.datetime.now() + datetime.timedelta(minutes=15)
                return False, "", "Account locked due to 5 failed attempts"
            
            remaining = 5 - failed_attempts
            return False, "", f"Invalid password. {remaining} attempts remaining"

    def logout(self, token: str):
        self.active_sessions.pop(token, None)

    def change_password(self, user_id: str, old_pass: str, new_pass: str) -> Tuple[bool, str]:
        if user_id not in self.user_credentials:
            return False, "User not found"
        
        if not self.verify_password(old_pass, self.user_credentials[user_id]['password_hash']):
            return False, "Incorrect current password"
        
        is_valid, message = PasswordValidator.validate(new_pass)
        if not is_valid:
            return False, message
            
        self.user_credentials[user_id]['password_hash'] = self.hash_password(new_pass)
        return True, "Password changed successfully"

# Global singleton instance
auth_system = AuthSystem()

def require_auth(token: str) -> Tuple[bool, Dict[str, Any], str]:
    """Verify JWT token"""
    if not token:
        return False, {}, "No token provided"
    
    try:
        payload = jwt.decode(token, auth_system.SECRET_KEY, algorithms=['HS256'])
        return True, payload, "Authorized"
    except jwt.ExpiredSignatureError:
        return False, {}, "Token has expired"
    except jwt.InvalidTokenError:
        return False, {}, "Invalid token"

def require_role(token: str, required_role: str) -> Tuple[bool, Dict[str, Any], str]:
    """Verify JWT token and role"""
    is_auth, payload, message = require_auth(token)
    if not is_auth:
        return False, {}, message
    
    user_role = payload.get('role', 'customer')
    
    # Simple hierarchy: admin > manager > teller > customer
    role_hierarchy = {'admin': 4, 'manager': 3, 'teller': 2, 'customer': 1}
    
    if role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0):
        return True, payload, "Authorized"
    else:
        return False, {}, f"Required role: {required_role}. Current role: {user_role}"
