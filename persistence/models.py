from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from persistence.database import Base
import datetime

class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    name = Column(String)
    role = Column(String, default="customer")
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    # Relationships
    accounts = relationship("AccountDB", back_populates="owner")
    auth = relationship("AuthDB", back_populates="user", uselist=False)

class AccountDB(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    account_number = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    balance = Column(Float, default=0.0)

    # Relationships
    owner = relationship("UserDB", back_populates="accounts")
    transactions = relationship("TransactionDB", back_populates="account")

class TransactionDB(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    type = Column(String) # DEPOSIT, WITHDRAWAL
    amount = Column(Float)
    balance_after = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    account = relationship("AccountDB", back_populates="transactions")

class AuthDB(Base):
    __tablename__ = "auth_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    password_hash = Column(String)
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("UserDB", back_populates="auth")
