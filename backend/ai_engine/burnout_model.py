import logging
import os

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


logger = logging.getLogger(__name__)


FEATURE_COLUMNS = [
    "attendance_rate",
    "submission_delay",
    "grades",
    "activity_score",
    "engagement_decline",
    "sleep_quality",
    "screen_time",
    "social_interaction",
    "break_frequency",
    "mood_score",
    "stress_level",
]

# Used only when a caller genuinely omits a feature, which is the case for the
# ad hoc /predict payload built in the browser. StudentMetric supplies all 11
# columns, so nothing on the dashboard path should hit these.
FEATURE_DEFAULTS = {
    "attendance_rate": 85.0,
    "submission_delay": 0.0,
    "grades": 75.0,
    "activity_score": 50.0,
    "engagement_decline": 0.0,
    "sleep_quality": 7.0,
    "screen_time": 8.0,
    "social_interaction": 5.0,
    "break_frequency": 5.0,
    "mood_score": 3.0,
    "stress_level": 3.0,
}


class BurnoutModel:
    def __init__(self, model_dir: str):
        self.model_path = os.path.join(model_dir, "burnout_model.joblib")
        os.makedirs(model_dir, exist_ok=True)
        self.model = None

    def _risk_label(self, row):
        # Weighted risk calculation including new wellness metrics
        # row indexes: 0:att, 1:delay, 2:grades, 3:activity, 4:decline, 5:sleep, 6:screen, 7:social, 8:breaks, 9:mood, 10:stress
        risk_score = (
            (100 - row[0]) * 0.15  # Attendance
            + row[1] * 0.10         # Submission Delay
            + (100 - row[2]) * 0.10  # Grades
            + (100 - row[3]) * 0.05  # Activity
            + row[4] * 0.05         # Engagement Decline
            + (10 - row[5]) * 5     # Sleep Quality (0-10) -> (10-row)*5 = 0-50
            + row[6] * 2            # Screen Time (0-24h, mock impact)
            + (10 - row[7]) * 2     # Social Interaction (0-10)
            + (10 - row[8]) * 2     # Break Frequency (0-10)
            + (5 - row[9]) * 10     # Mood Score (1-5) -> (5-row)*10 = 0-40
            + row[10] * 5           # Stress Level (1-10)
        )
        
        # Normalize and label
        if risk_score >= 120:
            return 2  # Needs Support
        if risk_score >= 70:
            return 1  # Balanced
        return 0  # Doing Well

    def train_on_synthetic(self, n_samples: int = 1500):
        rng = np.random.default_rng(42)
        attendance = rng.uniform(35, 100, n_samples)
        submission_delay = rng.uniform(0, 14, n_samples)
        grades = rng.uniform(40, 100, n_samples)
        activity_score = rng.uniform(20, 100, n_samples)
        engagement_decline = rng.uniform(0, 100, n_samples)
        sleep_quality = rng.uniform(1, 10, n_samples)
        screen_time = rng.uniform(2, 16, n_samples)
        social_interaction = rng.uniform(1, 10, n_samples)
        break_frequency = rng.uniform(1, 10, n_samples)
        mood_score = rng.uniform(1, 5, n_samples)
        stress_level = rng.uniform(1, 10, n_samples)

        X = np.column_stack(
            [attendance, submission_delay, grades, activity_score, engagement_decline, 
             sleep_quality, screen_time, social_interaction, break_frequency, mood_score, stress_level]
        )
        y = np.array([self._risk_label(row) for row in X])
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        clf = RandomForestClassifier(n_estimators=200, random_state=42)
        clf.fit(X_train, y_train)
        self.model = clf
        joblib.dump(clf, self.model_path)
        return clf.score(X_test, y_test)

    def load_or_train(self):
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                # Check if model matches current feature set
                if self.model.n_features_in_ != len(FEATURE_COLUMNS):
                    print("Model feature mismatch. Retraining...")
                    self.train_on_synthetic()
            except:
                self.train_on_synthetic()
            return
        self.train_on_synthetic()

    def _vectorize(self, features: dict):
        """Build the model input row, recording any feature that was not supplied.

        FIX: this used to be a block of `features.get(name, <constant>)` calls.
        The 6 wellness features did not exist on StudentMetric, so every
        dashboard row silently fell back to the same constants and every student
        scored identically. The columns exist now, and any remaining
        substitution is logged instead of passing unnoticed.
        """
        values = []
        substituted = []
        for name in FEATURE_COLUMNS:
            raw = features.get(name)
            if raw is None or raw == "":
                substituted.append(name)
                values.append(FEATURE_DEFAULTS[name])
                continue
            try:
                values.append(float(raw))
            except (TypeError, ValueError):
                substituted.append(name)
                values.append(FEATURE_DEFAULTS[name])

        if substituted:
            logger.warning(
                "Burnout prediction substituted defaults for: %s",
                ", ".join(substituted),
            )
        return np.array([values])

    def predict(self, features: dict):
        if self.model is None:
            self.load_or_train()

        payload = self._vectorize(features)
        pred = int(self.model.predict(payload)[0])
        probs = self.model.predict_proba(payload)[0].tolist()
        # Supportive Terminology
        label_map = {0: "Doing Well", 1: "Balanced", 2: "Needs Support"}
        
        # Confidence calculation
        confidence = max(probs) * 100
        
        return {
            "status": label_map[pred], 
            "confidence": round(confidence, 1),
            "probabilities": probs
        }

    def forecast(self, features: dict):
        """
        Improved forecast that projects wellbeing trends based on current state.
        """
        forecasts = {}
        # Different scenarios: 7, 14, 30 days
        scenarios = {
            7: {"mod": "stable", "label": "Stable Trend"},
            14: {"mod": "declining", "label": "Slight decline possible"},
            30: {"mod": "improving", "label": "Potential for improvement"}
        }

        for days, scenario in scenarios.items():
            # Mock projection logic for demonstration
            projected = features.copy()
            if scenario["mod"] == "declining":
                projected["stress_level"] = min(10, float(features.get("stress_level", 3)) + 1.5)
                projected["sleep_quality"] = max(1, float(features.get("sleep_quality", 7)) - 1)
            elif scenario["mod"] == "improving":
                projected["stress_level"] = max(1, float(features.get("stress_level", 3)) - 1)
                projected["sleep_quality"] = min(10, float(features.get("sleep_quality", 7)) + 1)
            
            res = self.predict(projected)
            forecasts[f"{days}_days"] = {
                "status": res["status"],
                "label": scenario["label"],
                "trend": "down" if scenario["mod"] == "declining" else "up" if scenario["mod"] == "improving" else "flat"
            }
        
        return forecasts
