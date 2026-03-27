from bank import Bank
from account import Account
from user import User
from auth import auth_system
from persistence.store import save_data
from typing import List, Optional, Dict, Any, Tuple

STAFF_ROLES = {"admin", "manager", "teller"}


class BankingService:
    """Service layer for banking operations"""

    def __init__(self, bank: Bank):
        self.bank = bank

    def get_user_accounts(self, user_id: str, current_user_role: str) -> List[Account]:
        """Get accounts accessible to the current user"""
        all_accounts = self.bank.get_accounts()

        if current_user_role in STAFF_ROLES:
            # Staff can see all accounts
            return all_accounts
        else:
            # Customers can only see their own accounts
            return [acc for acc in all_accounts if acc.get_user().get_user_id() == user_id]

    def get_account_detail(self, account_number: str, current_user_id: str, current_user_role: str) -> Optional[Account]:
        """Get detailed account info if user has access"""
        account = self.bank.find_account(account_number)
        if not account:
            return None

        # Check access permission
        account_user_id = account.get_user().get_user_id()
        if current_user_role in STAFF_ROLES or account_user_id == current_user_id:
            return account

        return None

    def deposit_to_account(self, account_number: str, amount: float,
                          current_user_id: str, current_user_role: str) -> Tuple[bool, str, Optional[float]]:
        """Deposit money to account if user has permission"""
        account = self.get_account_detail(account_number, current_user_id, current_user_role)
        if not account:
            return False, "Account not found or access denied", None

        # Check if deposit is allowed (staff can deposit to any account, customers only to own)
        account_user_id = account.get_user().get_user_id()
        if current_user_role not in STAFF_ROLES and account_user_id != current_user_id:
            return False, "Access denied", None

        if account.deposit(amount):
            save_data(self.bank)  # Persist changes
            return True, "Deposit successful", account.get_balance()
        else:
            return False, "Invalid deposit amount", None

    def withdraw_from_account(self, account_number: str, amount: float,
                             current_user_id: str, current_user_role: str) -> Tuple[bool, str, Optional[float]]:
        """Withdraw money from account if user has permission"""
        account = self.get_account_detail(account_number, current_user_id, current_user_role)
        if not account:
            return False, "Account not found or access denied", None

        # Check if withdrawal is allowed (staff can withdraw from any account, customers only from own)
        account_user_id = account.get_user().get_user_id()
        if current_user_role not in STAFF_ROLES and account_user_id != current_user_id:
            return False, "Access denied", None

        if account.withdraw(amount):
            save_data(self.bank)  # Persist changes
            return True, "Withdrawal successful", account.get_balance()
        else:
            return False, "Insufficient funds or invalid amount", None

    def get_account_statement(self, account_number: str, current_user_id: str,
                             current_user_role: str, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Get recent transactions for account"""
        account = self.get_account_detail(account_number, current_user_id, current_user_role)
        if not account:
            return None

        transactions = account.get_transactions()
        if limit <= 0:
            return []
        return transactions[-limit:] if transactions else []

    def create_account(self, user: User, initial_balance: float = 0) -> Account:
        """Create new account for user (teller+ only)"""
        if initial_balance < 0:
            raise ValueError("Initial balance cannot be negative")

        # Generate account number
        user_id = user.get_user_id()
        account_num = f"ACC{user_id.upper()}001"

        # Ensure unique account number
        existing_nums = [acc.get_account_number() for acc in self.bank.get_accounts()]
        counter = 1
        while account_num in existing_nums:
            counter += 1
            account_num = f"ACC{user_id.upper()}{counter:03d}"

        account = Account(account_num, user, initial_balance)
        self.bank.add_account(account)
        save_data(self.bank)  # Persist changes

        return account

    def get_system_snapshot(self) -> Dict[str, Any]:
        """Get system-wide statistics"""
        accounts = self.bank.get_accounts()
        total_balance = sum(acc.get_balance() for acc in accounts)

        # Count unique users
        user_ids = set(acc.get_user().get_user_id() for acc in accounts)

        return {
            'bank_name': self.bank.get_name(),
            'total_users': len(user_ids),
            'total_accounts': len(accounts),
            'total_balance': total_balance,
            'auth_users': len(auth_system.user_credentials)
        }
