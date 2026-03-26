from fastapi import APIRouter, HTTPException, status, Depends
from api.schemas import (
    UserProfile, AccountSummary, AccountDetail,
    DepositWithdrawRequest, Transaction
)
from api.deps import get_current_user
from services.banking_service import BankingService
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

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(payload: dict = Depends(get_current_user)):
    """Get current user profile"""
    # In a full implementation, you'd fetch user details from database
    # For now, return basic info from token
    return UserProfile(
        name=payload.get('user_id', '').capitalize(),  # Placeholder
        user_id=payload['user_id'],
        role=payload.get('role', 'customer'),
        email=None,  # Would come from user store
        phone=None   # Would come from user store
    )

@router.get("/accounts", response_model=List[AccountSummary])
async def get_accounts(payload: dict = Depends(get_current_user)):
    """Get accounts accessible to current user"""
    banking_service = get_banking_service()
    user_id = payload['user_id']
    user_role = payload.get('role', 'customer')

    accounts = banking_service.get_user_accounts(user_id, user_role)

    return [
        AccountSummary(
            account_number=acc.get_account_number(),
            balance=acc.get_balance(),
            user_id=acc.get_user().get_user_id()
        )
        for acc in accounts
    ]

@router.get("/accounts/{account_number}", response_model=AccountDetail)
async def get_account_detail(account_number: str, payload: dict = Depends(get_current_user)):
    """Get detailed account information"""
    banking_service = get_banking_service()
    user_id = payload['user_id']
    user_role = payload.get('role', 'customer')

    account = banking_service.get_account_detail(account_number, user_id, user_role)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found or access denied"
        )

    transactions = [
        Transaction(
            type=txn['type'],
            amount=txn['amount'],
            balance_after=txn['balance_after']
        )
        for txn in account.get_transactions()[-10:]  # Last 10 transactions
    ]

    return AccountDetail(
        account_number=account.get_account_number(),
        balance=account.get_balance(),
        user_id=account.get_user().get_user_id(),
        user_name=account.get_user().get_name(),
        transactions=transactions
    )

@router.post("/accounts/{account_number}/deposit")
async def deposit_to_account(
    account_number: str,
    request: DepositWithdrawRequest,
    payload: dict = Depends(get_current_user)
):
    """Deposit money to account"""
    banking_service = get_banking_service()
    user_id = payload['user_id']
    user_role = payload.get('role', 'customer')

    success, message, new_balance = banking_service.deposit_to_account(
        account_number, request.amount, user_id, user_role
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return {
        "message": message,
        "new_balance": new_balance
    }

@router.post("/accounts/{account_number}/withdraw")
async def withdraw_from_account(
    account_number: str,
    request: DepositWithdrawRequest,
    payload: dict = Depends(get_current_user)
):
    """Withdraw money from account"""
    banking_service = get_banking_service()
    user_id = payload['user_id']
    user_role = payload.get('role', 'customer')

    success, message, new_balance = banking_service.withdraw_from_account(
        account_number, request.amount, user_id, user_role
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return {
        "message": message,
        "new_balance": new_balance
    }

@router.get("/accounts/{account_number}/statement", response_model=List[Transaction])
async def get_account_statement(
    account_number: str,
    limit: int = 10,
    payload: dict = Depends(get_current_user)
):
    """Get account transaction statement"""
    banking_service = get_banking_service()
    user_id = payload['user_id']
    user_role = payload.get('role', 'customer')

    transactions = banking_service.get_account_statement(
        account_number, user_id, user_role, limit
    )

    if transactions is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found or access denied"
        )

    return [
        Transaction(
            type=txn['type'],
            amount=txn['amount'],
            balance_after=txn['balance_after']
        )
        for txn in transactions
    ]