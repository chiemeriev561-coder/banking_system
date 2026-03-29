# Banking System Pylance Error Fix Plan
## Status: In Progress ✅

### 1. ✅ BankingService fully migrated to SQLAlchemy ORM

### 2. [IN PROGRESS] Fix routers Column→str casting

### 2. Fix Pydantic/SQLAlchemy Column type mismatches
   - **api/routers/accounts.py**: Cast Column → str (lines 25-29, etc.)
   - **api/routers/admin.py**: Fix User constructor calls (lines 21,24-26)
   - **api/routers/auth.py**: Fix register user profile return

### 3. Fix AccountDB attribute access issues
   - **api/routers/accounts.py**: Ensure AccountDB has expected attrs
   - Cast `str(account.account_number)`, `float(account.balance)`

### 4. Refactor test_api.py
   - Remove domain model mixing (direct BankingService calls)
   - Use proper DB/service patterns or API client tests

### 5. Fix services/banking_service.py
   - Remove persistence.store import
   - Ensure consistent DB model usage

### 6. [PENDING] Final validation
   - Run pytest
   - Restart Pylance
   - Test API endpoints
   - attempt_completion

**Progress:** BankingService partially migrated to SQLAlchemy (get_accounts, get_detail, deposit, withdraw, statement)
**Next:** create_account, snapshot, routers
