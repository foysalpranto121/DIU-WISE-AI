from datetime import datetime
from .db import db


class AcademicEvent(db.Model):
    __tablename__ = "academic_events"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    event_type = db.Column(db.String(50), nullable=False, default="exam")  # exam, assignment, presentation, quiz
    event_date = db.Column(db.Date, nullable=False)
    weight = db.Column(db.Float, default=1.0)  # importance multiplier 1.0–3.0
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "event_type": self.event_type,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "weight": self.weight,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
