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

    # Wellness value ranges per stress_label, so the demo data spreads across all
    # three burnout bands instead of every student landing on the same score.
    # Ranges follow the scales in ai_engine/burnout_model.py FEATURE_COLUMNS.
    STRAINED_LABELS = ("stress", "anxiety", "burnout")

    def _synthetic_row(self, i):
        attendance = round(random.uniform(45, 100), 2)
        submission_delay = round(random.uniform(0, 12), 2)
        grades = round(random.uniform(45, 100), 2)
        activity_score = round(random.uniform(30, 100), 2)
        engagement_decline = round(random.uniform(0, 100), 2)

        stress_label = random.choices(
            self.STRESS_LABELS, weights=[0.22, 0.2, 0.2, 0.15, 0.23]
        )[0]

        if stress_label in self.STRAINED_LABELS:
            sleep_quality = round(random.uniform(3.5, 7.5), 2)
            screen_time = round(random.uniform(6, 13), 2)
            social_interaction = round(random.uniform(2, 6.5), 2)
            break_frequency = round(random.uniform(2, 6.5), 2)
            mood_score = round(random.uniform(2, 4), 2)
            stress_level = round(random.uniform(4.5, 9), 2)
        else:
            sleep_quality = round(random.uniform(6, 10), 2)
            screen_time = round(random.uniform(2, 8), 2)
            social_interaction = round(random.uniform(5, 10), 2)
            break_frequency = round(random.uniform(5, 10), 2)
            mood_score = round(random.uniform(3.5, 5), 2)
            stress_level = round(random.uniform(1, 4.5), 2)

        return StudentMetric(
            student_id=f"DIU-{1000+i}",
            attendance_rate=attendance,
            submission_delay=submission_delay,
            grades=grades,
            activity_score=activity_score,
            engagement_decline=engagement_decline,
            sleep_quality=sleep_quality,
            screen_time=screen_time,
            social_interaction=social_interaction,
            break_frequency=break_frequency,
            mood_score=mood_score,
            stress_level=stress_level,
            stress_label=stress_label,
        )

    def fetch_dashboard_base(self):
        rows = StudentMetric.query.order_by(StudentMetric.id.asc()).all()
        return [r.to_dict() for r in rows]
