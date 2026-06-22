import os
from openai import OpenAI

class TriageService:
    def __init__(self):
        self.openai_client = None

    def _get_client(self):
        if not self.openai_client:
            key = os.getenv("OPENAI_API_KEY")
            if key and key != "your_openai_api_key_here":
                base_url = os.getenv("OPENAI_BASE_URL")
                kwargs = {"api_key": key}
                if base_url:
                    kwargs["base_url"] = base_url
                self.openai_client = OpenAI(**kwargs)
        return self.openai_client

    def route(self, distress_level: str, wellbeing_status: str, emotion: str, text: str = ""):
        # Emergency Override Check
        critical_keywords = ["suicide", "suicidal", "kill", "die", "harm", "end it all"]
        text_lower = text.lower()
        if any(word in text_lower for word in critical_keywords):
            return {
                "route_to": "emergency services",
                "priority": "critical",
                "message": "EMERGENCY: Please contact the campus crisis line at 988 or 911 immediately. Support is available right now.",
                "actions": ["Call 988 immediately", "Reach out to campus security", "Stay with a friend"]
            }

        # Base routing decision
        route_to = "self-help resources"
        priority = "normal"
        default_message = "Your wellbeing looks stable. Keep maintaining your healthy routines!"
        actions = [
            "Take a 10-minute mindful break",
            "Review your upcoming deadlines",
            "Drink a glass of water and stretch"
        ]
        
        emotion_lower = emotion.lower()

        if wellbeing_status == "Needs Support" or distress_level == "high":
            route_to = "counselor"
            priority = "urgent"
            default_message = "It looks like you're going through a tough time. We recommend connecting with a counselor."
            actions = [
                "Book an appointment with a counselor",
                "Reach out to a trusted peer or mentor",
                "Try a 5-minute breathing exercise"
            ]
        elif emotion_lower in ("anxiety", "stress", "burnout") or wellbeing_status == "Balanced":
            route_to = "wellbeing coach"
            priority = "high"
            default_message = "You're doing okay, but some extra support might help you stay balanced."
            actions = [
                "Schedule a quick reset session",
                "Use the 'Quick Reflection' tool below",
                "Go for a short walk outside"
            ]

        # Dynamic Recommendation via OpenAI (if available)
        client = self._get_client()
        if client:
            try:
                prompt = (
                    f"A student has a {wellbeing_status} status, {distress_level} distress, "
                    f"and feels {emotion}. Provide a supportive message and 3 specific, "
                    f"actionable advice items for today. Format as JSON: {{'message': '...', 'actions': ['...', '...', '...']}}"
                )
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                import json
                data = json.loads(response.choices[0].message.content)
                return {
                    "route_to": route_to,
                    "priority": priority,
                    "message": data.get("message", default_message),
                    "actions": data.get("actions", actions)
                }
            except Exception as e:
                print(f"OpenAI fallback error: {e}")

        return {
            "route_to": route_to,
            "priority": priority,
            "message": default_message,
            "actions": actions
        }

    def generate_wellbeing_plan(self, data: dict):
        """Generates a personalized Wellbeing Prevention & Growth Plan."""
        client = self._get_client()
        if not client:
            return "Plan generation requires an active AI connection. Try again later."

        prompt = (
            f"Generate a personalized 'Wellbeing Growth Plan' for a student with these metrics: "
            f"Sleep: {data.get('sleep_quality')}/10, Stress: {data.get('stress_level')}/10, "
            f"Mood: {data.get('mood_score')}/5, Social: {data.get('social_interaction')}/10. "
            f"Include: 1. Weekly schedule suggestions, 2. Specific coping strategies, 3. A motivational tip. "
            f"Keep it supportive, encouraging, and non-clinical. Max 250 words."
        )
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating plan: {str(e)}"
