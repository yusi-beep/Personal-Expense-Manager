from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime
from models.records import load_categories, load_records, save_record, overwrite_records

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

@records_bp.route("/edit/<int:index>", methods=["GET", "POST"])
def edit_record(index):
    records = load_records()
    record = records[index]

    if request.method == "POST":
        # Renew values
        record["type"] = request.form["type"]
        record["category"] = request.form["category"]
        record["amount"] = request.form["amount"]
        record["description"] = request.form["description"]

        overwrite_records(records)  # Save all in CSV
        return redirect(url_for("records.records"))

    return render_template("edit_record.html", record=record, index=index)

@records_bp.route("/delete/<int:index>")
def delete_record(index):
    records = load_records()
    records.pop(index)  # delete with index
    overwrite_records(records)
    return redirect(url_for("records.records"))
