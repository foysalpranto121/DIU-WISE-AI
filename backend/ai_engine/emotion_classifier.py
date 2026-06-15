from sentence_transformers import SentenceTransformer, util


class EmotionClassifier:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.label_examples = {
            "stress": [
                "I feel overwhelmed with tasks and deadlines",
                "Everything feels too much right now",
            ],
            "anxiety": [
                "I am constantly worried about failing",
                "My mind keeps racing with fear",
            ],
            "burnout": [
                "I feel emotionally exhausted and detached",
                "I have no energy left for studying",
            ],
            "confusion": [
                "I don't understand this topic at all",
                "I am lost and unsure what to do next",
            ],
            "neutral": [
                "I am doing okay today",
                "My day is normal and manageable",
            ],
        }
        self.prototype_embeddings = {
            label: self.model.encode(examples, convert_to_tensor=True).mean(dim=0)
            for label, examples in self.label_examples.items()
        }

    def predict(self, text: str):
        txt_embedding = self.model.encode(text, convert_to_tensor=True)
        scores = {}
        for label, proto in self.prototype_embeddings.items():
            scores[label] = float(util.cos_sim(txt_embedding, proto).item())
        best = max(scores, key=scores.get)
        return {"emotion": best, "scores": scores}
