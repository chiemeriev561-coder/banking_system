# Simple Banking System

A basic Python banking system with users, accounts, and transactions whith Encapsulation and Validation with save and load functions.

## 🎯 Key Features
- **Bank management**: Create banks and manage accounts
- **User accounts**: Create users with secure IDs
- **Banking operations**: Deposit, withdraw, check balance
- **Encapsulation**: Protected data with getter/setter methods

## 🔒 Encapsulation Implementation
All classes use **private attributes** (with `__` prefix) and **public methods**:

### Account Class Example
```python
# PRIVATE attributes (can't access directly)
self.__account_number
self.__balance

# PUBLIC methods (safe access)
get_balance()      # Check balance
deposit(amount)    # Add money (with validation)
withdraw(amount)   # Remove money (checks funds)


## 💾 Data Storage
The system now includes **`storage.py`** for saving/loading data:

### Storage Features
- **JSON-based storage**: All data saved in `bank_data.json`
- **Automatic saving**: Save progress before exiting
- **Data integrity**: Error handling for file operations
- **Easy reset**: Clear all data with one command

### How It Works
```python
# Save all data
save_data(bank, users, accounts)

# Load saved data
data = load_data()  # Returns dictionary or None

# Clear all data
clear_data()
## How to run:
1. Open main.py
2. Click the "Run" button (triangle icon)