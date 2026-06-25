from __future__ import annotations

from prompt_piper_api.services.similarity_utils import cosine_similarity


def maximal_marginal_relevance(
    query_embedding: list[float],
    candidates: list[tuple[int, list[float]]],
    *,
    lambda_mult: float = 0.7,
    top_k: int = 5,
) -> list[int]:
    """Select diverse candidate indices using Maximal Marginal Relevance (MMR)."""
    if not candidates:
        return []

    selected_indices: list[int] = []
    remaining = list(candidates)

    while remaining and len(selected_indices) < top_k:
        best_score = float("-inf")
        best_position = 0
        best_index = remaining[0][0]

        for position, (candidate_index, candidate_embedding) in enumerate(remaining):
            relevance = cosine_similarity(query_embedding, candidate_embedding)
            if not selected_indices:
                mmr_score = relevance
            else:
                redundancy = max(
                    cosine_similarity(
                        candidate_embedding,
                        next(item[1] for item in candidates if item[0] == chosen),
                    )
                    for chosen in selected_indices
                )
                mmr_score = lambda_mult * relevance - (1.0 - lambda_mult) * redundancy
            if mmr_score > best_score:
                best_score = mmr_score
                best_position = position
                best_index = candidate_index

        selected_indices.append(best_index)
        remaining.pop(best_position)

    return selected_indices
