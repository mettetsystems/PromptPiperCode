from __future__ import annotations

from prompt_piper_api.domain.requirement_card import RequirementCard, OptimizationTargets
from prompt_piper_api.services.embedding_service import EmbeddingService
from prompt_piper_api.services.optimization.constraint_graph_pass import ConstraintGraphPass
from prompt_piper_api.services.optimization.engine import TokenOptimizationEngine
from prompt_piper_api.services.pre_inference_metrics_service import PreInferenceMetricsService
from prompt_piper_api.services.requirement_capture import (
    RequirementCaptureEvaluator,
    body_chunks,
    normalize_phrase_for_capture,
)


class GroupedSemanticEmbedder:
    """Test embedder that maps concept groups to identical vectors."""

    _GROUPS: tuple[frozenset[str], ...] = (
        frozenset({"propeller", "fan looking part of an airplane", "the fan looking part of an airplane"}),
        frozenset({"hood scoop", "part the air goes into a car hood", "a hood scoop"}),
        frozenset({"engineering managers", "engineering team"}),
    )

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            normalized = text.lower()
            group_id = "other"
            for index, group in enumerate(self._GROUPS):
                if any(token in normalized for token in group):
                    group_id = f"group-{index}"
                    break
            vectors.append(hash_embed(group_id, dimensions=384))
        return vectors


from prompt_piper_api.services.similarity_utils import hash_embed


def test_normalize_phrase_for_capture_ignores_vague_words() -> None:
    original = "Don't use really big words for beginners"
    cleaned = "Don't use big words for beginners"
    assert normalize_phrase_for_capture(original) == normalize_phrase_for_capture(cleaned)


def test_binding_capture_ignores_optional_card_fields() -> None:
    card = RequirementCard(
        objective="Summarize weekly engineering status for leadership review.",
        audience="Engineering managers",
        persona_role="technical writer explaining aviation mechanics",
        edge_cases=["when sources conflict"],
        example_outputs=["one-page explainer"],
        optimization_targets=OptimizationTargets(richness="include enough detail"),
    )
    body = "\n".join(
        [
            "Mission",
            "-------",
            "Summarize weekly engineering status for leadership review.",
            "",
            "Context",
            "-------",
            "Audience: Engineering managers",
        ]
    )
    graph = ConstraintGraphPass().run(body, card)
    evaluator = RequirementCaptureEvaluator(EmbeddingService(prefer_fallback=True))
    full_score = evaluator.score(body, card)
    binding_score = evaluator.score(body, card, constraint_graph=graph)
    assert full_score < 1.0
    assert binding_score == 1.0


def test_verbatim_requirement_still_captures() -> None:
    evaluator = RequirementCaptureEvaluator(EmbeddingService(prefer_fallback=True))
    card = RequirementCard(objective="Summarize weekly status", audience="Engineering managers")
    body = "Mission\n-------\nSummarize weekly status\n\nContext\n-------\nAudience: Engineering managers"

    assert evaluator.score(body, card) == 1.0


def test_rephrased_constraint_can_capture_lexically() -> None:
    evaluator = RequirementCaptureEvaluator(EmbeddingService(prefer_fallback=True))
    card = RequirementCard(constraints=["Keep the response within 300 words"])
    body = "Constraints\n---------------\nKeep the response within 300 words."

    assert evaluator.captures_phrase(
        card.constraints[0],
        body,
        body_chunks(body),
    )


def test_precise_refinement_counts_as_capture() -> None:
    embedding = EmbeddingService(embedder=GroupedSemanticEmbedder())
    evaluator = RequirementCaptureEvaluator(embedding)
    requirement = "the fan looking part of an airplane"
    body = "Output contract\n----------------\nInspect the propeller assembly before flight."

    assert evaluator.captures_phrase(requirement, body, body_chunks(body))


def test_unrelated_phrase_does_not_capture() -> None:
    embedding = EmbeddingService(embedder=GroupedSemanticEmbedder())
    evaluator = RequirementCaptureEvaluator(embedding)
    requirement = "the fan looking part of an airplane"
    body = "Mission\n-------\nWrite release notes for the billing team."

    assert not evaluator.captures_phrase(requirement, body, body_chunks(body))


def test_optimized_prompt_meets_capture_gate_for_typical_session() -> None:
    card = RequirementCard(
        objective="Summarize weekly engineering status for leadership review.",
        audience="Engineering managers",
        desired_output_shape="Bulleted summary with risks and next steps",
        constraints=["Keep the response within 300 words"],
    )
    body = "\n".join(
        [
            "Mission",
            "-------",
            "Summarize weekly engineering status for leadership review.",
            "",
            "Context",
            "-------",
            "Audience: Engineering managers",
            "Primary language: en",
            "",
            "Constraints",
            "---------------",
            "Keep the response within 300 words.",
            "",
            "Output contract",
            "----------------",
            "Bulleted summary with risks and next steps.",
        ]
    )
    optimization = TokenOptimizationEngine().optimize(body, card)
    metrics = PreInferenceMetricsService(
        capture_evaluator=RequirementCaptureEvaluator(EmbeddingService(prefer_fallback=True)),
    ).compute(optimization.optimized_body, card, optimization=optimization)

    assert metrics.requirement_capture_score >= 0.90
