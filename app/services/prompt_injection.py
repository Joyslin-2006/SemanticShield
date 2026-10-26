
from functools import lru_cache

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


MODEL_NAME = "protectai/deberta-v3-base-prompt-injection-v2"
INJECTION_THRESHOLD = 0.50

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


@lru_cache(maxsize=1)
def load_model():
    # Load tokenizer and pretrained classifier only once.
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME
    )

    model.to(DEVICE)
    model.eval()

    return tokenizer, model


def detect_prompt_injection(prompt: str) -> dict:
    if not prompt.strip():
        return {
            "detected": False,
            "score": 0.0,
            "reason": "Empty prompt",
        }

    tokenizer, model = load_model()

    # Convert the text into tokens that the model understands.
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=512,
    )

    inputs = {
        name: tensor.to(DEVICE)
        for name, tensor in inputs.items()
    }

    # Inference does not need gradient calculation.
    with torch.inference_mode():
        outputs = model(**inputs)

        # Convert model logits into class probabilities.
        probabilities = torch.softmax(
            outputs.logits,
            dim=-1,
        )[0]

    # According to the model card:
    # class 0 = benign, class 1 = injection detected.
    injection_score = float(probabilities[1].item())

    return {
        "detected": injection_score >= INJECTION_THRESHOLD,
        "score": round(injection_score, 4),
        "threshold": INJECTION_THRESHOLD,
        "model": MODEL_NAME,
    }
