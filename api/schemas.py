from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from decimal import Decimal

# Auth schemas
class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    user_id: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=8)
    role: Optional[str] = Field("customer", pattern="^(customer|teller|manager|admin)$")
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)

class LoginRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

# User/Account schemas
class UserProfile(BaseModel):
    name: str
    user_id: str
    role: str
    email: Optional[str]
    phone: Optional[str]

class AccountSummary(BaseModel):
    account_number: str
    balance: float
    user_id: str

class Transaction(BaseModel):
    type: str
    amount: float
    balance_after: float

class AccountDetail(BaseModel):
    account_number: str
    balance: float
    user_id: str
    user_name: str
    transactions: List[Transaction]

class DepositWithdrawRequest(BaseModel):
    amount: float = Field(..., gt=0)

# Admin schemas
class UserStatus(BaseModel):
    user_id: str
    name: str
    role: str
    locked: bool
    failed_attempts: int

class ResetPasswordResponse(BaseModel):
    temporary_password: str

# System schemas
class SystemSnapshot(BaseModel):
    bank_name: str
    total_users: int
    total_accounts: int
    total_balance: float
    auth_users: int

# Error schemas
class ErrorResponse(BaseModel):
    detail: str