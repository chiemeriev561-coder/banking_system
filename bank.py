class Bank:
    def __init__(self, name):
        self.__name = name
        self.__accounts = []
    
    def get_name(self):
        return self.__name
    
    def get_accounts(self):
        return self.__accounts.copy()  # Return copy for encapsulation
    
    def add_account(self, account):
        self.__accounts.append(account)
    
    def find_account(self, account_number):
        for account in self.__accounts:
            if account.get_account_number() == account_number:
                return account
        return None
    
    def get_total_balance(self):
        """Get total of all account balances"""
        total = 0
        for account in self.__accounts:
            total += account.get_balance()
        return total