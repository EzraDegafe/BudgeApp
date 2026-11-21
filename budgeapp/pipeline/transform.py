"""Transform: clean raw rows into Transaction-ready records (dates, amounts, types)."""

import logging
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ("DATE", "DESCRIPTION", "AMOUNT", "TRANSACTION_TYPE")

# TRANSACTION_TYPE values that mean money came in. Any other type means money left the
# account, so it's an expense. Add words here if your bank uses others for incoming money.
DEPOSIT_TYPES = {"DEPOSIT", "CREDIT"}

DATE_FORMATS = ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d")


@dataclass
class TxnRecord:
    """One cleaned row, ready to become a Transaction."""

    txn_date: date
    name: str
    txn_type: str  # "deposit" or "expense"
    amount_cents: int  # always positive


@dataclass
class RowError:
    row: int  # row number as shown in Excel (header is row 1)
    reason: str


def _parse_date(text: str) -> date:
    text = text.strip().split(" ")[0]  # Excel sometimes adds a time: "2026-11-19 00:00:00"
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"date {text!r} isn't in a recognised format (expected MM/DD/YYYY)")


def _parse_amount(text: str) -> Decimal:
    cleaned = text.strip().replace("$", "").replace(",", "")
    if cleaned.startswith("(") and cleaned.endswith(")"):  # accounting style: (12.50)
        cleaned = "-" + cleaned[1:-1]
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        raise ValueError(f"amount {text!r} isn't a number") from None


def _parse_type(text: str, amount: Decimal) -> str:
    key = text.strip().upper()
    if not key:  # no type given: fall back to the sign of the amount
        return "expense" if amount < 0 else "deposit"
    return "deposit" if key in DEPOSIT_TYPES else "expense"


def transform(df: pd.DataFrame) -> tuple[list[TxnRecord], list[RowError]]:
    """Clean every row. Good rows become records; bad rows are reported with the reason.

    Raises ValueError if required columns are missing, since no row could be read then.
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        logger.warning("File is missing columns %s (has %s)", missing, list(df.columns))
        raise ValueError(
            f"The file is missing these columns: {', '.join(missing)}. "
            f"Expected: {', '.join(REQUIRED_COLUMNS)}."
        )

    records: list[TxnRecord] = []
    errors: list[RowError] = []
    for i, row in enumerate(df.fillna("").to_dict("records")):
        row_number = i + 2  # +1 for the header, +1 because Excel counts from 1
        try:
            name = re.sub(r"\s+", " ", row["DESCRIPTION"]).strip()
            if not name:
                raise ValueError("description is empty")
            amount = _parse_amount(row["AMOUNT"])
            records.append(
                TxnRecord(
                    txn_date=_parse_date(row["DATE"]),
                    name=name[:255],  # matches the database column size
                    txn_type=_parse_type(row["TRANSACTION_TYPE"], amount),
                    amount_cents=int((abs(amount) * 100).quantize(Decimal(1))),
                )
            )
        except ValueError as exc:
            logger.warning("Row %d skipped: %s", row_number, exc)
            errors.append(RowError(row_number, str(exc)))

    logger.info("Transformed %d rows: %d good, %d with errors", len(df), len(records), len(errors))
    return records, errors
