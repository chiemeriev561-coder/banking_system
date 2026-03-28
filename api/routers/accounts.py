from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from api.schemas import (
    UserProfile, AccountSummary, AccountDetail,
    DepositWithdrawRequest, Transaction
)
from api.deps import get_current_user
from services.banking_service import BankingService
from persistence.database import get_db
from persistence.models import UserDB
from typing import List, Optional

router = APIRouter()

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(payload: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user profile"""
    user_id = payload['user_id']
    user = db.query(UserDB).filter(UserDB.user_id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserProfile(
        name=user.name,
        user_id=user.user_id,
        role=user.role,
        email=user.email,
        phone=user.phone
    )

@router.get("/accounts", response_model=List[AccountSummary])
async def get_accounts(payload: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get accounts accessible to current user"""
    banking_service = BankingService(db)
    user_id = payload['user_id']
    user_role = payload.get('role', 'customer')

    accounts = banking_service.get_user_accounts(user_id, user_role)

    return [
        AccountSummary(
            account_number=acc.account_number,
            balance=acc.balance,
            user_id=acc.owner.user_id
        )
        for acc in accounts
    ]

@router.get("/accounts/{account_number}", response_model=AccountDetail)
async def get_account_detail(account_number: str, payload: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get detailed account information"""
    banking_service = BankingService(db)
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
            type=txn.type,
            amount=txn.amount,
            balance_after=txn.balance_after,
            timestamp=txn.timestamp.isoformat()
        )
        for txn in account.transactions[-10:]  # Last 10 transactions
    ]

    return AccountDetail(
        account_number=account.account_number,
        balance=account.balance,
        user_id=account.owner.user_id,
        user_name=account.owner.name,
        transactions=transactions
    )

@router.post("/accounts/{account_number}/deposit")
async def deposit_to_account(
    account_number: str,
    request: DepositWithdrawRequest,
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deposit money to account"""
    banking_service = BankingService(db)
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
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Withdraw money from account"""
    banking_service = BankingService(db)
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
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get account transaction statement"""
    banking_service = BankingService(db)
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
            balance_after=txn['balance_after'],
            timestamp=txn['timestamp']
        )
        for txn in transactions
    ]