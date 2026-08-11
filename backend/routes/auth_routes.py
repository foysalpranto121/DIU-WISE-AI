from functools import wraps

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from extensions import limiter, oauth
from models import User, db

auth_bp = Blueprint("auth", __name__)


def admin_required(func):
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.role != "admin":
            return jsonify({"error": "admin access required"}), 403
        return func(*args, **kwargs)

    return wrapper


@auth_bp.route("/login", methods=["GET", "POST"])
# Password guessing was unrestricted. Only the POST path is limited, so
# reloading the login page never trips the limit.
@limiter.limit(
    lambda: current_app.config["RATELIMIT_LOGIN"],
    exempt_when=lambda: request.method == "GET",
)
def login():
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect(url_for("index"))
        return render_template("login.html")

    payload = request.get_json(force=True)
    email = payload.get("email", "").strip().lower()
    password = payload.get("password", "")
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401
    if not user.is_active_account:
        return jsonify({"error": "Account disabled"}), 403
    login_user(user, remember=True)
    return jsonify({"message": "Logged in", "user": user.to_dict()})


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect(url_for("index"))
        return render_template("register.html")

    # JSON API path (used by the register form via fetch)
    payload = request.get_json(force=True)
    full_name = payload.get("full_name", "").strip()
    email = payload.get("email", "").strip().lower()
    password = payload.get("password", "")
    if not full_name or not email or len(password) < 8:
        return jsonify({"error": "Full name, email and a password of at least 8 characters are required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "That email is already registered. Try logging in instead."}), 409

    user = User(full_name=full_name, email=email, role="student")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user, remember=True)
    return jsonify({"message": "Account created", "user": user.to_dict()}), 201


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out"})


@auth_bp.route("/me", methods=["GET"])
def me():
    if not current_user.is_authenticated:
        return jsonify({"authenticated": False, "user": None})
    return jsonify({"authenticated": True, "user": current_user.to_dict()})


@auth_bp.route("/account/password", methods=["POST"])
@login_required
def update_password():
    payload = request.get_json(force=True)
    old_password = payload.get("old_password", "")
    new_password = payload.get("new_password", "")
    if len(new_password) < 8:
        return jsonify({"error": "New password must be at least 8 characters"}), 400
    if not current_user.check_password(old_password):
        return jsonify({"error": "Current password incorrect"}), 400
    current_user.set_password(new_password)
    db.session.commit()
    return jsonify({"message": "Password updated"})


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
# Every successful POST can send a real email through Brevo's 300 per day
# free tier, so the limit is tight. GET only renders the form.
@limiter.limit(
    lambda: current_app.config["RATELIMIT_PASSWORD_RESET"],
    exempt_when=lambda: request.method == "GET",
)
def forgot_password():
    """Request a password reset link by email.

    The response is identical whether or not the address belongs to an
    account, so this endpoint cannot be used to test which emails are
    registered.
    """
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect(url_for("index"))
        return render_template("forgot_password.html")

    email = (request.form.get("email") or "").strip().lower()
    if not email or "@" not in email or len(email) > 160:
        flash("Please enter a valid email address.", "error")
        return redirect(url_for("auth.forgot_password"))

    user = User.query.filter_by(email=email).first()
    if user is not None:
        from services.registry import ServiceRegistry

        try:
            ServiceRegistry.get("password_reset_service").send_reset_email(user)
        except Exception:
            # Deliberately swallowed: a delivery failure must not produce a
            # different response for registered addresses. It is logged for
            # the operator instead.
            current_app.logger.exception("Password reset email failed to send")

    flash(
        "If an account exists for that address, a reset link has been sent. "
        "It is valid for one hour.",
        "success",
    )
    return redirect(url_for("auth.forgot_password"))


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token: str):
    """Set a new password using a valid reset token.

    The token is verified on both the GET (to avoid rendering a form that can
    never succeed) and again on the POST (the only check that matters).
    """
    from services.registry import ServiceRegistry

    reset_service = ServiceRegistry.get("password_reset_service")
    user = reset_service.verify_token(token)
    if user is None:
        flash("That reset link is invalid or has expired. Request a new one.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "GET":
        return render_template("reset_password.html", token=token)

    password = request.form.get("password") or ""
    confirm = request.form.get("confirm_password") or ""
    if len(password) < 8:
        flash("Password must be at least 8 characters.", "error")
        return redirect(url_for("auth.reset_password", token=token))
    if password != confirm:
        flash("Passwords do not match.", "error")
        return redirect(url_for("auth.reset_password", token=token))

    user.set_password(password)
    db.session.commit()
    flash("Password updated. Sign in with your new password.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/auth/google", methods=["GET"])
def google_login():
    """Send the user to Google's consent screen.

    Authlib generates a random state, stores it in the session and appends it
    to the authorization URL; the callback rejects any response whose state
    does not match.
    """
    if not current_app.config["GOOGLE_CLIENT_ID"]:
        flash("Google sign-in is not configured on this server.", "error")
        return redirect(url_for("auth.login"))
    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/auth/google/callback", methods=["GET"])
def google_callback():
    """Complete Google sign-in: log in a matching account or create one."""
    if not current_app.config["GOOGLE_CLIENT_ID"]:
        flash("Google sign-in is not configured on this server.", "error")
        return redirect(url_for("auth.login"))

    try:
        # Validates the state parameter against the session and exchanges the
        # code; raises on any mismatch or error response from Google.
        token = oauth.google.authorize_access_token()
    except Exception:
        current_app.logger.exception("Google OAuth callback failed")
        flash("Google sign-in failed. Please try again.", "error")
        return redirect(url_for("auth.login"))

    userinfo = token.get("userinfo") or {}
    email = (userinfo.get("email") or "").strip().lower()
    if not email or not userinfo.get("email_verified", False):
        flash("Google did not provide a verified email address.", "error")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()
    if user is None:
        user = User(
            full_name=(userinfo.get("name") or email.split("@")[0])[:120],
            email=email,
            role="student",
            auth_provider="google",
            is_active_account=True,
        )
        db.session.add(user)
        db.session.commit()
    if not user.is_active_account:
        flash("Account disabled.", "error")
        return redirect(url_for("auth.login"))

    login_user(user, remember=True)
    return redirect(url_for("index"))


@auth_bp.route("/admin", methods=["GET"])
@admin_required
def admin_page():
    return render_template("admin.html")


@auth_bp.route("/admin/users", methods=["GET"])
@admin_required
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({"users": [u.to_dict() for u in users]})


@auth_bp.route("/admin/users", methods=["POST"])
@admin_required
def create_user():
    payload = request.get_json(force=True)
    full_name = payload.get("full_name", "").strip()
    email = payload.get("email", "").strip().lower()
    role = payload.get("role", "student")
    password = payload.get("password", "")
    if role not in ("student", "admin"):
        return jsonify({"error": "Invalid role"}), 400
    if not full_name or not email or len(password) < 8:
        return jsonify({"error": "full_name, email and min 8-char password required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 409
    user = User(full_name=full_name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User created", "user": user.to_dict()}), 201


@auth_bp.route("/admin/users/<int:user_id>", methods=["PATCH"])
@admin_required
def update_user(user_id: int):
    user = User.query.get_or_404(user_id)
    payload = request.get_json(force=True)
    if "full_name" in payload:
        user.full_name = payload["full_name"].strip()
    if "role" in payload and payload["role"] in ("student", "admin"):
        user.role = payload["role"]
    if "is_active_account" in payload:
        user.is_active_account = bool(payload["is_active_account"])
    db.session.commit()
    return jsonify({"message": "User updated", "user": user.to_dict()})
