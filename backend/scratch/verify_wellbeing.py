import os
import sys
from ai_engine.burnout_model import BurnoutModel
from services.triage_service import TriageService

# Mock Config
class MockApp:
    def __init__(self):
        self.config = {"MODEL_DIR": "ai_engine/trained"}

def test_wellbeing_logic():
    print("Testing Wellbeing Insights Logic...")
    
    model = BurnoutModel("ai_engine/trained")
    model.load_or_train()
    
    triage = TriageService()
    
    # Case 1: Healthy student
    payload_healthy = {
        "stress_level": 2,
        "sleep_quality": 8,
        "screen_time": 4,
        "social_interaction": 8,
        "break_frequency": 8,
        "mood_score": 5,
        "attendance_rate": 95,
        "submission_delay": 0,
        "grades": 90,
        "activity_score": 80
    }
    
    res1 = model.predict(payload_healthy)
    print(f"\nHealthy Case Status: {res1['status']} (Confidence: {res1['confidence']}%)")
    
    triage_res1 = triage.route(distress_level="low", wellbeing_status=res1["status"], emotion="happy")
    print(f"Triage Message: {triage_res1['message']}")
    print(f"Actionable Guidance: {triage_res1['actions']}")
    
    # Case 2: Stressed student
    payload_stressed = {
        "stress_level": 9,
        "sleep_quality": 3,
        "screen_time": 14,
        "social_interaction": 2,
        "break_frequency": 1,
        "mood_score": 1,
        "attendance_rate": 40,
        "submission_delay": 5,
        "grades": 50,
        "activity_score": 20
    }
    
    res2 = model.predict(payload_stressed)
    print(f"\nStressed Case Status: {res2['status']} (Confidence: {res2['confidence']}%)")
    
    triage_res2 = triage.route(distress_level="high", wellbeing_status=res2["status"], emotion="anxiety")
    print(f"Triage Message: {triage_res2['message']}")
    print(f"Actionable Guidance: {triage_res2['actions']}")

    # Test Forecast
    forecast = model.forecast(payload_stressed)
    print("\nForecast for stressed student:")
    for days, data in forecast.items():
        print(f"  {days}: {data['status']} ({data['label']}, Trend: {data['trend']})")

if __name__ == "__main__":
    # Ensure we can import from backend
    sys.path.append(os.getcwd())
    test_wellbeing_logic()
