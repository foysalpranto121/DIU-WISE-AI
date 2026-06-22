from datetime import date, timedelta

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from models import AcademicEvent, db

calendar_bp = Blueprint("calendar", __name__)

EVENT_WEIGHTS = {"exam": 3.0, "presentation": 2.0, "assignment": 1.5, "quiz": 1.0}


@calendar_bp.route("/stress-calendar")
@login_required
def stress_calendar():
    events = (
        AcademicEvent.query.filter_by(user_id=current_user.id)
        .order_by(AcademicEvent.event_date)
        .all()
    )
    return render_template("stress_calendar.html", events=[e.to_dict() for e in events])


@calendar_bp.route("/api/events", methods=["GET"])
@login_required
def list_events():
    events = (
        AcademicEvent.query.filter_by(user_id=current_user.id)
        .order_by(AcademicEvent.event_date)
        .all()
    )
    return jsonify([e.to_dict() for e in events]), 200


@calendar_bp.route("/api/events", methods=["POST"])
@login_required
def add_event():
    data = request.get_json(force=True)
    title = (data.get("title") or "").strip()
    event_type = data.get("event_type", "exam").lower()
    event_date_str = (data.get("event_date") or "").strip()

    if not title or not event_date_str:
        return jsonify({"error": "title and event_date are required"}), 400

    try:
        event_date = date.fromisoformat(event_date_str)
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    weight = EVENT_WEIGHTS.get(event_type, 1.0)

    event = AcademicEvent(
        user_id=current_user.id,
        title=title,
        event_type=event_type,
        event_date=event_date,
        weight=weight,
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(event.to_dict()), 201


@calendar_bp.route("/api/events/<int:event_id>", methods=["DELETE"])
@login_required
def delete_event(event_id):
    event = AcademicEvent.query.filter_by(
        id=event_id, user_id=current_user.id
    ).first_or_404()
    db.session.delete(event)
    db.session.commit()
    return jsonify({"message": "Event deleted"}), 200


@calendar_bp.route("/api/stress-forecast")
@login_required
def stress_forecast():
    events = AcademicEvent.query.filter_by(user_id=current_user.id).all()
    today = date.today()
    forecast = []

    for i in range(30):
        day = today + timedelta(days=i)
        base_stress = 40
        event_boost = 0.0
        day_events = []

        for ev in events:
            days_until = (ev.event_date - day).days
            if days_until == 0:
                # Day-of event: max pressure
                event_boost += ev.weight * 22
                day_events.append(ev.to_dict())
            elif 1 <= days_until <= 7:
                # Build-up: pressure scales with proximity
                event_boost += ev.weight * 14 * (1 - days_until / 8)
                day_events.append(ev.to_dict())

        stress_score = min(100, round(base_stress + event_boost))

        if stress_score >= 80:
            risk = "high"
        elif stress_score >= 58:
            risk = "medium"
        else:
            risk = "low"

        forecast.append({
            "date": day.isoformat(),
            "day_label": f"{day.day} {day.strftime('%b')}",
            "stress_score": stress_score,
            "risk_level": risk,
            "events": day_events,
        })

    # Find spike days to surface as alerts
    spikes = [f for f in forecast if f["risk_level"] == "high"]

    return jsonify({"forecast": forecast, "spikes": spikes}), 200
