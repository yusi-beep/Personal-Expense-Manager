from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.models import db, Category

categories_bp = Blueprint("categories", __name__, url_prefix="/categories")

@categories_bp.route("/", methods=["GET", "POST"])
@login_required
def add_category():
    if request.method == "POST":
        name = (request.form.get("category") or "").strip()
        if not name:
            flash("Category name cannot be empty.", "danger")
            categories = Category.query.filter_by(user_id=current_user.id).all()
            return render_template("add_category.html", categories=categories)

        # check for dublicate (case-insensitive)
        existing = (Category.query
                    .filter(Category.user_id == current_user.id)
                    .filter(db.func.lower(Category.name) == name.lower())
                    .first())
        if existing:
            flash(f"Category '{name}' already exists.", "warning")
            categories = Category.query.filter_by(user_id=current_user.id).all()
            return render_template("add_category.html", categories=categories)

        db.session.add(Category(name=name, user_id=current_user.id))
        db.session.commit()
        flash("Category added.", "success")
        return redirect(url_for("categories.add_category"))

    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template("add_category.html", categories=categories)
