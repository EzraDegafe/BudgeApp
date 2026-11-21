"""Query helpers (repositories) used by the UI and the load step."""

from collections.abc import Iterable
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from budgeapp.auth import hash_password, verify_password
from budgeapp.db.models import TXN_TYPES, Transaction, User


class UserRepo:
    def __init__(self, session: Session):
        self.session = session

    def get_by_username(self, username: str) -> User | None:
        return self.session.scalar(select(User).where(User.username == username))

    def register(self, username: str, password: str) -> User:
        """Create a user. Raises ValueError if the username is taken."""
        if self.get_by_username(username) is not None:
            raise ValueError(f"Username {username!r} is already taken")
        user = User(username=username, password_hash=hash_password(password))
        self.session.add(user)
        self.session.flush()
        return user

    def authenticate(self, username: str, password: str) -> User | None:
        """Return the user if the username and password match, else None."""
        user = self.get_by_username(username)
        if user is None or not verify_password(password, user.password_hash):
            return None
        return user


class TransactionRepo:
    """Transactions for one user. Every query is limited to that user's rows."""

    def __init__(self, session: Session, user_id: int):
        self.session = session
        self.user_id = user_id

    def add(self, txn: Transaction) -> Transaction:
        if txn.txn_type not in TXN_TYPES:
            raise ValueError(f"txn_type must be one of {TXN_TYPES}, got {txn.txn_type!r}")
        txn.user_id = self.user_id
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
            .where(
                Transaction.user_id == self.user_id,
                Transaction.txn_date >= start,
                Transaction.txn_date <= end,
            )
            .order_by(Transaction.txn_date.desc(), Transaction.id.desc())
        )
        return list(self.session.scalars(stmt))

    def delete(self, txn_id: int) -> bool:
        txn = self.session.get(Transaction, txn_id)
        if txn is None or txn.user_id != self.user_id:
            return False
        self.session.delete(txn)
        self.session.flush()
        return True
