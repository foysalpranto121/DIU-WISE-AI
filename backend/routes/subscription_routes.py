from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models import Subscription, db

sub_bp = Blueprint("subscription", __name__)


@sub_bp.route("/pricing")
def pricing():
    return render_template("pricing.html")


@sub_bp.route("/landing")
def landing():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    return render_template("landing.html")


@sub_bp.route("/api/subscription/upgrade", methods=["POST"])
@login_required
def upgrade():
    data = request.get_json(force=True)
    plan = data.get("plan", "free")
    if plan not in ("free", "pro", "campus"):
        return jsonify({"error": "Invalid plan"}), 400

    sub = Subscription.query.filter_by(user_id=current_user.id).first()
    if not sub:
        sub = Subscription(user_id=current_user.id, plan=plan)
        db.session.add(sub)
    else:
        sub.plan = plan
        sub.status = "active"
    db.session.commit()
    return jsonify({"plan": plan, "label": sub.plan_label}), 200


@sub_bp.route("/api/subscription/status")
@login_required
def status():
    sub = Subscription.query.filter_by(user_id=current_user.id).first()
    if not sub:
        return jsonify({"plan": "free", "label": "Basic", "is_pro": False}), 200
    return jsonify({**sub.to_dict(), "is_pro": sub.is_pro, "label": sub.plan_label}), 200
