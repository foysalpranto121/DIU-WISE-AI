from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chat", methods=["POST"])
def chat():
    payload = request.get_json(force=True)
    message = payload.get("message", "").strip()
    anonymous = bool(payload.get("anonymous", True))
    history = payload.get("history", [])
    
    if not message:
        return jsonify({"error": "message is required"}), 400
    if not anonymous and not current_user.is_authenticated:
        return jsonify({"error": "login required when anonymous is disabled"}), 401

    from services.registry import ServiceRegistry
    rag = ServiceRegistry.get("rag_engine")
    router = ServiceRegistry.get("agent_router")
    
    # Context data from frontend
    context_data = payload.get("student_context", {})
    
    # Get routing decision
    routing_decision = router.route_query(message)
    agent_name = routing_decision["agent_name"]
    route = routing_decision["route"]
    
    # Pass to RAG Engine (always — no cache bypass)
    result = rag.answer(
        message, 
        anonymous=anonymous, 
        history=history,
        intent=routing_decision["intent"],
        urgency=routing_decision["urgency"],
        context_data=context_data
    )
    result["agent_name"] = agent_name
    result["route"] = route

    # --- Crisis Safety Net ---------------------------------------------------
    # Surface the urgency level so the frontend can trigger the Crisis Safety
    # Net (calming exercise + emergency helplines). We treat a query as a crisis
    # if the keyword router flagged HIGH urgency, or the model returned a HIGH
    # risk_level. This closes the loop between distress *detection* and *action*.
    model_risk = (result.get("structured_response") or {}).get("risk_level", "low")
    urgency = routing_decision.get("urgency", "low")
    result["urgency"] = urgency
    result["crisis"] = bool(urgency == "high" or model_risk == "high")
    # ------------------------------------------------------------------------

    if current_user.is_authenticated:
        result["user"] = {"id": current_user.id, "email": current_user.email}
    return jsonify(result), 200


# Verified Bangladesh emergency & emotional-support helplines.
# Kept server-side so numbers can be updated in one place without touching the UI.
CRISIS_RESOURCES = [
    {
        "name": "National Emergency Service",
        "phone": "999",
        "tel": "999",
        "hours": "24/7 — every day",
        "desc": "Free national emergency line for immediate, life-threatening situations.",
        "priority": True,
    },
    {
        "name": "Kaan Pete Roi",
        "phone": "09612-119911",
        "tel": "09612119911",
        "hours": "Every day, 3:00 PM – 3:00 AM",
        "desc": "Bangladesh's emotional-support & suicide-prevention helpline. Confidential, non-judgmental listening by trained volunteers.",
        "priority": True,
    },
    {
        "name": "Moner Bondhu",
        "phone": "01776-632344",
        "tel": "01776632344",
        "hours": "Daytime support",
        "desc": "Mental-health support, counselling and psychosocial guidance.",
        "priority": False,
    },
    {
        "name": "DIU Counselling & Psychosocial Support",
        "phone": "On-campus",
        "tel": "",
        "hours": "University hours",
        "desc": "Reach out to your department counsellor or the DIU student welfare desk for in-person support.",
        "priority": False,
    },
]


@chat_bp.route("/crisis-resources", methods=["GET"])
def crisis_resources():
    """Return verified emergency / emotional-support helplines for the Crisis Safety Net."""
    return jsonify({
        "message": "You are not alone. Reaching out is a sign of strength.",
        "resources": CRISIS_RESOURCES,
    }), 200
