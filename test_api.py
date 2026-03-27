import httpx
import pytest

import api.app as app_module
import api.routers.accounts as accounts_router_module
import api.routers.admin as admin_router_module
import api.routers.auth as auth_router_module
from api.app import app
from auth import auth_system
from bank import Bank
from persistence.store import clear_data
from services.banking_service import BankingService
from user import User

pytestmark = pytest.mark.anyio


def reset_state():
    """Reset file-backed and in-memory application state between tests."""
    clear_data()
    auth_system.user_credentials.clear()
    auth_system.active_sessions.clear()
    app_module._bank = None
    auth_router_module._bank = None
    accounts_router_module._bank = None
    admin_router_module._bank = None


@pytest.fixture
async def client():
    reset_state()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
    reset_state()


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


async def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = await client.post("/auth/login", json={
        "user_id": "nonexistent",
        "password": "wrongpass"
    })

    assert response.status_code == 401


async def test_get_accounts_unauthorized(client):
    """Test accessing accounts without authentication"""
    response = await client.get("/api/accounts")
    assert response.status_code == 401


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

    response = await client.post(
        f"/api/accounts/{account_number}/withdraw",
        json={"amount": 999999.0},
        headers=headers
    )
    assert response.status_code == 400


async def test_admin_operations(client):
    """Test admin-only operations"""
    await client.post("/auth/register", json={
        "name": "Regular User",
        "user_id": "regular",
        "password": "Password123!"
    })

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

    response = await client.post("/admin/users/regular/unlock", headers=admin_headers)
    assert response.status_code == 200


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
        "password": "OldPassword123!"
    })
    assert response.status_code == 401

    response = await client.post("/auth/login", json={
        "user_id": "passtest",
        "password": "NewPassword123!"
    })
    assert response.status_code == 200


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
    bank = Bank("Test Bank")
    service = BankingService(bank)
    user = User("Test User", "testuser")
    account = service.create_account(user, initial_balance=100.0)
    account.deposit(25.0)

    statement = service.get_account_statement(
        account.get_account_number(),
        current_user_id=user.get_user_id(),
        current_user_role=user.get_role(),
        limit=0,
    )

    assert statement == []


def test_create_account_rejects_negative_initial_balance():
    """Accounts should not be created with a negative starting balance."""
    bank = Bank("Test Bank")
    service = BankingService(bank)
    user = User("Test User", "testuser")

    with pytest.raises(ValueError, match="Initial balance cannot be negative"):
        service.create_account(user, initial_balance=-1.0)
