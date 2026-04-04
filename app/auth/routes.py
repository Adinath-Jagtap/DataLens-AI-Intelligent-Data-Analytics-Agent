import bcrypt
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import create_user, get_user_by_email
from flask import current_app

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        name     = request.form.get("display_name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.", "error")
            return render_template("auth/register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("auth/register.html")

        if get_user_by_email(email):
            flash("An account with that email already exists.", "error")
            return render_template("auth/register.html")

        pw_hash  = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        is_admin = (email == current_app.config["ADMIN_EMAIL"])
        user     = create_user(name, email, pw_hash, is_admin)

        login_user(user)
        flash(f"Welcome, {name}!", "success")
        return redirect(url_for("main.home"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = get_user_by_email(email)
        if not user or not user.password_hash:
            flash("Invalid email or password.", "error")
            return render_template("auth/login.html")

        if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            flash("Invalid email or password.", "error")
            return render_template("auth/login.html")

        login_user(user)
        flash(f"Welcome back, {user.display_name}!", "success")
        next_page = request.args.get("next")
        return redirect(next_page or url_for("main.home"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You've been signed out.", "success")
    return redirect(url_for("auth.login"))
