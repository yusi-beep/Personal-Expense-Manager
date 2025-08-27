import csv
import os
from collections import defaultdict
from datetime import datetime

FILE_NAME = "expenses.csv"
CATEGORY_FILE = "categories.csv"

# Проверка за CSV файлове
if not os.path.exists(FILE_NAME):
    with open(FILE_NAME, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["date", "type", "category", "amount", "description"])

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

def save_record(date, entry_type, category, amount, description):
    with open(FILE_NAME, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([date, entry_type, category, amount, description])

def load_categories():
    categories = []
    with open(CATEGORY_FILE, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            categories.append(row["category"])
    return categories

def save_category(category):
    with open(CATEGORY_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([category])

def calculate_balance(records):
    income = round(sum(float(r["amount"]) for r in records if r["type"] == "income"), 2)
    expense = round(sum(float(r["amount"]) for r in records if r["type"] == "expense"), 2)
    balance = round(income - expense, 2)
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
    