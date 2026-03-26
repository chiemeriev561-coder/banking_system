import pytest
from fastapi.testclient import TestClient
from api.app import app
from persistence.store import clear_data

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Clear data before and after each test"""
    clear_data()
    yield
    clear_data()

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Clear data before and after each test"""
    clear_data()
    yield
    clear_data()

def test_register_user(client):
    """Test user registration"""
    response = client.post("/auth/register", json={
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

def test_login_user(client):
    """Test user login"""
    # First register
    client.post("/auth/register", json={
        "name": "Jane Doe",
        "user_id": "jane",
        "password": "Password123!"
    })

    # Then login
    response = client.post("/auth/login", json={
        "user_id": "jane",
        "password": "Password123!"
    })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post("/auth/login", json={
        "user_id": "nonexistent",
        "password": "wrongpass"
    })

    assert response.status_code == 401

def test_get_accounts_unauthorized(client):
    """Test accessing accounts without authentication"""
    response = client.get("/api/accounts")
    assert response.status_code == 401

def test_deposit_withdraw_flow(client):
    """Test deposit and withdraw operations"""
    # Register and login
    client.post("/auth/register", json={
        "name": "Test User",
        "user_id": "testuser",
        "password": "Password123!"
    })

    login_response = client.post("/auth/login", json={
        "user_id": "testuser",
        "password": "Password123!"
    })

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get accounts
    response = client.get("/api/accounts", headers=headers)
    assert response.status_code == 200
    accounts = response.json()
    assert len(accounts) == 1  # Default account created

    account_number = accounts[0]["account_number"]
    initial_balance = accounts[0]["balance"]

    # Deposit money
    response = client.post(
        f"/api/accounts/{account_number}/deposit",
        json={"amount": 50.0},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["new_balance"] == initial_balance + 50.0

    # Withdraw money
    response = client.post(
        f"/api/accounts/{account_number}/withdraw",
        json={"amount": 25.0},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["new_balance"] == initial_balance + 25.0

    # Try to withdraw too much
    response = client.post(
        f"/api/accounts/{account_number}/withdraw",
        json={"amount": 999999.0},
        headers=headers
    )
    assert response.status_code == 400

def test_admin_operations(client):
    """Test admin-only operations"""
    # Register regular user
    client.post("/auth/register", json={
        "name": "Regular User",
        "user_id": "regular",
        "password": "Password123!"
    })

    # Register admin user
    client.post("/auth/register", json={
        "name": "Admin User",
        "user_id": "admin",
        "password": "Password123!",
        "role": "admin"
    })

    # Login as admin
    login_response = client.post("/auth/login", json={
        "user_id": "admin",
        "password": "Password123!"
    })

    admin_token = login_response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Get all users (admin only)
    response = client.get("/admin/users", headers=admin_headers)
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 2  # At least regular and admin

    # Lock user
    response = client.post("/admin/users/regular/lock", headers=admin_headers)
    assert response.status_code == 200

    # Try to login as locked user
    response = client.post("/auth/login", json={
        "user_id": "regular",
        "password": "Password123!"
    })
    assert response.status_code == 401

    # Unlock user
    response = client.post("/admin/users/regular/unlock", headers=admin_headers)
    assert response.status_code == 200

def test_change_password(client):
    """Test password change"""
    # Register user
    client.post("/auth/register", json={
        "name": "Password Test",
        "user_id": "passtest",
        "password": "OldPassword123!"
    })

    # Login with old password
    login_response = client.post("/auth/login", json={
        "user_id": "passtest",
        "password": "OldPassword123!"
    })

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Change password
    response = client.post("/auth/change-password", json={
        "current_password": "OldPassword123!",
        "new_password": "NewPassword123!"
    }, headers=headers)

    assert response.status_code == 200

    # Try to login with old password (should fail)
    response = client.post("/auth/login", json={
        "user_id": "passtest",
        "password": "OldPassword123!"
    })
    assert response.status_code == 401

    # Login with new password (should succeed)
    response = client.post("/auth/login", json={
        "user_id": "passtest",
        "password": "NewPassword123!"
    })
    assert response.status_code == 200

def test_system_snapshot(client):
    """Test system snapshot endpoint"""
    response = client.get("/system/snapshot")
    assert response.status_code == 200
    data = response.json()
    assert "bank_name" in data
    assert "total_users" in data
    assert "total_accounts" in data
    assert "total_balance" in data