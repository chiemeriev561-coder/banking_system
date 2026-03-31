# Banking System API

A REST API for a banking system with JWT authentication, user management, and account operations backed by PostgreSQL.

## 🎯 Key Features
- **REST API**: Full REST endpoints for banking operations
- **JWT Authentication**: Secure token-based authentication with role-based access
- **User Management**: Register users with different roles (customer, teller, manager, admin)
- **Account Operations**: Deposit, withdraw, check balance, view statements
- **Admin Functions**: User management, account locking/unlocking, password resets
- **Data Persistence**: SQLAlchemy models stored in PostgreSQL

## 🔒 Security Features
- **JWT Tokens**: Bearer token authentication
- **Role-Based Access**: Different permissions for customers, tellers, managers, and admins
- **Password Security**: bcrypt hashing with strength validation
- **Account Protection**: Failed attempt locking and admin controls

## 🚀 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `POST /auth/change-password` - Change password (authenticated)
- `POST /auth/logout` - Logout (invalidate token)

### Banking Operations (Authenticated)
- `GET /me` - Get current user profile
- `GET /api/accounts` - List user's accessible accounts
- `GET /api/accounts/{account_number}` - Get account details
- `POST /api/accounts/{account_number}/deposit` - Deposit money
- `POST /api/accounts/{account_number}/withdraw` - Withdraw money
- `GET /api/accounts/{account_number}/statement` - Get transaction history

### Admin Operations (Admin role required)
- `GET /admin/users` - List all users with status
- `POST /admin/users/{user_id}/lock` - Lock user account
- `POST /admin/users/{user_id}/unlock` - Unlock user account
- `POST /admin/users/{user_id}/reset-password` - Reset user password

### System Operations
- `GET /system/snapshot` - Get system statistics
- `POST /system/save` - Save all data
- `POST /system/clear` - Clear all data

## 💻 How to Run

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set the database connection string in `.env`:
```bash
DATABASE_URL=postgresql+psycopg://victor:2323@localhost:5432/banking_db
```

3. Start the API server:
```bash
uvicorn api.app:app --reload
```

4. Access the API documentation at: http://localhost:8000/docs

## 🧪 Testing

Run the test suite:
```bash
pytest tests/test_api.py -v
```

## 📁 Project Structure

```
banking_system/
├── api/
│   ├── app.py              # FastAPI application
│   ├── deps.py             # Authentication dependencies
│   ├── schemas.py          # Pydantic models
│   └── routers/
│       ├── auth.py         # Authentication endpoints
│       ├── accounts.py     # Banking operations
│       └── admin.py        # Admin operations
├── core/
│   └── auth.py             # JWT and password utilities
├── data/
│   └── banking.db          # Legacy SQLite database artifact
├── docs/
│   └── TODO.md             # Project notes
├── domain/
│   ├── account.py          # Account domain model
│   ├── bank.py             # Bank domain model
│   └── user.py             # User domain model
├── services/
│   ├── auth_service.py     # Authentication business logic
│   └── banking_service.py  # Banking business logic
├── persistence/
│   ├── database.py         # SQLAlchemy engine/session setup
│   └── models.py           # Database models
├── scripts/
│   └── migrate_json_to_sqlite.py  # Legacy JSON migration script
└── tests/
    └── test_api.py         # API tests
```
