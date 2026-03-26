import json
import os
import datetime
from bank import Bank
from user import User
from account import Account
from auth import auth_system

DATA_FILE = "data_store.json"

def save_data(bank):
    """
    Save entire bank state and auth credentials to JSON file
    Returns: True if saved, False if error
    """
    try:
        # Prepare bank data
        data = {
            "bank": {
                "name": bank.get_name(),
                "total_accounts": len(bank.get_accounts())
            },
            "users": [],
            "accounts": [],
            "auth": {
                "user_credentials": {}
            }
        }

        # Collect all users from bank accounts
        user_dict = {}
        for account in bank.get_accounts():
            user = account.get_user()
            if user.get_user_id() not in user_dict:
                user_dict[user.get_user_id()] = {
                    "name": user.get_name(),
                    "user_id": user.get_user_id(),
                    "role": user.get_role(),
                    "email": getattr(user, '_User__email', None),
                    "phone": getattr(user, '_User__phone', None)
                }

        data["users"] = list(user_dict.values())

        # Collect all accounts
        for account in bank.get_accounts():
            account_data = {
                "account_number": account.get_account_number(),
                "user_id": account.get_user().get_user_id(),
                "balance": account.get_balance(),
                "transactions": getattr(account, '_Account__transactions', [])
            }
            data["accounts"].append(account_data)

        # Collect auth credentials
        for user_id, creds in auth_system.user_credentials.items():
            # Convert bytes to string for JSON serialization
            password_hash = creds['password_hash']
            if isinstance(password_hash, bytes):
                password_hash = password_hash.decode('utf-8')

            # Convert datetime to ISO string
            locked_until = creds.get('locked_until')
            if isinstance(locked_until, datetime.datetime):
                locked_until = locked_until.isoformat()
            elif locked_until is None:
                locked_until = None

            data["auth"]["user_credentials"][user_id] = {
                'password_hash': password_hash,
                'failed_attempts': creds.get('failed_attempts', 0),
                'locked_until': locked_until,
                'role': creds.get('role', 'customer')
            }

        # Write to file
        with open(DATA_FILE, 'w') as file:
            json.dump(data, file, indent=4)

        print(f"✅ Data saved successfully to {DATA_FILE}")
        print(f"   - {len(data['users'])} users")
        print(f"   - {len(data['accounts'])} accounts")
        print(f"   - {len(data['auth']['user_credentials'])} auth credentials")
        return True

    except Exception as e:
        print(f"❌ Error saving data: {e}")
        return False

def load_data():
    """
    Load and recreate entire bank and auth state from file
    Returns: Bank object with all accounts, or None if no file
    """
    if not os.path.exists(DATA_FILE):
        print("📭 No saved data found")
        return None

    try:
        with open(DATA_FILE, 'r') as file:
            data = json.load(file)

        print("📂 Loading saved data...")

        # Create bank
        bank = Bank(data["bank"]["name"])
        print(f"   Bank: {bank.get_name()}")

        # Create users dictionary for quick lookup
        users = {}
        for user_data in data.get("users", []):
            user = User(
                user_data["name"],
                user_data["user_id"],
                user_data.get("role", "customer")
            )
            if user_data.get("email"):
                user.set_email(user_data["email"])
            if user_data.get("phone"):
                user.set_phone(user_data["phone"])
            users[user_data["user_id"]] = user
            print(f"   User: {user.get_name()} (ID: {user.get_user_id()}, Role: {user.get_role()})")

        # Create accounts and add to bank
        for account_data in data.get("accounts", []):
            user_id = account_data["user_id"]
            if user_id in users:
                # Create account with saved balance
                account = Account(
                    account_data["account_number"],
                    users[user_id],
                    account_data["balance"]
                )

                # Restore transactions if they exist
                if "transactions" in account_data:
                    setattr(account, '_Account__transactions', account_data["transactions"])

                # Add to bank
                bank.add_account(account)
                print(f"   Account: {account.get_account_number()} - ${account.get_balance()}")

        # Load auth credentials
        for user_id, creds in data.get("auth", {}).get("user_credentials", {}).items():
            # Convert string back to bytes for bcrypt
            password_hash = creds['password_hash']
            if isinstance(password_hash, str):
                password_hash = password_hash.encode('utf-8')

            # Convert ISO string back to datetime
            locked_until = creds.get('locked_until')
            if locked_until:
                try:
                    locked_until = datetime.datetime.fromisoformat(locked_until)
                except:
                    locked_until = None

            auth_system.user_credentials[user_id] = {
                'password_hash': password_hash,
                'failed_attempts': creds.get('failed_attempts', 0),
                'locked_until': locked_until,
                'role': creds.get('role', 'customer')
            }

        print(f"✅ Loaded {len(bank.get_accounts())} accounts")
        print(f"✅ Loaded {len(auth_system.user_credentials)} auth credentials")
        return bank

    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None

def clear_data():
    """Delete saved data file"""
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
        print(f"🧹 Deleted {DATA_FILE}")
        return True
    print("📭 No data file to delete")
    return False

def view_saved_data():
    """Show what's in the saved file (for debugging)"""
    if not os.path.exists(DATA_FILE):
        print("No saved data file exists")
        return

    try:
        with open(DATA_FILE, 'r') as file:
            data = json.load(file)

        print("\n📄 SAVED DATA PREVIEW:")
        print(f"Bank: {data['bank']['name']}")
        print(f"Users: {len(data['users'])}")
        print(f"Accounts: {len(data['accounts'])}")
        print(f"Auth Credentials: {len(data['auth']['user_credentials'])}")

        for i, account in enumerate(data['accounts'][:3]):  # Show first 3
            print(f"  {i+1}. {account['account_number']}: ${account['balance']} (User: {account['user_id']})")

        if len(data['accounts']) > 3:
            print(f"  ... and {len(data['accounts']) - 3} more accounts")

    except Exception as e:
        print(f"Error reading file: {e}")