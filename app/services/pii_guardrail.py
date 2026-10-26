
from functools import lru_cache

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig


@lru_cache(maxsize=1)
def get_analyzer() -> AnalyzerEngine:
    return AnalyzerEngine()


@lru_cache(maxsize=1)
def get_anonymizer() -> AnonymizerEngine:
    return AnonymizerEngine()


def check_and_anonymize(text: str) -> dict:
    # Step 1: Detect personally identifiable information.
    results = get_analyzer().analyze(
        text=text,
        language="en",
    )

    # Step 2: Replace all detected PII with the same placeholder.
    anonymized = get_anonymizer().anonymize(
        text=text,
        analyzer_results=results,
        operators={
            "DEFAULT": OperatorConfig(
                "replace",
                {"new_value": "<REDACTED>"},
            )
        },
    )

    # Step 3: Return entity types and confidence scores,
    # without exposing the original sensitive values.
    entities = [
        {
            "type": result.entity_type,
            "score": round(result.score, 4),
        }
        for result in results
    ]

    return {
        "detected": bool(results),
        "entities": entities,
        "anonymized_text": anonymized.text,
    }
