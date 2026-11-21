"""Extract: read raw rows from an uploaded CSV or Excel file."""

import logging
from pathlib import Path
from typing import BinaryIO

import pandas as pd

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = (".csv", ".xlsx")


def read_file(file: BinaryIO, filename: str) -> pd.DataFrame:
    """Read every cell as text, with column names upper-cased and trimmed.

    Raises ValueError if the file type isn't supported or the file can't be read.
    """
    ext = Path(filename).suffix.lower()
    logger.info("Reading %r", filename)
    try:
        if ext == ".csv":
            df = pd.read_csv(file, dtype=str, skip_blank_lines=True)
        elif ext == ".xlsx":
            df = pd.read_excel(file, dtype=str)
        else:
            raise ValueError(
                f"Unsupported file type {ext or '(none)'}. "
                f"Use one of: {', '.join(SUPPORTED_EXTENSIONS)}"
            )
    except ValueError:
        raise
    except Exception as exc:
        logger.exception("Couldn't read %r", filename)
        raise ValueError(f"Couldn't read {filename}: {exc}") from exc

    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.dropna(how="all")  # drop fully empty rows
    logger.info("Read %d rows from %r with columns %s", len(df), filename, list(df.columns))
    return df
