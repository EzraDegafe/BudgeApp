from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from budgeapp.auth import hash_password, verify_password
from budgeapp.db.models import Base, Transaction
from budgeapp.db.repositories import TransactionRepo, UserRepo


@pytest.fixture
def session():
    engine = create_engine("sqlite://")  # in-memory
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def users(session):
    return UserRepo(session)


@pytest.fixture
def repo(session, users):
    return TransactionRepo(session, users.register("alice", "pw").id)


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


def test_users_only_see_their_own_transactions(session, users, repo):
    bob = TransactionRepo(session, users.register("bob", "pw").id)
    txn = repo.add(make_txn("Alice's"))
    bob.add(make_txn("Bob's"))

    assert [t.name for t in repo.list_between(date(2026, 1, 1), date(2026, 12, 31))] == ["Alice's"]
    assert bob.delete(txn.id) is False


def test_register_and_authenticate(users):
    users.register("carol", "secret")

    assert users.authenticate("carol", "secret") is not None
    assert users.authenticate("carol", "wrong") is None
    assert users.authenticate("nobody", "secret") is None


def test_register_rejects_duplicate_username(users):
    users.register("dave", "pw")
    with pytest.raises(ValueError):
        users.register("dave", "other")


def test_password_is_hashed_with_random_salt():
    first, second = hash_password("pw"), hash_password("pw")
    assert first != second and "pw" not in first
    assert verify_password("pw", first) and verify_password("pw", second)
    assert not verify_password("pw", "not-a-hash")
