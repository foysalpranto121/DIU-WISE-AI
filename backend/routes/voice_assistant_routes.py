import io
import json
import os
import tempfile

from flask import Blueprint, jsonify, render_template, request, send_file
from flask_login import current_user, login_required

va_bp = Blueprint("voice_assistant", __name__)


@va_bp.route("/voice-assistant")
@login_required
def voice_assistant_page():
    return render_template("voice_assistant.html")


@va_bp.route("/voice-assistant/speak", methods=["POST"])
@login_required
def speak():
    """Text → OpenAI TTS → audio/mpeg.
    Returns JSON {fallback: true} when no API key is configured so the
    browser can fall back to SpeechSynthesis automatically."""
    data = request.get_json(force=True)
    text = (data.get("text") or "").strip()
    voice = data.get("voice", "nova")

    if not text:
        return jsonify({"error": "text is required"}), 400

    # TTS must go to OpenAI directly — proxy providers don't support it.
    # Prefer WHISPER_API_KEY (real sk-... key) over the proxy OPENAI_API_KEY.
    api_key = os.getenv("WHISPER_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key.startswith("euri-") or api_key == "your_openai_api_key_here":
        return jsonify({"fallback": True}), 200

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://api.openai.com/v1", timeout=30)

        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text[:4096],
        )
        return send_file(
            io.BytesIO(response.content),
            mimetype="audio/mpeg",
            as_attachment=False,
        )
    except Exception as e:
        print(f"[VoiceAssistant] TTS error: {e}")
        return jsonify({"fallback": True, "error": str(e)}), 200


@va_bp.route("/voice-assistant/chat", methods=["POST"])
@login_required
def voice_chat():
    """Full pipeline: audio blob → Whisper STT → AI chat → TTS text.
    Returns transcript, structured AI response, and a ready-to-speak tts_text."""
    if "audio" not in request.files:
        return jsonify({"error": "No audio file"}), 400

    audio_file = request.files["audio"]
    lang_mode = request.form.get("lang_mode", "both")   # "en" | "bn" | "both"
    try:
        history = json.loads(request.form.get("history", "[]"))
    except Exception:
        history = []

    api_key = os.getenv("WHISPER_API_KEY") or os.getenv("OPENAI_API_KEY", "")

    # ── Step 1: Transcribe with Whisper ─────────────────────────────────
    transcript = ""
    detected_lang = "en"
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=".webm")
        os.close(fd)
        audio_file.save(tmp_path)

        if not api_key:
            return jsonify({"error": "no_api_key", "fallback": True}), 200

        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.openai.com/v1",
            timeout=25,
        )
        with open(tmp_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="verbose_json",
            )
        transcript = result.text or ""
        detected_lang = getattr(result, "language", "en")

    except Exception as e:
        print(f"[VoiceAssistant] Transcription error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    if not transcript.strip():
        return jsonify({"error": "Nothing transcribed — please speak clearly."}), 400

    # ── Step 2: AI response ─────────────────────────────────────────────
    from services.registry import ServiceRegistry
    rag    = ServiceRegistry.get("rag_engine")
    router = ServiceRegistry.get("agent_router")

    routing   = router.route_query(transcript)
    ai_result = rag.answer(
        transcript,
        anonymous=False,
        history=history[-6:],
        intent=routing["intent"],
        urgency=routing["urgency"],
        context_data={},
    )

    structured = ai_result.get("structured_response", {})
    summary_en  = structured.get("summary", "")
    summary_bn  = structured.get("summary_bn", "")
    spoken_bn   = structured.get("spoken_bn", "")   # TTS-optimised Bangla from prompt
    advice_en   = structured.get("advice", [])
    advice_bn   = structured.get("advice_bn", [])
    action_en   = structured.get("action_required", "")
    action_bn   = structured.get("action_required_bn", "")

    # ── Step 3: Separate English and Bangla TTS texts ───────────────────
    # English → goes to OpenAI TTS (great quality)
    tts_en = " ".join(filter(None, [summary_en, action_en] + advice_en[:1]))

    # Bangla → goes to browser SpeechSynthesis with bn-BD voice
    # Prefer the spoken_bn field (TTS-optimised) if present, else compose from parts
    if spoken_bn:
        tts_bn = spoken_bn
    else:
        tts_bn = " ".join(filter(None, [summary_bn, action_bn] + advice_bn[:1]))

    # Clean Bangla for TTS: remove non-Bangla/non-space punctuation that confuse synth
    import re
    tts_bn = re.sub(r'["""\'()\[\]{}:;,\-—–]', ' ', tts_bn)
    tts_bn = re.sub(r'\s+', ' ', tts_bn).strip()

    # lang_mode filtering
    if lang_mode == "en":
        tts_bn = ""
    elif lang_mode == "bn":
        tts_en = ""

    urgency    = routing.get("urgency", "low")
    model_risk = structured.get("risk_level", "low")

    return jsonify({
        "transcript":          transcript,
        "detected_lang":       detected_lang,
        "structured_response": structured,
        "tts_en":              tts_en,
        "tts_bn":              tts_bn,
        "urgency":             urgency,
        "crisis":              bool(urgency == "high" or model_risk == "high"),
    }), 200
