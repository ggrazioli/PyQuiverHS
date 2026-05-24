from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, current_user, login_required
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from models import User
from extensions import db, limiter, mail
from flask_mail import Message



auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(current_app.secret_key)
    return serializer.dumps(email, salt=current_app.config["SECURITY_PASSWORD_SALT"])

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.secret_key)
    try:
        email = serializer.loads(
            token,
            salt=current_app.config["SECURITY_PASSWORD_SALT"],
            max_age=expiration
        )
        return email
    except SignatureExpired:
        return None
    except BadSignature:
        return None
    
def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(current_app.secret_key)
    return serializer.dumps(email, salt=current_app.config["SECURITY_PASSWORD_SALT"])


def confirm_reset_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.secret_key)
    try:
        email = serializer.loads(
            token,
            salt=current_app.config["SECURITY_PASSWORD_SALT"],
            max_age=expiration
        )
        return email
    except SignatureExpired:
        return None
    except BadSignature:
        return None
    
def send_confirmation_email(user):
    token = generate_confirmation_token(user.email)
    confirm_url = url_for("auth.confirm_email", token=token, _external=True)

    msg = Message(
        subject="Confirm your QuiverHS account",
        recipients=[user.email],
    )

    msg.body = f"""Welcome to PyQuiverHS!

Please confirm your email address by visiting the link below:

{confirm_url}

If you did not create this account, you can ignore this message.
"""

    msg.html = render_template(
        "email/confirm_account.html",
        confirm_url=confirm_url
    )

    mail.send(msg)


@auth_bp.route("/signup", methods=["GET", "POST"])
@limiter.limit("5 per hour")
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not email or not password or not confirm_password:
            flash("Please complete all fields.")
            return redirect(url_for("auth.signup"))

        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("auth.signup"))

        if len(password) < 8:
            flash("Password must be at least 8 characters.")
            return redirect(url_for("auth.signup"))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("User already exists.")
            return redirect(url_for("auth.signup"))
        # Note: set confirmed=False in production, bypassing email
        # confirmation temporarily with confirmed=True 
        user = User(email=email, confirmed=False)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        print("SIGNUP SUCCESS - GENERATING TOKEN")

        send_confirmation_email(user)

        flash("Account created, check your email.")
        return redirect(url_for("auth.login"))

    return render_template("auth/signup.html")

@auth_bp.route("/confirm/<token>")
def confirm_email(token):
    email = confirm_token(token)

    if not email:
        flash("The confirmation link is invalid or has expired.")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()

    if not user:
        flash("User not found.")
        return redirect(url_for("auth.signup"))

    if user.confirmed:
        flash("Account already confirmed. Please log in.")
        return redirect(url_for("auth.login"))

    user.confirmed = True
    db.session.commit()

    flash("Your email has been confirmed. You can now log in.")
    return redirect(url_for("auth.login"))

@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user is None or not user.check_password(password):
            flash("Invalid email or password.")
            return redirect(url_for("auth.login"))
        
        if not user.confirmed:
            flash("Your email is not confirmed. Request a new confirmation link below.")
            return redirect(url_for("auth.resend_confirmation"))

        login_user(user)
        flash("Logged in successfully.")
        return redirect(url_for("home"))

    return render_template("auth/login.html")

@auth_bp.route("/resend-confirmation", methods=["GET", "POST"])
def resend_confirmation():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()

        if user and not user.confirmed:
            token = generate_confirmation_token(user.email)
            confirm_url = url_for("auth.confirm_email", token=token, _external=True)

            # PRINTS CONFIRMATION TO TERMINAL FOR TESTING
            # print("\n=== RESENT EMAIL CONFIRMATION LINK ===", flush=True)
            # print(confirm_url, flush=True)
            # print("=== END RESENT CONFIRMATION LINK ===\n", flush=True)

            # Later replace print(...) with real email send

            send_confirmation_email(user)

        flash("If that account exists and is not yet confirmed, a new confirmation email has been sent.")
        return redirect(url_for("auth.login"))

    return render_template("auth/resend_confirmation.html")

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per hour")
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            token = generate_reset_token(user.email)
            reset_url = url_for("auth.reset_password", token=token, _external=True)

            print("\n=== PASSWORD RESET LINK ===")
            print(reset_url)
            print("=== END PASSWORD RESET LINK ===\n")

            # Later replace print(...) with real email send

        flash("If that email exists, a password reset link has been sent.")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")

@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    email = confirm_reset_token(token)
    if not email:
        flash("The password reset link is invalid or has expired.")
        return redirect(url_for("auth.forgot_password"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User not found.")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not password or not confirm_password:
            flash("Please complete all fields.")
            return redirect(url_for("auth.reset_password", token=token))

        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("auth.reset_password", token=token))

        if len(password) < 8:
            flash("Password must be at least 8 characters.")
            return redirect(url_for("auth.reset_password", token=token))

        user.set_password(password)
        db.session.commit()

        flash("Your password has been reset. Please log in.")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.")
    return redirect(url_for("landing"))