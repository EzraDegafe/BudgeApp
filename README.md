# BudgeApp

A personal budgeting app built with [Streamlit](https://streamlit.io) and
[SQLAlchemy](https://www.sqlalchemy.org), backed by PostgreSQL.

You import bank statements and other financial files, and the app turns them into transactions
and shows where your money goes.

> **Status:** early development. Login and the monthly dashboard work. File import and
> analytics are placeholder pages for now.

## Features

| Page      | What it does                                                          | Status      |
|-----------|-----------------------------------------------------------------------|-------------|
| Log in    | Register an account and log in. Each user sees only their own data    | Working     |
| Home      | Income, spending, and net for the current month, plus recent transactions | Working     |
| Import    | Upload CSV, Excel, PDF, or image statements and turn them into transactions | Planned     |
| Analytics | Charts and spending trends over time                                  | Planned     |

## Requirements

- Python 3.11 or newer
- PostgreSQL, running locally or reachable over the network
- *(Optional, for importing images and scanned PDFs later)*
  [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) and
  [Poppler](https://poppler.freedesktop.org/), which `pytesseract` and `pdf2image` need

## Getting started

### 1. Create a virtual environment and install dependencies

```powershell
python -m venv venv
venv\Scripts\activate            # Windows (PowerShell)
# source venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
```

### 2. Create the database

Create an empty Postgres database:

```bash
createdb budgeapp
```

The app creates the tables itself the first time it starts.

### 3. Configure the connection

Copy the example env file and put your credentials in it:

```powershell
copy .env.example .env           # Windows
# cp .env.example .env           # macOS / Linux
```

```ini
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/budgeapp
```

`.env` is in `.gitignore`, so your credentials won't be committed.

### 4. Run the app

```bash
streamlit run app.py
```

Streamlit opens the app in your browser, at http://localhost:8501 by default.

## Project layout

```
app.py                  Streamlit entry point: page config, navigation, one-time DB setup
app_pages/              One file per page (UI only)
  login.py              Log in and register
  home.py               Monthly dashboard
  upload.py             File import (placeholder)
  analytics.py          Charts and trends (placeholder)
budgeapp/               Backend package (no Streamlit code)
  db/
    models.py           ORM models: User, Transaction
    connection.py       Engine, get_session(), init_db(); reads DATABASE_URL from .env
    repositories.py     UserRepo (register, log in) and TransactionRepo query helpers
  auth.py               Password hashing
  pipeline/             Import pipeline (in progress)
    extract.py          Read raw rows from uploaded files
    transform.py        Clean and categorize rows
    load.py             Save records to the database
tests/                  pytest suite (runs against in-memory SQLite)
```

### Data model

- **User**: `username`, `password_hash`, `created_at`. One user has many transactions.
- **Transaction**: `txn_date`, `name`, `txn_type` (`"deposit"` or `"expense"`), `amount_cents`,
  `category`, `is_recurring`, `source` (for example, the name of the imported file), and
  `user_id`.

Amounts are stored as **positive whole numbers of cents** so they don't suffer float rounding
errors. Whether money came in or went out is stored in `txn_type`, not in the sign of the amount.
Divide by 100 when you display an amount.

### Using the database in code

```python
from budgeapp.db.connection import get_session
from budgeapp.db.repositories import TransactionRepo

with get_session() as session:  # commits on success, rolls back on error
    # Scoped to one user: only that user's transactions are returned or changed.
    txns = TransactionRepo(session, st.session_state.user_id).list_between(start, end)
```

Keep Streamlit code in `app_pages/` and database and pipeline logic in `budgeapp/`, so the
backend can be tested without the UI.

## Development

```bash
pytest              # run the tests
ruff check .        # lint
ruff format .       # format
```

The tests use an in-memory SQLite database, so you don't need Postgres to run them.
