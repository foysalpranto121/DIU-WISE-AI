from functools import wraps

from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

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
