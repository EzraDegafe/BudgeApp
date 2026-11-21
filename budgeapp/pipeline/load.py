"""Load: write transformed records to the database via TransactionRepo."""

import logging
from collections import Counter
from dataclasses import dataclass

from sqlalchemy.orm import Session

from budgeapp.db.models import Transaction
from budgeapp.db.repositories import TransactionRepo
from budgeapp.pipeline.transform import TxnRecord

logger = logging.getLogger(__name__)


@dataclass
class LoadResult:
    added: int
    skipped_duplicates: int


def _key(txn_date, name, txn_type, amount_cents) -> tuple:
    return (txn_date, name, txn_type, amount_cents)


def load(session: Session, user_id: int, records: list[TxnRecord], source: str) -> LoadResult:
    """Save records for a user, skipping ones that are already in the database.

    Duplicates are counted, not just matched: if the database has one "$20 Zelle on 11/19" and
    the file has two, one more is added. So re-uploading a file adds nothing, but two genuine
    identical transactions on the same day are both kept.
    """
    if not records:
        return LoadResult(added=0, skipped_duplicates=0)

    repo = TransactionRepo(session, user_id)
    start = min(r.txn_date for r in records)
    end = max(r.txn_date for r in records)
    already_saved = Counter(
        _key(t.txn_date, t.name, t.txn_type, t.amount_cents) for t in repo.list_between(start, end)
    )

    new_txns = []
    skipped = 0
    for r in records:
        key = _key(r.txn_date, r.name, r.txn_type, r.amount_cents)
        if already_saved[key] > 0:
            already_saved[key] -= 1
            skipped += 1
            continue
        new_txns.append(
            Transaction(
                txn_date=r.txn_date,
                name=r.name,
                txn_type=r.txn_type,
                amount_cents=r.amount_cents,
                source=source[:255],
            )
        )

    added = repo.add_many(new_txns)
    logger.info(
        "Import of %r for user %s: %d added, %d skipped as already imported",
        source,
        user_id,
        added,
        skipped,
    )
    return LoadResult(added=added, skipped_duplicates=skipped)
