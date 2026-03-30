from sqlalchemy.orm import Session
from sqlalchemy import func
from persistence.models import UserDB, AccountDB, TransactionDB, AuthDB

from typing import List, Optional, Dict, Any, Tuple

STAFF_ROLES = {"admin", "manager", "teller"}


class BankingService:
    """Service layer for banking operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_accounts(self, user_id: str, current_user_role: str) -> List[AccountDB]:
        """Get accounts accessible to the current user"""
        if current_user_role in STAFF_ROLES:
            # Staff can see all accounts
            return self.db.query(AccountDB).all()
        else:
            # Customers can only see their own accounts
            user = self.db.query(UserDB).filter(UserDB.user_id == user_id).first()
            if not user:
                return []
            return user.accounts

    def get_account_detail(self, account_number: str, current_user_id: str, current_user_role: str) -> Optional[AccountDB]:
        """Get detailed account info if user has access"""
        account = self.db.query(AccountDB).filter(AccountDB.account_number == account_number).first()
        if not account:
            return None

        # Check access permission
        if current_user_role in STAFF_ROLES or account.owner.user_id == current_user_id:
            return account

        return None

    def deposit_to_account(self, account_number: str, amount: float,
                          current_user_id: str, current_user_role: str) -> Tuple[bool, str, Optional[float]]:
        """Deposit money to account if user has permission"""
        account = self.get_account_detail(account_number, current_user_id, current_user_role)
        if not account:
            return False, "Account not found or access denied", None

        if amount <= 0:
            return False, "Invalid deposit amount", None

        # Update balance
        account.balance += amount
        
        # Record transaction
        transaction = TransactionDB(
            account_id=account.id,
            type="DEPOSIT",
            amount=amount,
            balance_after=float(account.balance)
        )
        self.db.add(transaction)
        self.db.commit()
        
        return True, "Deposit successful", float(account.balance)

    def withdraw_from_account(self, account_number: str, amount: float,
                             current_user_id: str, current_user_role: str) -> Tuple[bool, str, Optional[float]]:
        """Withdraw money from account if user has permission"""
        account = self.get_account_detail(account_number, current_user_id, current_user_role)
        if not account:
            return False, "Account not found or access denied", None

        if amount <= 0:
            return False, "Invalid withdrawal amount", None
            
        if account.balance < amount:
            return False, "Insufficient funds", None

        # Update balance
        account.balance -= amount
        
        # Record transaction
        transaction = TransactionDB(
            account_id=account.id,
            type="WITHDRAWAL",
            amount=amount,
            balance_after=float(account.balance)
        )
        self.db.add(transaction)
        self.db.commit()
        
        return True, "Withdrawal successful", float(account.balance)

    def get_account_statement(
        self,
        account_number: str,
        current_user_id: str,
        current_user_role: str,
        limit: int = 10,
    ) -> Optional[List[Dict[str, Any]]]:
        """Get recent transactions for account"""
        account = self.get_account_detail(account_number, current_user_id, current_user_role)
        if not account:
            return None

        transactions = self.db.query(TransactionDB)\
            .filter(TransactionDB.account_id == account.id)\
            .order_by(TransactionDB.timestamp.desc())\
            .limit(limit)\
            .all()
            
        return [
            {
                "type": t.type,
                "amount": t.amount,
                "balance_after": t.balance_after,
                "timestamp": t.timestamp.isoformat()
            } for t in transactions
        ]

    def create_account(self, user_id: str, initial_balance: float = 0) -> AccountDB:
        """Create new account for user (teller+ only)"""
        if initial_balance < 0:
            raise ValueError("Initial balance cannot be negative")

        user = self.db.query(UserDB).filter(UserDB.user_id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Generate account number
        account_num = f"ACC{user_id.upper()}001"

        # Ensure unique account number
        counter = 1
        while self.db.query(AccountDB).filter(AccountDB.account_number == account_num).first():
            counter += 1
            account_num = f"ACC{user_id.upper()}{counter:03d}"

        account = AccountDB(
            account_number=account_num,
            user_id=user.id,
            balance=initial_balance
        )
        self.db.add(account)
        self.db.flush()
        
        if initial_balance > 0:
            transaction = TransactionDB(
                account_id=account.id,
                type="DEPOSIT",
                amount=initial_balance,
                balance_after=initial_balance
            )
            self.db.add(transaction)
            
        self.db.commit()
        return account

    def get_system_snapshot(self) -> Dict[str, Any]:
        """Get system-wide statistics"""
        total_accounts = self.db.query(AccountDB).count()
        total_balance = self.db.query(func.sum(AccountDB.balance)).scalar() or 0.0
        total_users = self.db.query(UserDB).count()
        auth_users = self.db.query(AuthDB).count()

        return {
            'bank_name': "Secure Bank (PostgreSQL)",
            'total_users': total_users,
            'total_accounts': total_accounts,
            'total_balance': total_balance,
            'auth_users': auth_users
        }
