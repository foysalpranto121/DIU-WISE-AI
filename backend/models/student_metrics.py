from datetime import datetime

from .db import db


class StudentMetric(db.Model):
    __tablename__ = "student_metrics"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), nullable=False, index=True)
    attendance_rate = db.Column(db.Float, nullable=False)
    submission_delay = db.Column(db.Float, nullable=False)
    grades = db.Column(db.Float, nullable=False)
    activity_score = db.Column(db.Float, nullable=False)
    engagement_decline = db.Column(db.Float, nullable=False, default=0.0)
    stress_label = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "attendance_rate": self.attendance_rate,
            "submission_delay": self.submission_delay,
            "grades": self.grades,
            "activity_score": self.activity_score,
            "engagement_decline": self.engagement_decline,
            "stress_label": self.stress_label,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
