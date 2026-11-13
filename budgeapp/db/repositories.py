"""Query helpers (repositories) used by the UI and the load step."""

from collections.abc import Iterable
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from budgeapp.db.models import TXN_TYPES, Transaction


class TransactionRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, txn: Transaction) -> Transaction:
        if txn.txn_type not in TXN_TYPES:
            raise ValueError(f"txn_type must be one of {TXN_TYPES}, got {txn.txn_type!r}")
        self.session.add(txn)
        self.session.flush()
        return txn

    def add_many(self, txns: Iterable[Transaction]) -> int:
        count = 0
        for txn in txns:
            self.add(txn)
            count += 1
        return count

    def list_between(self, start: date, end: date) -> list[Transaction]:
        """Transactions with start <= txn_date <= end, newest first."""
        stmt = (
            select(Transaction)
            .where(Transaction.txn_date >= start, Transaction.txn_date <= end)
            .order_by(Transaction.txn_date.desc(), Transaction.id.desc())
        )
        return list(self.session.scalars(stmt))

    def delete(self, txn_id: int) -> bool:
        txn = self.session.get(Transaction, txn_id)
        if txn is None:
            return False
        self.session.delete(txn)
        self.session.flush()
        return True
