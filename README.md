# Personal Expense Tracker (Flask)

Simple expense tracking web app with authentication, charts, CSV/PDF export, import and REST API.

## Features
- Auth (register/login) – each user has own records & categories
- CRUD for records & categories
- Charts (pie + monthly bar)
- Filters (category, type, date range, search)
- Pagination
- Export: CSV/PDF; Import: CSV
- REST API + token auth
- SQLite (dev) – easy to switch to Postgres later

## Tech
Flask · Flask-Login · Flask-SQLAlchemy · Chart.js · Bootstrap · ReportLab

---

## Quick start (Local)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # set SECRET_KEY, APP_ENV=development

python app.py
# http://127.0.0.1:5000
