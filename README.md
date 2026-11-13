# BudgeApp
Personal budgeting app built with Streamlit and SQLAlchemy.

## Setup
```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env         # then set your Postgres DATABASE_URL
streamlit run app.py
```
Requires a running PostgreSQL server with an empty database created (e.g. `createdb budgeapp`). Tables are created on first run.

## Project layout
```
app.py                  Streamlit entry point (navigation, DB init)
app_pages/              One file per page
  home.py               Monthly dashboard
  upload.py             File import
  analytics.py          Charts and trends
budgeapp/               Backend package (no Streamlit code)
  db/
    models.py           ORM models (Transaction)
    connection.py       Engine, get_session(), init_db()
    repositories.py     TransactionRepo query helpers
  pipeline/
    extract.py          Read raw rows from files
    transform.py        Clean and categorize rows
    load.py             Save rows to the database
tests/                  pytest suite
```

## Dev
```bash
pytest
ruff check .
```
