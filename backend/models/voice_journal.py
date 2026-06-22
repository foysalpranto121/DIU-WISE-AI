from datetime import datetime
from .db import db


class VoiceJournal(db.Model):
    __tablename__ = "voice_journals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    transcript = db.Column(db.Text, nullable=False)
    language_detected = db.Column(db.String(20), nullable=True)
    emotion = db.Column(db.String(50), nullable=True)
    emotion_scores = db.Column(db.JSON, nullable=True)
    duration_seconds = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "transcript": self.transcript,
            "language_detected": self.language_detected,
            "emotion": self.emotion,
            "emotion_scores": self.emotion_scores,
            "duration_seconds": self.duration_seconds,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
