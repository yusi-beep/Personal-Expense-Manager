from flask import Blueprint, render_template, request, url_for
from flask_login import login_required, current_user
from models.models import Record
from collections import defaultdict
from datetime import datetime, timedelta, date

home_bp = Blueprint("home", __name__)

def normalize_base_date(scope: str, d: datetime) -> date:
    d = d.date()
    if scope == "day":
        return d
    if scope == "week":
        # ISO: Monday as start
        return d - timedelta(days=d.weekday())
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
        # prev month first day
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

@home_bp.route("/")
@login_required
def index():
    scope = request.args.get("scope", "month")  # day | week | month | year

    # if POST ?date=YYYY-MM-DD - use it, else today
    try:
        base_in = datetime.strptime(request.args.get("date", ""), "%Y-%m-%d")
    except Exception:
        base_in = datetime.now()

    base = normalize_base_date(scope, base_in)
    prev_d, next_d = prev_next_dates(scope, base)

    #load data for current user
    all_records = Record.query.filter_by(user_id=current_user.id).all()

    # period filter
    if scope == "day":
        records = [r for r in all_records if r.date == base.strftime("%Y-%m-%d")]
    elif scope == "week":
        start = base
        end = base + timedelta(days=6)
        records = [r for r in all_records if start.strftime("%Y-%m-%d") <= r.date <= end.strftime("%Y-%m-%d")]
    elif scope == "month":
        prefix = base.strftime("%Y-%m")
        records = [r for r in all_records if r.date.startswith(prefix)]
    else:  # year
        prefix = base.strftime("%Y")
        records = [r for r in all_records if r.date.startswith(prefix)]

    # summary
    income = sum(r.amount for r in records if r.type == "income")
    expense = sum(r.amount for r in records if r.type == "expense")
    balance = income - expense

    # pie (expenses / incomes by category)
    exp_by_cat = defaultdict(float)
    inc_by_cat = defaultdict(float)
    for r in records:
        if r.type == "expense":
            exp_by_cat[r.category] += r.amount
        else:
            inc_by_cat[r.category] += r.amount

    # Income/expense for months
    monthly_income = defaultdict(float)
    monthly_expense = defaultdict(float)
    for r in records:
        date_obj = datetime.strptime(r.date, "%Y-%m-%d")
        ym = date_obj.strftime("%Y-%m")
        if r.type == "income":
            monthly_income[ym] += r.amount
        else:
            monthly_expense[ym] += r.amount

    # monthly bar – върху филтрираните записи (можеш да го оставиш или да го правиш винаги глобално)
    monthly_income = defaultdict(float)
    monthly_expense = defaultdict(float)
    for r in records:
        ym = r.date[:7]
        if r.type == "income":
            monthly_income[ym] += r.amount
        else:
            monthly_expense[ym] += r.amount
    months = sorted(set(monthly_income.keys()) | set(monthly_expense.keys()))

    return render_template(
        "index.html",
        # summary
        income=round(income, 2),
        expense=round(expense, 2),
        balance=round(balance, 2),
        # pies
        cat_labels=list(exp_by_cat.keys()),
        cat_values=list(exp_by_cat.values()),
        inc_labels=list(inc_by_cat.keys()),
        inc_values=list(inc_by_cat.values()),
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
