from datetime import datetime
from . import db

class Subscription(db.Model):
    __tablename__ = "subscriptions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    plan = db.Column(db.String(20), default="free", nullable=False)  # free, pro, campus
    status = db.Column(db.String(20), default="active")  # active, cancelled, expired
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "plan": self.plan,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    @property
    def is_pro(self):
        return self.plan in ("pro", "campus")

    @property
    def plan_label(self):
        return {"free": "Basic", "pro": "Pro", "campus": "Campus"}.get(self.plan, "Basic")

    @property
    def plan_color(self):
        return {"free": "#6b7280", "pro": "#6366f1", "campus": "#a855f7"}.get(self.plan, "#6b7280")
