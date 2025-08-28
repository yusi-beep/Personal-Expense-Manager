from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.models import db, Record, Category
from sqlalchemy import func


categories_bp = Blueprint("categories", __name__, url_prefix="/categories")

@categories_bp.route("/", methods=["GET", "POST"])
@login_required
def add_category():
    categories = Category.query.filter_by(user_id=current_user.id).all()

    if request.method == "POST":
        name = (request.form.get("category") or "").strip()
        if not name:
            flash("Category name cannot be empty.", "danger")
            return render_template("add_category.html", categories=categories)

        name = name.title()[:50]

        # check for dublicate (case-insensitive)
        existing = (Category.query
            .filter(Category.user_id == current_user.id)
            .filter(func.lower(Category.name) == name.lower())
            .first())

        if existing:
            flash(f"Category '{name}' already exists.", "warning")
            return render_template("add_category.html", categories=categories)

        db.session.add(Category(name=name, user_id=current_user.id))
        db.session.commit()
        flash("Category added.", "success")
        return redirect(url_for("categories.add_category"))

    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template("add_category.html", categories=categories)

@categories_bp.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_category(id):
    cat = Category.query.get_or_404(id)
    if cat.user_id != current_user.id:
        return "Unauthorized", 403

    in_use = Record.query.filter_by(user_id=current_user.id, category=cat.name).count()
    if in_use > 0:
        flash(f"Cannot delete '{cat.name}' – it is used by {in_use} record(s).", "warning")
        return redirect(url_for("categories.add_category"))

    db.session.delete(cat)
    db.session.commit()
    flash("Category deleted.", "success")
    return redirect(url_for("categories.add_category"))

@categories_bp.route("/rename/<int:id>", methods=["POST"])
@login_required
def rename_category(id):
    cat = Category.query.get_or_404(id)
    if cat.user_id != current_user.id:
        return "Unauthorized", 403

    new_name = (request.form.get("new_name") or "").strip()
    if not new_name:
        flash("New name cannot be empty.", "danger")
        return redirect(url_for("categories.add_category"))
    new_name = new_name.title()[:50]

    # dublicates (case-insensitive)
    dup = (Category.query
           .filter(Category.user_id == current_user.id)
           .filter(func.lower(Category.name) == new_name.lower())
           .first())
    if dup and dup.id != id:
        flash(f"Category '{new_name}' already exists.", "warning")
        return redirect(url_for("categories.add_category"))

    old_name = cat.name
    cat.name = new_name
    db.session.flush()  # new name, but stil not commit

    # renew user records with this category
    (Record.query
     .filter_by(user_id=current_user.id, category=old_name)
     .update({Record.category: new_name}))
    db.session.commit()

    flash(f"Category renamed to '{new_name}'.", "success")
    return redirect(url_for("categories.add_category"))

