from flask import Flask, render_template, request, redirect, url_for

import csv
import os
from datetime import datetime
from collections import defaultdict
import matplotlib
matplotlib.use('Agg') #to work without GUI
import matplotlib.pyplot as pyplot
app = Flask(__name__)

FILE_NAME = "expenses.csv"
CATEGORY_FILE = "categories.csv"

#Check if exist CSV
if not os.path.exists(FILE_NAME):
    with open(FILE_NAME, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writrow(["date", "type", "category", "amount", "description"])

if not os.path.exists(CATEGORY_FILE):
    with open(CATEGORY_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["category"])

def load_records():
    records = []
    with open(FILE_NAME, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            records.append(row)
    return records

def load_categories():
    categories = []
    with open(CATEGORY_FILE, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            categories.append(row["category"])
    return categories

def calculate_balance(records):
    income = round(sum(float(r["amount"]) for r in records if r["type"] == "income"),2)
    expense = round(sum(float(r["amount"]) for r in records if r["type"] == "expense"),2)
    balance = round(income - expense,2)
    return income, expense, balance

def expenses_by_category(records):
    categories = defaultdict(float)
    for r in records:
        if r["type"] == "expense":
            categories[r["category"]] += float(r["amount"])
    return categories

def monthly_summary(records):
    monthly_income = defaultdict(float)
    monthly_expense = defaultdict(float)

    for r in records:
        date_obj = datetime.strptime(r["date"], "%Y-%m-%d")
        year_month = date_obj.strftime("%Y-%m")
        amount = float(r["amount"])
        if r["type"] == "income":
            monthly_income[year_month] += amount
        elif r["type"] == "expense":
            monthly_expense[year_month] += amount

    months = sorted(set(list(monthly_income.keys()) + list(monthly_expense.keys())))
    income_vals = [monthly_income[m] for m in months]
    expense_vals = [monthly_expense[m] for m in months]

    return months, income_vals, expense_vals

@app.route("/")
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

@app.route("/records")
def records():
    records = load_records()
    return render_template("records.html", records=records)

@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    if request.method == "POST":
        category = request.form["category"].strip()
        if category:  # add only if not empty
            with open(CATEGORY_FILE, "a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow([category])
            return redirect(url_for("add_category"))

    categories = load_categories()
    return render_template("add_category.html", categories=categories)

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        date = datetime.now().strftime("%Y-%m-%d")
        entry_type = request.form["type"]
        category = request.form["category"]
        amount = request.form["amount"]
        description = request.form["description"]

        with open(FILE_NAME, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([date, entry_type, category, amount, description])

        return redirect(url_for("index"))

    categories = load_categories()
    return render_template("add.html", categories=categories)

if __name__ == "__main__":
    app.run(debug=True)