from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime
from models.records import load_categories, load_records, save_record

records_bp = Blueprint("records", __name__, url_prefix="/records")

@records_bp.route("/")
def records():
    records = load_records()
    return render_template("records.html", records=records)

@records_bp.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        date = datetime.now().strftime("%Y-%m-%d")
        entry_type = request.form["type"]
        category = request.form["category"]
        amount = request.form["amount"]
        description = request.form["description"]

        save_record(date, entry_type, category, amount, description)
        return redirect(url_for("records.records"))

    categories = load_categories()
    return render_template("add.html", categories=categories)
