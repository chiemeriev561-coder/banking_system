from typing import Optional

class User:
    def __init__(self, name: str, user_id: str, role: str = "customer"):
        self.__name = name
        self.__user_id = user_id
        self.__role = role
        self.__email: Optional[str] = None
        self.__phone: Optional[str] = None
    
    def get_name(self) -> str:
        return self.__name
    
    def get_user_id(self) -> str:
        return self.__user_id
    
    def get_role(self) -> str:
        return self.__role
    
    def set_email(self, email: str):
        self.__email = email
    
    def set_phone(self, phone: str):
        self.__phone = phone
    
    def has_permission(self, action: str) -> bool:
        permissions = {
            "customer": ["view_own_account", "deposit_own", "withdraw_own"],
            "teller": ["view_any_account", "deposit_any", "withdraw_any", "create_account"],
            "manager": ["view_any_account", "deposit_any", "withdraw_any", "create_account", "delete_account"],
            "admin": ["all"]
        }
        
        if self.__role == "admin":
            return True
        
        role_perms = permissions.get(self.__role, [])
        return action in role_perms
    
    def can_access_account(self, account_user_id: str) -> bool:
        if self.__role in ["admin", "manager", "teller"]:
            return True
        return self.__user_id == account_user_id
