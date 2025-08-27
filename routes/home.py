from flask import Blueprint, render_template
from models.records import load_records, calculate_balance, expenses_by_category, monthly_summary

home_bp = Blueprint("home", __name__)

@home_bp.route("/")
def index():
    records = load_records()
    income, expense, balance = calculate_balance(records)

    cat_data = expenses_by_category(records)
    months, income_vals, expense_vals = monthly_summary(records)

    return render_template(
        "index.html",
        income=income,
        expense=expense,
        balance=balance,
        cat_labels=list(cat_data.keys()) if cat_data else [],
        cat_values=list(cat_data.values()) if cat_data else [],
        months=months if months else [],
        income_vals=income_vals if income_vals else [],
        expense_vals=expense_vals if expense_vals else []
    )
