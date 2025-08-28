from flask import Blueprint, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from models.models import db, User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Проверка дали потребителят вече съществува
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template("register.html", error="Username already taken")

        hashed_pw = generate_password_hash(password, method="pbkdf2:sha256")
        user = User(username=username, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("auth.login"))

    return render_template("register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("home.index"))

    return render_template("login.html", error="Invalid username or password")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
