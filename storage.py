import json
import os
from bank import Bank
from user import User
from account import Account

DATA_FILE = "bank_data.json"

def save_data(bank):
    """
    COMPLETE SAVE: Save entire bank state to JSON file
    Returns: True if saved, False if error
    """
    try:
        # Prepare all data in proper format
        data = {
            "bank_info": {
                "name": bank.get_name(),
                "total_accounts": len(bank.get_accounts())
            },
            "users": [],
            "accounts": []
        }
        
        # Collect all users from bank accounts
        user_dict = {}
        for account in bank.get_accounts():
            user = account.get_user()
            if user.get_user_id() not in user_dict:
                user_dict[user.get_user_id()] = {
                    "name": user.get_name(),
                    "user_id": user.get_user_id()
                }
        
        data["users"] = list(user_dict.values())
        
        # Collect all accounts
        for account in bank.get_accounts():
            account_data = {
                "account_number": account.get_account_number(),
                "user_id": account.get_user().get_user_id(),
                "balance": account.get_balance(),
                "transactions": getattr(account, '_Account__transactions', [])  # Get private attribute
            }
            data["accounts"].append(account_data)
        
        # Write to file
        with open(DATA_FILE, 'w') as file:
            json.dump(data, file, indent=4)
        
        print(f"✅ Data saved successfully to {DATA_FILE}")
        print(f"   - {len(data['users'])} users")
        print(f"   - {len(data['accounts'])} accounts")
        return True
        
    except Exception as e:
        print(f"❌ Error saving data: {e}")
        return False

def load_data():
    """
    COMPLETE LOAD: Load and recreate entire bank from file
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
        bank = Bank(data["bank_info"]["name"])
        print(f"   Bank: {bank.get_name()}")
        
        # Create users dictionary for quick lookup
        users = {}
        for user_data in data.get("users", []):
            # Default role to 'customer' if not specified in saved data
            role = user_data.get("role", "customer")
            user = User(user_data["name"], user_data["user_id"], role)
            users[user_data["user_id"]] = user
            print(f"   User: {user.get_name()} (ID: {user.get_user_id()}, Role: {role})")
        
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
        
        print(f"✅ Loaded {len(bank.get_accounts())} accounts")
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
        print(f"Bank: {data['bank_info']['name']}")
        print(f"Users: {len(data['users'])}")
        print(f"Accounts: {len(data['accounts'])}")
        
        for i, account in enumerate(data['accounts'][:3]):  # Show first 3
            print(f"  {i+1}. {account['account_number']}: ${account['balance']} (User: {account['user_id']})")
        
        if len(data['accounts']) > 3:
            print(f"  ... and {len(data['accounts']) - 3} more accounts")
            
    except Exception as e:
        print(f"Error reading file: {e}")