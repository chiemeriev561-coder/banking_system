from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any
from auth import require_auth, require_role as auth_require_role

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Dependency to get current authenticated user payload"""
    token = credentials.credentials
    is_auth, payload, message = require_auth(token)

    if not is_auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload

def require_role(required_role: str):
    """Factory function to create role-based dependencies"""
    def role_dependency(payload: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        # Since we already validated the token in get_current_user,
        # we just need to check the role
        user_role = payload.get('role', 'customer')

        # Simple hierarchy: admin > manager > teller > customer
        role_hierarchy = {'admin': 4, 'manager': 3, 'teller': 2, 'customer': 1}

        if role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0):
            return payload
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {required_role}. Current role: {user_role}"
            )

    return role_dependency

# Pre-defined role dependencies
require_admin = require_role("admin")
require_manager = require_role("manager")
require_teller = require_role("teller")