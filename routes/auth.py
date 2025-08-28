from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from models.models import db, User
from sqlalchemy import func

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home.index"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()

        # base validation
        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template("register.html", username=username)

        if len(username) < 3:
            flash("Username must be at least 3 characters.", "danger")
            return render_template("register.html", username=username)

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html", username=username)

        # dublicates (case-insensitive)
        existing_user = User.query.filter(func.lower(User.username) == username.lower()).first()
        if existing_user:
            flash("Username is already taken.", "warning")
            return render_template("register.html", username=username)

        # generate hash (default pbkdf2:sha256)
        hashed_pw = generate_password_hash(password)
        user = User(username=username, password=hashed_pw)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home.index"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()
        remember = request.form.get("remember") == "on"
        next_url = request.args.get("next") or url_for("home.index")

        user = User.query.filter(func.lower(User.username) == username.lower()).first()

        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember)
            flash("Welcome back!", "success")
            return redirect(next_url)

        flash("Invalid username or password.", "danger")
        # return entered username for confort
        return render_template("login.html", username=username)

    # GET
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
