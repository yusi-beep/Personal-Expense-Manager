from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.models import db, Record, Category
from decimal import Decimal, InvalidOperation
from datetime import datetime

records_bp = Blueprint("records", __name__, url_prefix="/records")

@records_bp.route("/")
@login_required
def list_records():
    sort = request.args.get("sort", "desc") 
    q = Record.query.filter_by(user_id=current_user.id)

    if sort == "asc":
        records = q.order_by(Record.date.asc()).all()
    else:
        records = q.order_by(Record.date.desc()).all()

    return render_template("records.html", records=records, sort=sort)

@records_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_record():
    categories = Category.query.filter_by(user_id=current_user.id).all()

    if request.method == "POST":
        entry_type = (request.form.get("type") or "").strip().lower()
        category = (request.form.get("category") or "").strip()
        amount_raw = (request.form.get("amount") or "").replace(",", ".").strip()
        date_val = request.form.get("date") or datetime.now().strftime("%Y-%m-%d")
        desc = (request.form.get("description") or "").strip()

        if entry_type not in ("income", "expense"):
            flash("Invalid type. Choose Income or Expense.", "danger")
            return render_template("add.html", categories=categories)

        if not category:
            flash("Please select a category.", "danger")
            return render_template("add.html", categories=categories)

        try:
            amount = Decimal(amount_raw)
            if amount <= 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            flash("Amount must be a positive number.", "danger")
            # върни и въведените стойности, за да не ги пишеш пак (по желание)
            return render_template("add.html", categories=categories)

        rec = Record(
            date=date_val,
            type=entry_type,
            category=category,
            amount=float(amount),  # съхраняваме като float
            description=desc,
            user_id=current_user.id
        )
        db.session.add(rec)
        db.session.commit()
        flash("Record added successfully.", "success")
        return redirect(url_for("records.list_records"))

    return render_template("add.html", categories=categories)

@records_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_record(id):
    record = Record.query.get_or_404(id)
    if record.user_id != current_user.id:
        return "Unauthorized", 403
    if request.method == "POST":
        record.date = request.form.get("date") or record.date
        record.type = request.form["type"]
        record.category = request.form["category"]
        record.amount = float(request.form["amount"])
        record.description = request.form["description"]
        db.session.commit()
        return redirect(url_for("records.list_records"))
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template("edit_record.html", record=record, categories=categories)

@records_bp.route("/delete/<int:id>")
@login_required
def delete_record(id):
    record = Record.query.get_or_404(id)
    if record.user_id != current_user.id:
        return "Unauthorized", 403
    db.session.delete(record)
    db.session.commit()
    return redirect(url_for("records.list_records"))
