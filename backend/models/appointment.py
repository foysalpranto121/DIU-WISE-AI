from datetime import datetime
from .db import db

class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    counselor_id = db.Column(db.Integer, nullable=False)
    counselor_name = db.Column(db.String(120), nullable=False)
    appointment_date = db.Column(db.String(50), nullable=False)
    appointment_time = db.Column(db.String(50), nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), nullable=False, default="Scheduled")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to user
    user = db.relationship('User', backref=db.backref('appointments', lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "counselor_id": self.counselor_id,
            "counselor_name": self.counselor_name,
            "appointment_date": self.appointment_date,
            "appointment_time": self.appointment_time,
            "reason": self.reason,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
