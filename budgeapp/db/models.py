"""SQLAlchemy ORM models."""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Allowed values for Transaction.txn_type
TXN_TYPES = ("deposit", "expense")


class Base(DeclarativeBase):
    pass


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    txn_date: Mapped[date] = mapped_column(Date, index=True)
    name: Mapped[str] = mapped_column(String(255))
    txn_type: Mapped[str] = mapped_column(String(20))  # "deposit" or "expense"
    # Stored as a positive integer number of cents to avoid float rounding.
    amount_cents: Mapped[int] = mapped_column(Integer)
    category: Mapped[str | None] = mapped_column(String(100), default=None)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str | None] = mapped_column(String(255), default=None)  # e.g. imported file name
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<Transaction {self.txn_date} {self.name!r} {self.txn_type} {self.amount_cents}>"
