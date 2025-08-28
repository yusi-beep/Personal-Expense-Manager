from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models.models import Record
from collections import defaultdict
from datetime import datetime

home_bp = Blueprint("home", __name__)

@home_bp.route("/")
@login_required
def index():
    records = Record.query.filter_by(user_id=current_user.id).all()

    income = sum(r.amount for r in records if r.type == "income")
    expense = sum(r.amount for r in records if r.type == "expense")
    balance = income - expense

    # Разходи по категории
    cat_data = defaultdict(float)
    for r in records:
        if r.type == "expense":
            cat_data[r.category] += r.amount

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

    months = sorted(set(monthly_income.keys()) | set(monthly_expense.keys()))

    return render_template("index.html",
        income=round(income, 2),
        expense=round(expense, 2),
        balance=round(balance, 2),
        cat_labels=list(cat_data.keys()),
        cat_values=list(cat_data.values()),
        months=months,
        income_vals=[monthly_income[m] for m in months],
        expense_vals=[monthly_expense[m] for m in months]
    )
