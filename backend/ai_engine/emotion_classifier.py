import re


# Emotion lexicon. Patterns are matched as substrings against lowercased text,
# the same way AgentRouter matches its intent keywords, so stems like "stress"
# also cover "stressed" and "stressful". Word boundaries are only used for short
# words that would otherwise match inside unrelated ones.
#
# Declaration order is also the tie-break order: when two emotions match the
# same number of patterns, the one declared first wins.
EMOTION_KEYWORDS = {
    "stress": [
        r"stress",
        r"overwhelm",
        r"too much",
        r"pressure",
        r"deadline",
        r"workload",
        r"swamped",
        r"no time",
        r"keep up",
        r"\btense\b",
        r"piling up",
    ],
    "anxiety": [
        r"anxiet",
        r"anxious",
        r"worr",
        r"nervous",
        r"\bfear",
        r"afraid",
        r"scared",
        r"panic",
        r"dread",
        r"racing",
        r"restless",
        r"what if",
    ],
    "burnout": [
        r"burn ?ed? ?out",
        r"burnout",
        r"exhaust",
        r"drain",
        r"depleted",
        r"no energy",
        r"detached",
        r"\bnumb\b",
        r"\bempty\b",
        r"cynical",
        r"unmotivated",
        r"give up",
    ],
    "confusion": [
        r"confus",
        r"(do not|don.{0,2}t|dont) understand",
        r"(do not|don.{0,2}t|dont) know",
        r"\blost\b",
        r"unsure",
        r"unclear",
        r"no idea",
        r"\bstuck\b",
        r"puzzled",
    ],
    "neutral": [
        r"\bokay\b",
        r"\bok\b",
        r"\bfine\b",
        r"\bnormal\b",
        r"manageable",
        r"alright",
        r"\bgood\b",
        r"\bstable\b",
        r"\bcalm\b",
    ],
}

DEFAULT_EMOTION = "neutral"


class EmotionClassifier:
    """Keyword based emotion classifier.

    This replaced a sentence-transformers implementation that embedded the
    input with the MiniLM model and compared it to per-label prototype
    embeddings. That version pulled torch, transformers and
    sentence-transformers into the process, about 312 MB of resident memory,
    which put the app over the 512 MB limit of the hosting tier this project
    can afford. RAGEngine already made the same tradeoff for the same reason
    and retrieves by keyword.

    Accuracy is lower than the embedding version: this matches literal wording
    and does not understand paraphrase or negation. That is a known and
    accepted tradeoff, not an oversight.

    The return shape is unchanged, so `/emotion` and the voice journal keep
    working without any frontend change.
    """

    def __init__(self):
        """Precompile the lexicon once, since the service is a long lived singleton."""
        self.patterns = {
            label: [re.compile(p) for p in patterns]
            for label, patterns in EMOTION_KEYWORDS.items()
        }

    def predict(self, text: str):
        """Classify `text` and return {"emotion": label, "scores": {label: float}}.

        Scores are the share of total keyword matches each emotion accounts for,
        so they sum to 1.0. The previous implementation returned cosine
        similarities, which were on a different scale; nothing reads the
        individual numbers, they are stored on the voice journal entry and
        displayed only as the winning label.
        """
        if not isinstance(text, str) or not text.strip():
            return self._empty_result()

        lowered = text.lower()
        counts = {
            label: sum(1 for pattern in patterns if pattern.search(lowered))
            for label, patterns in self.patterns.items()
        }

        total = sum(counts.values())
        if total == 0:
            return self._empty_result()

        scores = {label: count / total for label, count in counts.items()}
        best = max(counts, key=counts.get)
        return {"emotion": best, "scores": scores}

    def _empty_result(self):
        """Result used when the text is unusable or matches nothing at all."""
        scores = {label: 0.0 for label in self.patterns}
        scores[DEFAULT_EMOTION] = 1.0
        return {"emotion": DEFAULT_EMOTION, "scores": scores}
