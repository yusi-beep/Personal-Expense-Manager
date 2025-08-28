from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from models.models import Record
from collections import defaultdict
from datetime import datetime, timedelta, date
from sqlalchemy import and_

home_bp = Blueprint("home", __name__)

VALID_SCOPES = {"day", "week", "month", "year"}

def normalize_base_date(scope: str, d: datetime) -> date:
    d = d.date()
    if scope == "day":
        return d
    if scope == "week":
        return d - timedelta(days=d.weekday())  # Monday
    if scope == "month":
        return date(d.year, d.month, 1)
    if scope == "year":
        return date(d.year, 1, 1)
    return d

def prev_next_dates(scope: str, base: date):
    if scope == "day":
        return base - timedelta(days=1), base + timedelta(days=1)
    if scope == "week":
        return base - timedelta(days=7), base + timedelta(days=7)
    if scope == "month":
        y, m = base.year, base.month
        prev_y, prev_m = (y - 1, 12) if m == 1 else (y, m - 1)
        next_y, next_m = (y + 1, 1) if m == 12 else (y, m + 1)
        return date(prev_y, prev_m, 1), date(next_y, next_m, 1)
    if scope == "year":
        return date(base.year - 1, 1, 1), date(base.year + 1, 1, 1)
    return base, base

def period_label(scope: str, base: date) -> str:
    if scope == "day":
        return base.strftime("%Y-%m-%d")
    if scope == "week":
        start = base
        end = base + timedelta(days=6)
        return f"Week {start.strftime('%Y-%m-%d')} – {end.strftime('%Y-%m-%d')}"
    if scope == "month":
        return base.strftime("%Y-%m")
    if scope == "year":
        return base.strftime("%Y")
    return base.isoformat()

def filtered_query(user_id: int, scope: str, base: date):
    """return SQLAlchemy query, filtered by perid for user."""
    q = Record.query.filter(Record.user_id == user_id)
    if scope == "day":
        day_str = base.strftime("%Y-%m-%d")
        return q.filter(Record.date == day_str)
    if scope == "week":
        start_str = base.strftime("%Y-%m-%d")
        end_str   = (base + timedelta(days=6)).strftime("%Y-%m-%d")
        return q.filter(and_(Record.date >= start_str, Record.date <= end_str))
    if scope == "month":
        prefix = base.strftime("%Y-%m")
        return q.filter(Record.date.like(f"{prefix}%"))
    # year
    prefix = base.strftime("%Y")
    return q.filter(Record.date.like(f"{prefix}%"))

@home_bp.route("/")
@login_required
def index():
    scope = request.args.get("scope", "month")
    if scope not in VALID_SCOPES:
        scope = "month"

    # ?date=YYYY-MM-DD or now
    try:
        base_in = datetime.strptime(request.args.get("date", ""), "%Y-%m-%d")
    except Exception:
        base_in = datetime.now()

    base = normalize_base_date(scope, base_in)
    prev_d, next_d = prev_next_dates(scope, base)

    # filtered records from DB, by date for stable charts
    records = (filtered_query(current_user.id, scope, base)
               .order_by(Record.date.asc())
               .all())

    # SUMMARY
    income = sum(r.amount for r in records if r.type == "income")
    expense = sum(r.amount for r in records if r.type == "expense")
    balance = income - expense

    # PIE: expenses / incomes by category
    exp_by_cat = defaultdict(float)
    inc_by_cat = defaultdict(float)
    for r in records:
        if r.type == "expense":
            exp_by_cat[r.category] += r.amount
        elif r.type == "income":
            inc_by_cat[r.category] += r.amount

    # (optional) sort by value
    exp_items = sorted(exp_by_cat.items(), key=lambda x: x[1], reverse=True)
    inc_items = sorted(inc_by_cat.items(), key=lambda x: x[1], reverse=True)

    # MONTHLY BAR (по филтрираните записи)
    monthly_income = defaultdict(float)
    monthly_expense = defaultdict(float)
    for r in records:
        ym = r.date[:7]  # 'YYYY-MM'
        if r.type == "income":
            monthly_income[ym] += r.amount
        else:
            monthly_expense[ym] += r.amount
    months = sorted(set(monthly_income.keys()) | set(monthly_expense.keys()))

    return render_template(
        "index.html",
        income=round(income, 2),
        expense=round(expense, 2),
        balance=round(balance, 2),
        # pies
        cat_labels=[k for k, _ in exp_items],
        cat_values=[v for _, v in exp_items],
        inc_labels=[k for k, _ in inc_items],
        inc_values=[v for _, v in inc_items],
        # bars
        months=months,
        income_vals=[monthly_income[m] for m in months],
        expense_vals=[monthly_expense[m] for m in months],
        # ui state
        scope=scope,
        base_date_str=base.strftime("%Y-%m-%d"),
        prev_date_str=prev_d.strftime("%Y-%m-%d"),
        next_date_str=next_d.strftime("%Y-%m-%d"),
        period_title=period_label(scope, base),
    )
