
from functools import lru_cache

from detoxify import Detoxify


# Initial threshold; tune this using a representative test dataset.
TOXICITY_THRESHOLD = 0.80


@lru_cache(maxsize=1)
def get_model() -> Detoxify:
    # Load the pretrained model once and reuse it.
    return Detoxify("original")


def detect_toxicity(text: str) -> dict:
    if not text.strip():
        return {
            "detected": False,
            "toxicity_score": 0.0,
            "threshold": TOXICITY_THRESHOLD,
            "scores": {},
        }

    # Predict scores for the input text.
    raw_scores = get_model().predict(text)

    # Convert model outputs to ordinary Python floats.
    scores = {
        category: round(float(score), 4)
        for category, score in raw_scores.items()
    }

    toxicity_score = scores.get("toxicity", 0.0)

    return {
        "detected": toxicity_score >= TOXICITY_THRESHOLD,
        "toxicity_score": toxicity_score,
        "threshold": TOXICITY_THRESHOLD,
        "scores": scores,
    }
