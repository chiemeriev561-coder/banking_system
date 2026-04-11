from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from persistence.database import Base
import datetime
from typing import List, Optional

class UserDB(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default="customer")
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    accounts: Mapped[List["AccountDB"]] = relationship("AccountDB", back_populates="owner")
    auth: Mapped[Optional["AuthDB"]] = relationship("AuthDB", back_populates="user", uselist=False)

class AccountDB(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_number: Mapped[str] = mapped_column(String, unique=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    balance: Mapped[float] = mapped_column(Float, default=0.0)

    # Relationships
    owner: Mapped["UserDB"] = relationship("UserDB", back_populates="accounts")
    transactions: Mapped[List["TransactionDB"]] = relationship("TransactionDB", back_populates="account")

class TransactionDB(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"))
    type: Mapped[str] = mapped_column(String) # DEPOSIT, WITHDRAWAL
    amount: Mapped[float] = mapped_column(Float)
    balance_after: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    account: Mapped["AccountDB"] = relationship("AccountDB", back_populates="transactions")

class AuthDB(Base):
    __tablename__ = "auth_credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True)
    password_hash: Mapped[str] = mapped_column(String)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["UserDB"] = relationship("UserDB", back_populates="auth")
