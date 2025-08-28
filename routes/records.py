from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from models.models import db, Record, Category

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
    if request.method == "POST":
        # base validation 
        category = request.form.get("category")
        if not category:
            categories = Category.query.filter_by(user_id=current_user.id).all()
            return render_template("add.html", categories=categories, error="Please select a category.")

        record = Record(
            date=request.form.get("date") or datetime.now().strftime("%Y-%m-%d"),
            type=request.form["type"],
            category=category,
            amount=float(request.form["amount"]),
            description=request.form["description"],
            user_id=current_user.id
        )
        db.session.add(record)
        db.session.commit()
        return redirect(url_for("records.list_records"))

    # IMPORTANT: with GET show categories for current user
    categories = Category.query.filter_by(user_id=current_user.id).all()
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
