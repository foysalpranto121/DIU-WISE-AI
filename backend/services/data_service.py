import random

from models import StudentMetric, db


class DataService:
    STRESS_LABELS = ["stress", "anxiety", "burnout", "confusion", "neutral"]

    def seed_if_empty(self, n=180):
        if StudentMetric.query.count() > 0:
            return
        rows = [self._synthetic_row(i) for i in range(1, n + 1)]
        db.session.bulk_save_objects(rows)
        db.session.commit()

    def _synthetic_row(self, i):
        attendance = round(random.uniform(45, 100), 2)
        submission_delay = round(random.uniform(0, 12), 2)
        grades = round(random.uniform(45, 100), 2)
        activity_score = round(random.uniform(30, 100), 2)
        engagement_decline = round(random.uniform(0, 100), 2)

        stress_label = random.choices(
            self.STRESS_LABELS, weights=[0.22, 0.2, 0.2, 0.15, 0.23]
        )[0]
        return StudentMetric(
            student_id=f"DIU-{1000+i}",
            attendance_rate=attendance,
            submission_delay=submission_delay,
            grades=grades,
            activity_score=activity_score,
            engagement_decline=engagement_decline,
            stress_label=stress_label,
        )

    def fetch_dashboard_base(self):
        rows = StudentMetric.query.order_by(StudentMetric.id.asc()).all()
        return [r.to_dict() for r in rows]
