from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .db import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")  # student/admin
    is_active_account = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # New Student Details
    university = db.Column(db.String(200), nullable=True)
    department = db.Column(db.String(150), nullable=True)
    student_id = db.Column(db.String(50), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    
    # Expanded Student Info
    semester = db.Column(db.String(50), nullable=True)
    batch = db.Column(db.String(50), nullable=True)
    current_gpa = db.Column(db.Float, nullable=True, default=0.0)
    credit_load = db.Column(db.Integer, nullable=True, default=0)
    
    # Preferences & Tracking (JSON)
    preferences = db.Column(db.JSON, nullable=True, default=lambda: {"notifications": True, "privacy": "private"})
    achievements = db.Column(db.JSON, nullable=True, default=lambda: [])
    goals = db.Column(db.JSON, nullable=True, default=lambda: {"study_hours": 0, "assignments": 0})

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return self.is_active_account

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role,
            "university": self.university,
            "department": self.department,
            "student_id": self.student_id,
            "phone_number": self.phone_number,
            "semester": self.semester,
            "batch": self.batch,
            "current_gpa": self.current_gpa,
            "credit_load": self.credit_load,
            "preferences": self.preferences,
            "achievements": self.achievements,
            "goals": self.goals,
            "is_active_account": self.is_active_account,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
