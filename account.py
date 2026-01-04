class Account:
    def __init__(self, account_number, user, balance=0):
        # Private attributes
        self.__account_number = account_number
        self.__user = user
        self.__balance = balance
        self.__transactions = []  # Track transaction history
        
        # Record initial deposit if starting balance > 0
        if balance > 0:
            self.__transactions.append({
                "type": "DEPOSIT",
                "amount": balance,
                "balance_after": balance
            })
    
    # Getter methods
    def get_account_number(self):
        return self.__account_number
    
    def get_user(self):
        return self.__user
    
    def get_balance(self):
        return self.__balance
    
    def get_transactions(self):
        return self.__transactions.copy()  # Return copy for encapsulation
    
    # Banking methods
    def deposit(self, amount):
        if amount > 0:
            self.__balance += amount
            self.__transactions.append({
                "type": "DEPOSIT",
                "amount": amount,
                "balance_after": self.__balance
            })
            return True
        return False
    
    def withdraw(self, amount):
        if 0 < amount <= self.__balance:
            self.__balance -= amount
            self.__transactions.append({
                "type": "WITHDRAWAL",
                "amount": amount,
                "balance_after": self.__balance
            })
            return True
        return False
    
    def show_statement(self):
        """Print transaction history"""
        print(f"\n📝 STATEMENT FOR ACCOUNT {self.__account_number}")
        print(f"Holder: {self.__user.get_name()}")
        print(f"Current Balance: ${self.__balance:.2f}")
        print("\nRecent Transactions:")
        
        if not self.__transactions:
            print("  No transactions yet")
            return
        
        for i, trans in enumerate(self.__transactions[-10:]):  # Last 10 transactions
            sign = "+" if trans["type"] == "DEPOSIT" else "-"
            print(f"  {trans['type']}: {sign}${trans['amount']:.2f} | Balance: ${trans['balance_after']:.2f}")