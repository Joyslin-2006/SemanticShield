
from collections import defaultdict, deque

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.services.rate_limiter import RateLimiter
from app.services.semantic_similarity import check_similarity
from app.services.pii_guardrail import check_and_anonymize
from app.services.prompt_injection import detect_prompt_injection
from app.services.toxicity_guardrail import detect_toxicity


router = APIRouter()

# Allow at most 5 accepted requests per IP in 60 seconds.
rate_limiter = RateLimiter(rate_limit=5, time_window=60)

# Retain the 10 most recent sanitized prompts per user.
prompt_history: dict[str, deque[str]] = defaultdict(
    lambda: deque(maxlen=10)
)


class CheckRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    prompt: str = Field(min_length=1, max_length=5000)


@router.get("/health")
def health_check():
    return {"status": "healthy"}


@router.post("/check")
def check_prompt(payload: CheckRequest, request: Request):
    # 1. Rate limiting
    client_ip = request.client.host if request.client else "unknown"

    allowed, retry_after = rate_limiter.is_allowed(client_ip)

    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "allowed": False,
                "reason": "Request rate limit exceeded",
            },
            headers={"Retry-After": str(retry_after)},
        )

    # 2. Detect and redact personal information.
    pii_result = check_and_anonymize(payload.prompt)

    # Use sanitized text in subsequent checks and history.
    sanitized_prompt = pii_result["anonymized_text"]

    # 3. Detect possible prompt injection.
    injection_result = detect_prompt_injection(payload.prompt)

    # 4. Evaluate toxic content.
    toxicity_result = detect_toxicity(payload.prompt)

    # 5. Compare against this user's recent prompts.
    previous_prompts = list(prompt_history[payload.user_id])

    similarity_result = check_similarity(
        sanitized_prompt,
        previous_prompts,
    )

    # Save the sanitized prompt, not the original.
    prompt_history[payload.user_id].append(sanitized_prompt)

    # PII is redacted, not automatically blocked.
    # The other three checks can block the prompt.
    is_blocked = (
        injection_result["detected"]
        or toxicity_result["detected"]
        or similarity_result["similar"]
    )

    reasons = []

    if injection_result["detected"]:
        reasons.append("Potential prompt injection detected")

    if toxicity_result["detected"]:
        reasons.append("Toxic content detected")

    if similarity_result["similar"]:
        reasons.append("Semantically similar prompt detected")

    if not reasons:
        if pii_result["detected"]:
            reasons.append("PII detected and redacted; other checks passed")
        else:
            reasons.append("All checks passed")

    return {
        "allowed": not is_blocked,
        "reason": reasons,
        "sanitized_prompt": sanitized_prompt,
        "checks": {
            "rate_limit": "passed",
            "pii": pii_result,
            "prompt_injection": injection_result,
            "toxicity": toxicity_result,
            "semantic_similarity": similarity_result,
        },
    }
