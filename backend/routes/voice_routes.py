import os
import tempfile

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from models import VoiceJournal, db

voice_bp = Blueprint("voice", __name__)


@voice_bp.route("/voice-journal")
@login_required
def voice_journal_page():
    entries = (
        VoiceJournal.query.filter_by(user_id=current_user.id)
        .order_by(VoiceJournal.created_at.desc())
        .limit(30)
        .all()
    )
    return render_template("voice_journal.html", entries=[e.to_dict() for e in entries])


@voice_bp.route("/voice-journal/transcribe", methods=["POST"])
@login_required
def transcribe():
    """Receive audio blob from MediaRecorder, return Whisper transcript."""
    if "audio" not in request.files:
        return jsonify({"error": "No audio file received"}), 400

    audio_file = request.files["audio"]
    # Use dedicated Whisper key if set, otherwise fall back to main OpenAI key
    api_key = os.getenv("WHISPER_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return jsonify({"error": "No API key configured", "fallback": True}), 200

    # Save blob to a temp file — Whisper needs a real file with a .webm extension.
    # On Windows, NamedTemporaryFile holds an exclusive lock while open, so
    # audio_file.save() would fail inside the with-block. Use mkstemp instead:
    # create the fd, close it immediately, then write freely.
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=".webm")
        os.close(fd)                  # release the Windows file lock
        audio_file.save(tmp_path)     # now safe to write on Windows

        from openai import OpenAI
        # Whisper must always go to OpenAI directly — never through an Euri proxy.
        # Explicitly pass base_url to override any OPENAI_BASE_URL env var.
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
        language = getattr(result, "language", "unknown")
        return jsonify({"transcript": transcript, "language": language}), 200

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e), "fallback": True}), 200
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@voice_bp.route("/voice-journal/save", methods=["POST"])
@login_required
def save_entry():
    from services.registry import ServiceRegistry

    data = request.get_json(force=True)
    transcript = (data.get("transcript") or "").strip()
    language = data.get("language", "unknown")
    duration = float(data.get("duration", 0))

    if not transcript:
        return jsonify({"error": "Transcript is empty"}), 400

    emotion_result = {"emotion": "neutral", "scores": {}}
    try:
        classifier = ServiceRegistry.get("emotion_classifier")
        emotion_result = classifier.predict(transcript)
    except Exception:
        pass

    journal = VoiceJournal(
        user_id=current_user.id,
        transcript=transcript,
        language_detected=language,
        emotion=emotion_result.get("emotion", "neutral"),
        emotion_scores=emotion_result.get("scores", {}),
        duration_seconds=duration,
    )
    db.session.add(journal)
    db.session.commit()

    return jsonify({
        "entry_id": journal.id,
        "transcript": transcript,
        "emotion": journal.emotion,
        "emotion_scores": journal.emotion_scores,
        "language": language,
    }), 201


@voice_bp.route("/voice-journal/entries")
@login_required
def get_entries():
    entries = (
        VoiceJournal.query.filter_by(user_id=current_user.id)
        .order_by(VoiceJournal.created_at.desc())
        .limit(50)
        .all()
    )
    return jsonify([e.to_dict() for e in entries]), 200


@voice_bp.route("/voice-journal/entries/<int:entry_id>", methods=["DELETE"])
@login_required
def delete_entry(entry_id):
    entry = VoiceJournal.query.filter_by(
        id=entry_id, user_id=current_user.id
    ).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    return jsonify({"message": "Entry deleted"}), 200
