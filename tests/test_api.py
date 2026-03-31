import asyncio
import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.app import app
from api.routers.accounts import get_account_detail, get_account_statement
from persistence.database import Base, get_db
from persistence.models import UserDB, AccountDB, TransactionDB, AuthDB
from services.banking_service import BankingService
from services.auth_service import auth_service
from core.auth import auth_system

# Setup in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

@pytest.mark.anyio
async def test_register_user(client):
    """Test user registration"""
    response = await client.post("/auth/register", json={
        "name": "John Doe",
        "user_id": "john",
        "password": "Password123!",
        "email": "john@example.com"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["user_id"] == "john"
    assert data["role"] == "customer"
    assert data["email"] == "john@example.com"

@pytest.mark.anyio
async def test_login_user(client):
    """Test user login"""
    await client.post("/auth/register", json={
        "name": "Jane Doe",
        "user_id": "jane",
        "password": "Password123!"
    })

    response = await client.post("/auth/login", json={
        "user_id": "jane",
        "password": "Password123!"
    })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.anyio
async def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = await client.post("/auth/login", json={
        "user_id": "nonexistent",
        "password": "wrongpass"
    })

    assert response.status_code == 401

@pytest.mark.anyio
async def test_get_accounts_unauthorized(client):
    """Test accessing accounts without authentication"""
    response = await client.get("/api/accounts")
    assert response.status_code == 401

@pytest.mark.anyio
async def test_deposit_withdraw_flow(client):
    """Test deposit and withdraw operations"""
    await client.post("/auth/register", json={
        "name": "Test User",
        "user_id": "testuser",
        "password": "Password123!"
    })

    login_response = await client.post("/auth/login", json={
        "user_id": "testuser",
        "password": "Password123!"
    })

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/accounts", headers=headers)
    assert response.status_code == 200
    accounts = response.json()
    assert len(accounts) == 1

    account_number = accounts[0]["account_number"]
    initial_balance = accounts[0]["balance"]

    response = await client.post(
        f"/api/accounts/{account_number}/deposit",
        json={"amount": 50.0},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["new_balance"] == initial_balance + 50.0

    response = await client.post(
        f"/api/accounts/{account_number}/withdraw",
        json={"amount": 25.0},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["new_balance"] == initial_balance + 25.0

@pytest.mark.anyio
async def test_admin_operations(client):
    """Test admin-only operations"""
    # Create regular user
    await client.post("/auth/register", json={
        "name": "Regular User",
        "user_id": "regular",
        "password": "Password123!"
    })

    # Create admin user
    await client.post("/auth/register", json={
        "name": "Admin User",
        "user_id": "admin",
        "password": "Password123!",
        "role": "admin"
    })

    login_response = await client.post("/auth/login", json={
        "user_id": "admin",
        "password": "Password123!"
    })

    admin_token = login_response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    response = await client.get("/admin/users", headers=admin_headers)
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 2

    response = await client.post("/admin/users/regular/lock", headers=admin_headers)
    assert response.status_code == 200

    response = await client.post("/auth/login", json={
        "user_id": "regular",
        "password": "Password123!"
    })
    assert response.status_code == 401

@pytest.mark.anyio
async def test_change_password(client):
    """Test password change"""
    await client.post("/auth/register", json={
        "name": "Password Test",
        "user_id": "passtest",
        "password": "OldPassword123!"
    })

    login_response = await client.post("/auth/login", json={
        "user_id": "passtest",
        "password": "OldPassword123!"
    })

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post("/auth/change-password", json={
        "current_password": "OldPassword123!",
        "new_password": "NewPassword123!"
    }, headers=headers)

    assert response.status_code == 200

    response = await client.post("/auth/login", json={
        "user_id": "passtest",
        "password": "NewPassword123!"
    })
    assert response.status_code == 200

@pytest.mark.anyio
async def test_system_snapshot(client):
    """Test system snapshot endpoint"""
    response = await client.get("/system/snapshot")
    assert response.status_code == 200
    data = response.json()
    assert "bank_name" in data
    assert "total_users" in data
    assert "total_accounts" in data
    assert "total_balance" in data

def test_get_account_statement_zero_limit_returns_empty_list():
    """Zero-limit statements should not return the full transaction history."""
    db = TestingSessionLocal()
    Base.metadata.create_all(bind=engine)
    try:
        service = BankingService(db)
        # Setup data
        auth_service.register_user(db, "Test User", "testuser", "Password123!")
        account = service.create_account("testuser", initial_balance=100.0)
        service.deposit_to_account(account.account_number, 25.0, "testuser", "customer")

        statement = service.get_account_statement(
            account.account_number,
            current_user_id="testuser",
            current_user_role="customer",
            limit=0,
        )

        assert statement == []
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_create_account_rejects_negative_initial_balance():
    """Accounts should not be created with a negative starting balance."""
    db = TestingSessionLocal()
    Base.metadata.create_all(bind=engine)
    try:
        service = BankingService(db)
        auth_service.register_user(db, "Test User", "testuser", "Password123!")
        
        with pytest.raises(ValueError, match="Initial balance cannot be negative"):
            service.create_account("testuser", initial_balance=-1.0)
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_get_account_statement_includes_timestamps():
    """Statement responses should preserve transaction timestamps."""
    db = TestingSessionLocal()
    Base.metadata.create_all(bind=engine)
    try:
        service = BankingService(db)
        auth_service.register_user(db, "Test User", "testuser", "Password123!")
        account = service.create_account("testuser", initial_balance=100.0)
        service.deposit_to_account(account.account_number, 25.0, "testuser", "customer")

        statement = asyncio.run(
            get_account_statement(
                account.account_number,
                limit=10,
                payload={"user_id": "testuser", "role": "customer"},
                db=db,
            )
        )
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

    assert statement
    assert statement[0].timestamp

def test_get_account_detail_includes_transaction_timestamps():
    """Account detail responses should include timestamps on nested transactions."""
    db = TestingSessionLocal()
    Base.metadata.create_all(bind=engine)
    try:
        service = BankingService(db)
        auth_service.register_user(db, "Test User", "testuser", "Password123!")
        account = service.create_account("testuser", initial_balance=100.0)
        service.deposit_to_account(account.account_number, 25.0, "testuser", "customer")

        detail = asyncio.run(
            get_account_detail(
                account.account_number,
                payload={"user_id": "testuser", "role": "customer"},
                db=db,
            )
        )
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

    assert detail.transactions
    assert detail.transactions[0].timestamp
