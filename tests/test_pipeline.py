import io
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from budgeapp.db.models import Base
from budgeapp.db.repositories import TransactionRepo, UserRepo
from budgeapp.pipeline.extract import read_file
from budgeapp.pipeline.load import load
from budgeapp.pipeline.transform import transform

# Real rows from the bank export, kept on one line each (long lines are allowed in tests).
BANK_CSV = """DATE,DESCRIPTION,AMOUNT,TRANSACTION_TYPE
11/19/2026,ONLINE TRANSFER FROM WOLDEYES Z REF #IB045V9J2L EVERYDAY CHECKING FOR CAR INSURANCE,217,DEPOSIT
11/19/2026,ONLINE TRANSFER FROM WOLDEYES Z EVERYDAY CHECKING XXXXXX8195 REF #IB045V8CM4 ON 11/19/26,2000,DEPOSIT
11/19/2026,ONLINE TRANSFER FROM YOSEFE M EVERYDAY CHECKING XXXXXXXXX9887 REF #IB045QJMKV ON 11/19/26,446.52,DEPOSIT
11/19/2026,ZELLE FROM RIZIG MICHAEL ON 11/19 REF # WFCT22X32SSX POOL TABLE,20,DEPOSIT
"""


def read_csv(text: str):
    return read_file(io.BytesIO(text.encode()), "statement.csv")


@pytest.fixture
def session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_bank_csv_transforms_cleanly():
    records, errors = transform(read_csv(BANK_CSV))

    assert errors == []
    assert len(records) == 4
    assert records[0].txn_date == date(2026, 11, 19)
    assert records[0].txn_type == "deposit"
    assert [r.amount_cents for r in records] == [21700, 200000, 44652, 2000]


def test_bad_rows_are_reported_not_imported():
    csv = """DATE,DESCRIPTION,AMOUNT,TRANSACTION_TYPE
11/19/2026,Groceries,"$1,234.50",WITHDRAWAL
not a date,Coffee,4.50,DEBIT
11/20/2026,Lunch,abc,DEBIT
11/21/2026,No type given,-12.25,
"""
    records, errors = transform(read_csv(csv))

    assert [(r.name, r.txn_type, r.amount_cents) for r in records] == [
        ("Groceries", "expense", 123450),
        ("No type given", "expense", 1225),
    ]
    assert [e.row for e in errors] == [3, 4]
    assert "date" in errors[0].reason
    assert "amount" in errors[1].reason


def test_any_type_other_than_deposit_is_an_expense():
    csv = """DATE,DESCRIPTION,AMOUNT,TRANSACTION_TYPE
11/19/2026,Paycheck,1500,deposit
11/19/2026,Rent,1200,CHECK
11/19/2026,Gas,40,POS PURCHASE
11/19/2026,Venmo,25,TRANSFER
"""
    records, errors = transform(read_csv(csv))

    assert errors == []
    assert [r.txn_type for r in records] == ["deposit", "expense", "expense", "expense"]


def test_missing_columns_explains_what_is_needed():
    with pytest.raises(ValueError, match="TRANSACTION_TYPE"):
        transform(read_csv("DATE,DESCRIPTION,AMOUNT\n11/19/2026,X,1\n"))


def test_unsupported_file_type():
    with pytest.raises(ValueError, match="Unsupported"):
        read_file(io.BytesIO(b""), "statement.pdf")


def test_reimporting_the_same_file_adds_nothing(session):
    user_id = UserRepo(session).register("ezra", "pw").id
    records, _ = transform(read_csv(BANK_CSV))

    first = load(session, user_id, records, source="statement.csv")
    second = load(session, user_id, records, source="statement.csv")

    assert (first.added, first.skipped_duplicates) == (4, 0)
    assert (second.added, second.skipped_duplicates) == (0, 4)
    saved = TransactionRepo(session, user_id).list_between(date(2026, 11, 1), date(2026, 11, 30))
    assert len(saved) == 4


def test_identical_transactions_in_one_file_are_both_kept(session):
    user_id = UserRepo(session).register("ezra", "pw").id
    csv = """DATE,DESCRIPTION,AMOUNT,TRANSACTION_TYPE
11/19/2026,COFFEE,4.50,DEBIT
11/19/2026,COFFEE,4.50,DEBIT
"""
    records, _ = transform(read_csv(csv))

    assert load(session, user_id, records, source="a.csv").added == 2
