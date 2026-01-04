"""
main.py - Enhanced with authentication system
"""

from bank import Bank
from user import User
from account import Account
from storage import save_data, load_data, clear_data
from auth import auth_system, require_auth, require_role, PasswordValidator
import getpass

# Global session variable
current_user = None
current_token = None

def register_user():
    """Register new user with authentication"""
    print("\n" + "="*40)
    print("👤 USER REGISTRATION")
    print("="*40)
    
    # Get user details
    name = input("Full Name: ").strip()
    user_id = input("User ID (username): ").strip().lower()
    
    # Check if user already exists
    if user_id in auth_system.user_credentials:
        print("❌ User ID already exists. Please choose another.")
        return None, None
    
    # Get password with confirmation
    while True:
        password = getpass.getpass("Password: ")
        confirm = getpass.getpass("Confirm Password: ")
        
        if password != confirm:
            print("❌ Passwords don't match. Try again.")
            continue
        
        # Validate password strength
        is_valid, message = PasswordValidator.validate(password)
        if not is_valid:
            print(f"❌ {message}")
            print("Password must have: 8+ chars, uppercase, lowercase, number, special char")
            continue
        
        break
    
    # Get role (default to customer)
    print("\nSelect Role:")
    print("1. Customer (default)")
    print("2. Teller")
    print("3. Manager")
    print("4. Admin (requires admin approval)")
    
    role_choice = input("Choose role [1-4, default 1]: ").strip()
    roles = { "1": "customer", "2": "teller", "3": "manager", "4": "admin" }
    role = roles.get(role_choice, "customer")
    
    # Additional info
    email = input("Email (optional): ").strip() or None
    phone = input("Phone (optional): ").strip() or None
    
    # Create user in auth system
    success, message = auth_system.create_user(user_id, password)
    if not success:
        print(f"❌ Registration failed: {message}")
        return None, None
    
    # Create User object
    user = User(name, user_id, role)
    if email:
        user.set_email(email)
    if phone:
        user.set_phone(phone)
    
    print(f"✅ Registration successful! Welcome {name}")
    print(f"   User ID: {user_id}")
    print(f"   Role: {role}")
    
    return user, user_id

def login_user():
    """Login existing user"""
    print("\n" + "="*40)
    print("🔐 USER LOGIN")
    print("="*40)
    
    user_id = input("User ID: ").strip().lower()
    password = getpass.getpass("Password: ")
    
    # Attempt login
    success, token, message = auth_system.login(user_id, password)
    
    if success:
        print(f"✅ {message}")
        
        # Get user info from bank (if exists)
        # In full system, you'd load user from database
        # For now, create a basic user object
        user = User(user_id.capitalize(), user_id, "customer")  # Role would come from DB
        
        return user, token
    else:
        print(f"❌ {message}")
        return None, None

def change_password_menu():
    """Change current user's password"""
    global current_user, current_token
    
    if not current_user or not current_token:
        print("❌ You must be logged in to change password")
        return
    
    print("\n" + "="*40)
    print("🔑 CHANGE PASSWORD")
    print("="*40)
    
    current_pass = getpass.getpass("Current Password: ")
    new_pass = getpass.getpass("New Password: ")
    confirm_pass = getpass.getpass("Confirm New Password: ")
    
    if new_pass != confirm_pass:
        print("❌ New passwords don't match")
        return
    
    success, message = auth_system.change_password(
        current_user.get_user_id(), 
        current_pass, 
        new_pass
    )
    
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")

def admin_dashboard():
    """Admin-only functionality"""
    global current_user, current_token
    
    # Check if user is admin
    has_role, payload, message = require_role(current_token, "admin")
    if not has_role:
        print(f"❌ {message}")
        return
    
    print("\n" + "="*40)
    print("👑 ADMIN DASHBOARD")
    print("="*40)
    
    while True:
        print("\nAdmin Options:")
        print("1. View All Users")
        print("2. Reset User Password")
        print("3. View Login Attempts")
        print("4. Lock/Unlock User")
        print("5. Back to Main Menu")
        
        choice = input("\nSelect option [1-5]: ").strip()
        
        if choice == "1":
            print("\n📋 Registered Users:")
            for user_id, creds in auth_system.user_credentials.items():
                status = "🔒 LOCKED" if creds.get('locked_until') else "✅ ACTIVE"
                print(f"  {user_id}: {status}")
                print(f"    Failed attempts: {creds.get('failed_attempts', 0)}")
        
        elif choice == "2":
            user_id = input("User ID to reset: ").strip()
            if user_id in auth_system.user_credentials:
                # In production, generate temporary password and email it
                temp_pass = "Temp123!"  # Would be generated randomly
                print(f"Temporary password for {user_id}: {temp_pass}")
                print("User must change this on first login")
            else:
                print("❌ User not found")
        
        elif choice == "3":
            print("\n🚨 Login Attempts:")
            for user_id, creds in auth_system.user_credentials.items():
                attempts = creds.get('failed_attempts', 0)
                if attempts > 0:
                    print(f"  {user_id}: {attempts} failed attempts")
        
        elif choice == "4":
            user_id = input("User ID to lock/unlock: ").strip()
            if user_id in auth_system.user_credentials:
                creds = auth_system.user_credentials[user_id]
                if creds.get('locked_until'):
                    creds['locked_until'] = None
                    creds['failed_attempts'] = 0
                    print(f"✅ {user_id} unlocked")
                else:
                    # Lock for 1 hour
                    import datetime
                    creds['locked_until'] = datetime.datetime.now() + datetime.timedelta(hours=1)
                    print(f"🔒 {user_id} locked for 1 hour")
            else:
                print("❌ User not found")
        
        elif choice == "5":
            break
        
        else:
            print("❌ Invalid option")

def main():
    global current_user, current_token
    
    print("=== 🏦 BANKING SYSTEM WITH AUTHENTICATION ===")
    
    # Load saved data
    bank = load_data()
    
    if bank is None:
        print("\nNo saved data found. Creating new bank...")
        bank_name = input("Enter bank name [Default: Secure Bank]: ").strip() or "Secure Bank"
        bank = Bank(bank_name)
        print(f"✅ Created new bank: {bank.get_name()}")
    
    # Main authentication loop
    while True:
        print("\n" + "="*50)
        print(f"🏦 {bank.get_name()} - Banking System")
        print("="*50)
        
        if current_user:
            print(f"👤 Logged in as: {current_user.get_name()}")
            print(f"   Role: {current_user.get_role()}")
            print(f"   User ID: {current_user.get_user_id()}")
        
        print("\nMain Menu:")
        print("1. 🔐 Login")
        print("2. 👤 Register")
        print("3. 🏦 Banking Operations")
        print("4. 🔑 Change Password")
        print("5. 👑 Admin Dashboard")
        print("6. 💾 Save Data")
        print("7. 📂 View Saved Data")
        print("8. 🧹 Clear All Data")
        print("9. 🚪 Logout")
        print("0. Exit")
        
        choice = input("\nEnter choice [0-9]: ").strip()
        
        # 1. Login
        if choice == "1":
            if current_user:
                print("❌ Already logged in. Logout first.")
            else:
                user, token = login_user()
                if user and token:
                    current_user = user
                    current_token = token
        
        # 2. Register
        elif choice == "2":
            if current_user:
                print("❌ Please logout before registering new user.")
            else:
                user, user_id = register_user()
                if user:
                    # Create a default account for new user
                    account_num = f"ACC{user_id.upper()}001"
                    account = Account(account_num, user, 100.0)  # Start with $100
                    bank.add_account(account)
                    print(f"✅ Created account {account_num} with $100.00")
        
        # 3. Banking Operations (requires login)
        elif choice == "3":
            if not current_user or not current_token:
                print("❌ Please login first")
                continue
            
            banking_operations(bank, current_user, current_token)
        
        # 4. Change Password
        elif choice == "4":
            change_password_menu()
        
        # 5. Admin Dashboard
        elif choice == "5":
            admin_dashboard()
        
        # 6. Save Data
        elif choice == "6":
            if save_data(bank):
                print("✅ All data saved successfully!")
            else:
                print("❌ Failed to save data")
        
        # 7. View Saved Data
        elif choice == "7":
            # Simple preview
            import os
            if os.path.exists("bank_data.json"):
                print("\n📄 Data File Exists")
                with open("bank_data.json", 'r') as f:
                    data = json.load(f)
                    print(f"Bank: {data['bank_info']['name']}")
                    print(f"Users: {len(data.get('users', []))}")
                    print(f"Accounts: {len(data.get('accounts', []))}")
            else:
                print("📭 No saved data file")
        
        # 8. Clear Data
        elif choice == "8":
            confirm = input("⚠️  Delete ALL saved data? (yes/no): ")
            if confirm.lower() == "yes":
                clear_data()
                print("Data cleared. Restarting with fresh bank...")
                bank = Bank("Fresh Bank")
                current_user = None
                current_token = None
        
        # 9. Logout
        elif choice == "9":
            if current_token:
                auth_system.logout(current_token)
                print("✅ Logged out successfully")
            current_user = None
            current_token = None
        
        # 0. Exit
        elif choice == "0":
            save = input("Save data before exiting? (yes/no): ")
            if save.lower() == "yes":
                save_data(bank)
            print("Goodbye! 👋")
            break
        
        else:
            print("❌ Invalid choice")

def banking_operations(bank, user, token):
    """Banking operations menu (requires authentication)"""
    print("\n" + "="*40)
    print("💰 BANKING OPERATIONS")
    print("="*40)
    
    # Get user's accounts
    user_accounts = []
    for account in bank.get_accounts():
        if account.get_user().get_user_id() == user.get_user_id():
            user_accounts.append(account)
    
    if not user_accounts:
        print("No accounts found for this user.")
        return
    
    while True:
        print(f"\nAccounts for {user.get_name()}:")
        for i, acc in enumerate(user_accounts, 1):
            print(f"{i}. {acc.get_account_number()} - ${acc.get_balance():.2f}")
        
        print("\nOptions:")
        print("1. Check Balance")
        print("2. Deposit")
        print("3. Withdraw")
        print("4. View Statement")
        print("5. Back to Main Menu")
        
        choice = input("\nSelect option [1-5]: ").strip()
        
        if choice == "1":
            # Show all account balances
            print("\n📊 ACCOUNT BALANCES:")
            total = 0
            for acc in user_accounts:
                print(f"  {acc.get_account_number()}: ${acc.get_balance():.2f}")
                total += acc.get_balance()
            print(f"\n💰 TOTAL: ${total:.2f}")
        
        elif choice == "2":
            acc_num = input("Account number: ").strip()
            account = bank.find_account(acc_num)
            if account and account.get_user().get_user_id() == user.get_user_id():
                try:
                    amount = float(input("Amount to deposit: $"))
                    if account.deposit(amount):
                        print(f"✅ Deposited ${amount:.2f}")
                        print(f"   New balance: ${account.get_balance():.2f}")
                    else:
                        print("❌ Invalid deposit amount")
                except:
                    print("❌ Please enter a valid number")
            else:
                print("❌ Account not found or access denied")
        
        elif choice == "3":
            acc_num = input("Account number: ").strip()
            account = bank.find_account(acc_num)
            if account and account.get_user().get_user_id() == user.get_user_id():
                try:
                    amount = float(input("Amount to withdraw: $"))
                    if account.withdraw(amount):
                        print(f"✅ Withdrew ${amount:.2f}")
                        print(f"   New balance: ${account.get_balance():.2f}")
                    else:
                        print("❌ Insufficient funds or invalid amount")
                except:
                    print("❌ Please enter a valid number")
            else:
                print("❌ Account not found or access denied")
        
        elif choice == "4":
            acc_num = input("Account number: ").strip()
            account = bank.find_account(acc_num)
            if account and account.get_user().get_user_id() == user.get_user_id():
                account.show_statement()
            else:
                print("❌ Account not found or access denied")
        
        elif choice == "5":
            break
        
        else:
            print("❌ Invalid option")

if __name__ == "__main__":
    # Import json for the view data option
    import json
    main()
    