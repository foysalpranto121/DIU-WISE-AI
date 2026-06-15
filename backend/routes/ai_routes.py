from flask import Blueprint, current_app, jsonify, request
from flask_login import login_required

ai_bp = Blueprint("ai", __name__)


@ai_bp.route("/predict", methods=["POST"])
@login_required
def predict():
    from services.registry import ServiceRegistry
    payload = request.get_json(force=True)
    
    burnout_model = ServiceRegistry.get("burnout_model")
    distress_detector = ServiceRegistry.get("distress_detector")
    triage_service = ServiceRegistry.get("triage_service")

    # Terminology shift: wellbeing_status instead of burnout_risk
    burnout = burnout_model.predict(payload)
    forecast = burnout_model.forecast(payload)
    
    distress = distress_detector.detect(payload)
    emotion_hint = payload.get("emotion", "neutral")
    
    triage = triage_service.route(
        distress_level=distress["distress_level"],
        wellbeing_status=burnout["status"],
        emotion=emotion_hint,
        text=payload.get("journal_text", "")
    )
    
    return jsonify({
        "wellbeing": {
            "status": burnout["status"],
            "confidence": burnout["confidence"],
            "forecast": forecast
        },
        "distress": distress,
        "triage": triage
    }), 200


@ai_bp.route("/generate-plan", methods=["POST"])
@login_required
def generate_plan():
    from services.registry import ServiceRegistry
    payload = request.get_json(force=True)
    triage_service = ServiceRegistry.get("triage_service")
    plan = triage_service.generate_wellbeing_plan(payload)
    return jsonify({"plan": plan}), 200


@ai_bp.route("/emotion", methods=["POST"])
@login_required
def emotion():
    from services.registry import ServiceRegistry
    payload = request.get_json(force=True)
    text = payload.get("text", "").strip()
    if not text:
        return jsonify({"error": "text is required"}), 400

    emotion_classifier = ServiceRegistry.get("emotion_classifier")
    triage_service = ServiceRegistry.get("triage_service")

    result = emotion_classifier.predict(text)
    triage = triage_service.route(
        distress_level=payload.get("distress_level", "low"),
        wellbeing_status=payload.get("wellbeing_status", "Doing Well"),
        emotion=result["emotion"],
        text=text,
    )
    return jsonify({"emotion": result, "triage": triage}), 200
