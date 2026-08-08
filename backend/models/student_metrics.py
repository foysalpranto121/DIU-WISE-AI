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

    # Wellness features the burnout model reads. See FEATURE_COLUMNS in
    # ai_engine/burnout_model.py: all 11 features are cast with float(), and the
    # server_default values below are the same fallbacks predict() used to
    # substitute when these columns did not exist.
    sleep_quality = db.Column(  # scale 1 to 10
        db.Float, nullable=False, default=7.0, server_default="7.0"
    )
    screen_time = db.Column(  # hours per day
        db.Float, nullable=False, default=8.0, server_default="8.0"
    )
    social_interaction = db.Column(  # scale 1 to 10
        db.Float, nullable=False, default=5.0, server_default="5.0"
    )
    break_frequency = db.Column(  # scale 1 to 10
        db.Float, nullable=False, default=5.0, server_default="5.0"
    )
    mood_score = db.Column(  # scale 1 to 5
        db.Float, nullable=False, default=3.0, server_default="3.0"
    )
    stress_level = db.Column(  # scale 1 to 10
        db.Float, nullable=False, default=3.0, server_default="3.0"
    )

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
            # FIX: these 6 keys were missing, so burnout_model.predict() fell back
            # to its hardcoded defaults for every student and scored everyone the
            # same. Additive only, no existing key changed.
            "sleep_quality": self.sleep_quality,
            "screen_time": self.screen_time,
            "social_interaction": self.social_interaction,
            "break_frequency": self.break_frequency,
            "mood_score": self.mood_score,
            "stress_level": self.stress_level,
            "stress_label": self.stress_label,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
