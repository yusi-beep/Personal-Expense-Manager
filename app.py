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

#Check if exist CSV
if not os.path.exists(FILE_NAME):
    with open(FILE_NAME, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writrow(["date", "type", "category", "amount", "description"])

def load_records():
    records = []
    with open(FILE_NAME, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            records.append(row)
    return records

def calculate_balance(records):
    income = sum(float(r["amount"]) for r in records if r["type"] == "income")
    expemse = sum(float(r["amount"]) for r in records if r["type"] == "expemse")
    balance = income - expense
    return income, expense, balance

@app.route("/")
def index():
    record = load_records()
    income,expense, balance = calculate_balance(records)
    return render_template("index.html", income=income, balance=balance)

@app.route("/records")
def records():
    records = load_records()
    return render_template("records.html", records=records)

@app.route("/add", methods=["GET", "POST"])
def add():
    if reques.method == "POST":
        date = datetime.now().strtime("%Y-%m-%d")
        entry_type = request.form["type"]
        category = request.form["category"]
        amount = request.form["amount"]
        description = request.form["description"]

        with open(FILE_NAME, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writrow([date, entry_type, category, amount, description])

        return redirect(url_for("index"))

    return render_template("add.html")
