from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from models.models import db, Category

categories_bp = Blueprint("categories", __name__, url_prefix="/categories")

@categories_bp.route("/", methods=["GET", "POST"])
@login_required
def add_category():
    if request.method == "POST":
        category = Category(name=request.form["category"], user_id=current_user.id)
        db.session.add(category)
        db.session.commit()
        return redirect(url_for("categories.add_category"))

    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template("add_category.html", categories=categories)
