import re

class AgentRouter:
    def __init__(self):
        self.routes = {
            "academic": {
                "keywords": [r"grade", r"course", r"schedule", r"assignment", r"exam", r"cgpa", r"class", r"credit", r"deadline", r"academic", r"study", r"gpa", r"lecture", r"semester"],
                "agent_name": "Academic Agent"
            },
            "mental_health": {
                "keywords": [r"stress", r"anxiet", r"depress", r"burnout", r"sad", r"overwhelm", r"tired", r"sleep", r"health", r"counsel", r"lonely", r"panic", r"suicide", r"harm", r"cry", r"hopeless", r"worthless"],
                "agent_name": "Mental Health Agent"
            },
            "admin": {
                "keywords": [r"password", r"account", r"login", r"system", r"error", r"dashboard", r"admin", r"bug"],
                "agent_name": "Admin Agent"
            }
        }

    def route_query(self, query: str) -> dict:
        query_lower = query.lower()

        # Intent Classification
        scores = {"academic": 0, "mental_health": 0, "admin": 0}

        for category, data in self.routes.items():
            for pattern in data["keywords"]:
                if re.search(pattern, query_lower):
                    scores[category] += 1

        best_route = max(scores, key=scores.get)
        if scores[best_route] == 0:
            best_route = "mental_health"

        # Urgency Check
        urgency = "low"
        if any(w in query_lower for w in ["suicide", "harm", "panic", "emergency", "die", "kill"]):
            urgency = "high"
        elif any(w in query_lower for w in ["overwhelm", "fail", "crying", "hopeless", "can't cope"]):
            urgency = "medium"

        return {
            "route": best_route,
            "agent_name": self.routes[best_route]["agent_name"],
            "cached_response": None,
            "intent": best_route,
            "urgency": urgency
        }

