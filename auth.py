from sqlalchemy.orm import Session
from persistence.models import UserDB, AuthDB
from persistence.database import SessionLocal
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
        self.SECRET_KEY = "super-secret-bank-key-123" # In production, use environment variable
    
    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except:
            return False
    
    def create_user(self, db: Session, name: str, user_id: str, password: str, role: str = "customer", 
                    email: Optional[str] = None, phone: Optional[str] = None, 
                    require_strong_password: bool = True) -> Tuple[bool, str]:
        
        # Check if user already exists
        existing_user = db.query(UserDB).filter(UserDB.user_id == user_id).first()
        if existing_user:
            return False, "User already exists"
        
        if require_strong_password:
            is_valid, message = PasswordValidator.validate(password)
            if not is_valid:
                return False, f"Weak password: {message}"
        
        password_hash = self.hash_password(password)
        
        # Create user record
        new_user = UserDB(
            user_id=user_id,
            name=name,
            role=role,
            email=email,
            phone=phone
        )
        db.add(new_user)
        db.flush() # Get user id for auth record
        
        # Create auth record
        new_auth = AuthDB(
            user_id=new_user.id,
            password_hash=password_hash
        )
        db.add(new_auth)
        db.commit()
        
        return True, "User created successfully"
    
    def login(self, db: Session, user_id: str, password: str) -> Tuple[bool, str, str]:
        user = db.query(UserDB).filter(UserDB.user_id == user_id).first()
        if not user or not user.auth:
            return False, "", "Invalid credentials"
        
        auth = user.auth
        
        # Check if account is locked
        if auth.locked_until and auth.locked_until > datetime.datetime.now():
            remaining = (auth.locked_until - datetime.datetime.now()).seconds // 60
            return False, "", f"Account locked. Try again in {remaining} minutes"
        
        # Verify password
        if self.verify_password(password, auth.password_hash):
            # Successful login - reset failed attempts and clear any lock
            auth.failed_attempts = 0
            auth.locked_until = None
            db.commit()
            
            # Create JWT token
            token = jwt.encode(
                {
                    'user_id': user_id, 
                    'role': str(user.role),
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
                },
                self.SECRET_KEY,
                algorithm='HS256'
            )
            return True, token, "Login successful"
        else:
            # Failed login
            auth.failed_attempts += 1
            
            if auth.failed_attempts >= 5:
                auth.locked_until = datetime.datetime.now() + datetime.timedelta(minutes=15)
                db.commit()
                return False, "", "Account locked due to 5 failed attempts"
            
            db.commit()
            remaining = 5 - auth.failed_attempts
            return False, "", f"Invalid password. {remaining} attempts remaining"

    def logout(self, token: str):
        # JWT logout is usually handled client side or with a distributed blacklist
        # For simplicity, we'll just ignore it here since payload check is enough
        pass

    def change_password(self, db: Session, user_id: str, old_pass: str, new_pass: str) -> Tuple[bool, str]:
        user = db.query(UserDB).filter(UserDB.user_id == user_id).first()
        if not user or not user.auth:
            return False, "User not found"
        
        if not self.verify_password(old_pass, user.auth.password_hash):
            return False, "Incorrect current password"
        
        is_valid, message = PasswordValidator.validate(new_pass)
        if not is_valid:
            return False, message
            
        user.auth.password_hash = self.hash_password(new_pass)
        db.commit()
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
