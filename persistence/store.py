"""Data store abstraction layer for persistence"""
from sqlalchemy.orm import Session
from .models import UserDB, AccountDB, TransactionDB, AuthDB
from typing import List, Dict, Any, Optional

class Store:
    """Abstraction over SQLAlchemy Session for data operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_user(self, user_id: str) -> Optional[UserDB]:
        return self.session.query(UserDB).filter(UserDB.user_id == user_id).first()
    
    def get_account(self, account_number: str) -> Optional[AccountDB]:
        return self.session.query(AccountDB).filter(AccountDB.account_number == account_number).first()
    
    def get_accounts_by_user(self, user_id: str) -> List[AccountDB]:
        user = self.get_user(user_id)
        return user.accounts if user else []
    
    def create_account(self, account_number: str, user_id: int, balance: float = 0.0) -> AccountDB:
        account = AccountDB(account_number=account_number, user_id=user_id, balance=balance)
        self.session.add(account)
        self.session.flush()
        return account
    
    def add_transaction(self, account_id: int, txn_type: str, amount: float, balance_after: float) -> TransactionDB:
        txn = TransactionDB(account_id=account_id, type=txn_type, amount=amount, balance_after=balance_after)
        self.session.add(txn)
        self.session.flush()
        return txn

# Global store factory (can be used if needed)
def get_store(session: Session) -> Store:
    return Store(session)

