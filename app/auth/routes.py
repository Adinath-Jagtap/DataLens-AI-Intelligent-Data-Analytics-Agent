# ── Google OAuth setup ────────────────────────────────────────────────────────
# 1. console.cloud.google.com → APIs & Services → Credentials
# 2. Create OAuth 2.0 Client ID → Web application
# 3. Authorized redirect URIs:
#      http://localhost:5000/oauth/google/authorized        (dev)
#      https://your-app.onrender.com/oauth/google/authorized (prod)
# 4. Copy Client ID + Secret → .env

# ── GitHub OAuth setup ────────────────────────────────────────────────────────
# 1. github.com → Settings → Developer settings → OAuth Apps → New OAuth App
# 2. Homepage URL: https://your-app.onrender.com
# 3. Authorization callback URL:
#      https://your-app.onrender.com/oauth/github/authorized
# 4. Copy Client ID + Secret → .env

import bcrypt
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_dance.contrib.google import google
from flask_dance.contrib.github import github
from app.models import create_user, get_user_by_email, get_or_create_oauth_user
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


# ── OAuth initiation ─────────────────────────────────────────────────────────

@auth_bp.route("/login/google")
def login_google():
    return redirect(url_for("google.login"))


@auth_bp.route("/login/github")
def login_github():
    return redirect(url_for("github.login"))


# ── Google callback ──────────────────────────────────────────────────────────

@auth_bp.route("/oauth/google/callback")
def oauth_google_callback():
    if not google.authorized:
        flash("Google sign-in was cancelled.", "error")
        return redirect(url_for("auth.login"))
    try:
        resp = google.get("/oauth2/v2/userinfo")
        if not resp.ok:
            raise ValueError(f"Google API returned {resp.status_code}")

        info        = resp.json()
        provider_id = str(info.get("id") or info.get("sub", ""))
        email       = info.get("email", "").strip()
        name        = info.get("name") or info.get("given_name") or email.split("@")[0]

        if not email:
            flash("Google did not return an email. Use email/password login instead.", "error")
            return redirect(url_for("auth.login"))

        user, is_new = get_or_create_oauth_user("google", provider_id, email, name)
        login_user(user)
        flash(
            f"Welcome to DataLens AI, {user.display_name}!" if is_new
            else f"Welcome back, {user.display_name}!",
            "success"
        )
        return redirect(request.args.get("next") or url_for("main.home"))

    except Exception as e:
        flash(f"Google sign-in failed: {str(e)[:120]}", "error")
        return redirect(url_for("auth.login"))


# ── GitHub callback ──────────────────────────────────────────────────────────

@auth_bp.route("/oauth/github/callback")
def oauth_github_callback():
    if not github.authorized:
        flash("GitHub sign-in was cancelled.", "error")
        return redirect(url_for("auth.login"))
    try:
        resp = github.get("/user")
        if not resp.ok:
            raise ValueError(f"GitHub API returned {resp.status_code}")

        info        = resp.json()
        provider_id = str(info.get("id", ""))
        name        = info.get("name") or info.get("login") or "GitHub User"
        email       = info.get("email")

        # GitHub may hide primary email — fetch from /user/emails
        if not email:
            emails_resp = github.get("/user/emails")
            if emails_resp.ok:
                email = next(
                    (e["email"] for e in emails_resp.json()
                     if e.get("primary") and e.get("verified")),
                    None
                )

        if not email:
            flash(
                "GitHub did not return a verified email. "
                "Go to github.com → Settings → Emails and make your email public.",
                "error"
            )
            return redirect(url_for("auth.login"))

        user, is_new = get_or_create_oauth_user("github", provider_id, email, name)
        login_user(user)
        flash(
            f"Welcome to DataLens AI, {user.display_name}!" if is_new
            else f"Welcome back, {user.display_name}!",
            "success"
        )
        return redirect(request.args.get("next") or url_for("main.home"))

    except Exception as e:
        flash(f"GitHub sign-in failed: {str(e)[:120]}", "error")
        return redirect(url_for("auth.login"))
