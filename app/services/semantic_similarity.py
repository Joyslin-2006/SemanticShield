
from sentence_transformers import SentenceTransformer, util

# Load the pretrained model once.
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def check_similarity(
    new_prompt: str,
    previous_prompts: list[str],
    threshold: float = 0.75,
) -> dict:
    if not previous_prompts:
        return {
            "similarity_score": 0.0,
            "similar": False,
            "matched_prompt": None,
        }

    new_embedding = model.encode(new_prompt, convert_to_tensor=True)

    previous_embeddings = model.encode(
        previous_prompts,
        convert_to_tensor=True,
    )

    scores = util.cos_sim(new_embedding, previous_embeddings)[0]

    best_index = int(scores.argmax().item())
    best_score = float(scores[best_index].item())

    return {
        "similarity_score": round(best_score, 4),
        "similar": best_score >= threshold,
        "matched_prompt": previous_prompts[best_index],
    }
