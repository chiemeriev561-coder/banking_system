import json
import os
import datetime
from sqlalchemy.orm import Session
from persistence.database import SessionLocal, engine, Base
from persistence.models import UserDB, AccountDB, TransactionDB, AuthDB

DATA_FILE = "data_store.json"

def migrate():
    if not os.path.exists(DATA_FILE):
        print(f"❌ No {DATA_FILE} found. Nothing to migrate.")
        return

    # Initialize database tables
    print("🔨 Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    # Load JSON data
    print(f"📂 Loading data from {DATA_FILE}...")
    with open(DATA_FILE, 'r') as file:
        data = json.load(file)

    db = SessionLocal()
    try:
        # 1. Migrate Users
        print("👤 Migrating users...")
        user_map = {} # user_id_str -> db_id
        for u_data in data.get("users", []):
            user = UserDB(
                user_id=u_data["user_id"],
                name=u_data["name"],
                role=u_data.get("role", "customer"),
                email=u_data.get("email"),
                phone=u_data.get("phone")
            )
            db.add(user)
            db.flush()
            user_map[u_data["user_id"]] = user.id
            print(f"   - Migrated user: {u_data['user_id']}")

        # 2. Migrate Auth Credentials
        print("🔐 Migrating auth credentials...")
        auth_data = data.get("auth", {}).get("user_credentials", {})
        for user_id_str, creds in auth_data.items():
            if user_id_str in user_map:
                locked_until = None
                if creds.get('locked_until'):
                    try:
                        locked_until = datetime.datetime.fromisoformat(creds['locked_until'])
                    except:
                        pass
                
                auth = AuthDB(
                    user_id=user_map[user_id_str],
                    password_hash=creds['password_hash'],
                    failed_attempts=creds.get('failed_attempts', 0),
                    locked_until=locked_until
                )
                db.add(auth)
                print(f"   - Migrated auth for: {user_id_str}")

        # 3. Migrate Accounts and Transactions
        print("💰 Migrating accounts and transactions...")
        for acc_data in data.get("accounts", []):
            user_id_str = acc_data["user_id"]
            if user_id_str in user_map:
                account = AccountDB(
                    account_number=acc_data["account_number"],
                    user_id=user_map[user_id_str],
                    balance=acc_data["balance"]
                )
                db.add(account)
                db.flush()
                print(f"   - Migrated account: {acc_data['account_number']}")

                # Migrate history
                transactions = acc_data.get("transactions", [])
                for t_data in transactions:
                    # In JSON, timestamp might not exist. We'll use UTC now if missing
                    # but try to preserve order
                    t_time = datetime.datetime.utcnow()
                    if t_data.get("timestamp"):
                        try:
                            t_time = datetime.datetime.fromisoformat(t_data["timestamp"])
                        except:
                            pass
                    
                    transaction = TransactionDB(
                        account_id=account.id,
                        type=t_data["type"],
                        amount=t_data["amount"],
                        balance_after=t_data["balance_after"],
                        timestamp=t_time
                    )
                    db.add(transaction)
                if transactions:
                    print(f"     - Migrated {len(transactions)} transactions")

        db.commit()
        print("✅ Migration completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
