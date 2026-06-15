class DistressDetector:
    def detect(self, student_row: dict):
        attendance_drop = 100 - float(student_row["attendance_rate"])
        delay = float(student_row["submission_delay"])
        engagement_decline = float(student_row.get("engagement_decline", 0))

        score = attendance_drop * 0.45 + delay * 2.2 + engagement_decline * 0.35
        if score >= 55:
            level = "high"
        elif score >= 30:
            level = "medium"
        else:
            level = "low"

        return {
            "distress_score": round(score, 2),
            "distress_level": level,
            "signals": {
                "attendance_drop": round(attendance_drop, 2),
                "submission_delay": round(delay, 2),
                "engagement_decline": round(engagement_decline, 2),
            },
        }
