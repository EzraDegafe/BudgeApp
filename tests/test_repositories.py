from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from budgeapp.db.models import Base, Transaction
from budgeapp.db.repositories import TransactionRepo


@pytest.fixture
def repo():
    engine = create_engine("sqlite://")  # in-memory
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield TransactionRepo(session)


def make_txn(name="X", txn_date=date(2026, 11, 1), txn_type="expense", amount_cents=100):
    return Transaction(txn_date=txn_date, name=name, txn_type=txn_type, amount_cents=amount_cents)


def test_list_between_filters_and_sorts_newest_first(repo):
    repo.add(make_txn("Old", date(2026, 10, 31)))
    repo.add(make_txn("A", date(2026, 11, 1), txn_type="deposit"))
    repo.add(make_txn("B", date(2026, 11, 5)))

    result = repo.list_between(date(2026, 11, 1), date(2026, 11, 30))

    assert [t.name for t in result] == ["B", "A"]


def test_add_rejects_unknown_type(repo):
    with pytest.raises(ValueError):
        repo.add(make_txn(txn_type="refund"))


def test_delete(repo):
    txn = repo.add(make_txn())
    assert repo.delete(txn.id) is True
    assert repo.delete(txn.id) is False
