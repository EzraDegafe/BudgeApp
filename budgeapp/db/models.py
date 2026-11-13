"""SQLAlchemy ORM models."""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Allowed values for Transaction.txn_type
TXN_TYPES = ("deposit", "expense")


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # One user -> many transactions. Lets you write user.transactions
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User {self.id} {self.username!r}>"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    txn_date: Mapped[date] = mapped_column(Date, index=True)
    name: Mapped[str] = mapped_column(String(255))
    txn_type: Mapped[str] = mapped_column(String(20))  # "deposit" or "expense"
    # Stored as a positive integer number of cents to avoid float rounding.
    amount_cents: Mapped[int] = mapped_column(Integer)
    category: Mapped[str | None] = mapped_column(String(100), default=None)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str | None] = mapped_column(String(255), default=None)  # e.g. imported file name
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Many transactions -> one user. Lets you write txn.user
    user: Mapped["User"] = relationship(back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction {self.txn_date} {self.name!r} {self.txn_type} {self.amount_cents}>"
