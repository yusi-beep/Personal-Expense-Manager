from flask import Blueprint, render_template, request, redirect, url_for
from models.records import load_categories, save_category

categories_bp = Blueprint("categories", __name__, url_prefix="/categories")

@categories_bp.route("/", methods=["GET", "POST"])
def add_category():
    if request.method == "POST":
        category = request.form["category"]
        save_category(category)
        return redirect(url_for("categories.add_category"))

    categories = load_categories()
    return render_template("add_category.html", categories=categories)


