from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from ...extensions import db
from ...models.user import User
from ...services import email_service

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or len(password) < 6:
            flash("Please fill all fields. Password must be at least 6 characters.", "error")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "error")
            return render_template("auth/register.html")

        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(f"Welcome to StudyMate AI, {user.name}!", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash("Welcome back!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.index"))

        flash("Invalid email or password.", "error")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()

        # Always show the same message whether or not the account exists,
        # so this endpoint can't be used to check which emails are registered.
        generic_message = "If an account exists for that email, a reset link has been sent."

        if user:
            token = user.generate_reset_token()
            db.session.commit()
            reset_url = url_for("auth.reset_password", token=token, _external=True)

            sent = email_service.send_email(
                user.email,
                "Reset your StudyMate AI password",
                f"Hi {user.name},\n\nClick the link below to reset your password. "
                f"This link expires in 1 hour.\n\n{reset_url}\n\n"
                f"If you didn't request this, you can safely ignore this email.",
            )
            if sent:
                flash(generic_message, "info")
            else:
                # No SMTP configured (or sending failed) — fall back to
                # showing the link directly so the flow still works.
                flash(generic_message, "info")
                flash(f"Email isn't configured yet — here's your reset link: {reset_url}", "info")
        else:
            flash(generic_message, "info")

        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.verify_reset_token(token):
        flash("That reset link is invalid or has expired. Please request a new one.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("auth/reset_password.html", token=token)
        if password != confirm:
            flash("Passwords don't match.", "error")
            return render_template("auth/reset_password.html", token=token)

        user.set_password(password)
        user.clear_reset_token()
        db.session.commit()
        flash("Password updated — you can now sign in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)


@auth_bp.route("/account")
@login_required
def account():
    confirm_delete = request.args.get("confirm") == "1"
    return render_template("auth/account.html", confirm_delete=confirm_delete)


@auth_bp.route("/account/delete", methods=["POST"])
@login_required
def delete_account():
    password = request.form.get("password", "")
    if not current_user.check_password(password):
        flash("Incorrect password. Account not deleted.", "error")
        return redirect(url_for("auth.account"))

    user = User.query.get(current_user.id)
    logout_user()
    db.session.delete(user)  # cascades delete all materials, topics, plans, quizzes, chat
    db.session.commit()
    flash("Your account and all associated data have been permanently deleted.", "info")
    return redirect(url_for("auth.login"))
