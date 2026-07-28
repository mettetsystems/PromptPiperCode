from __future__ import annotations

from prompt_piper_api.domain.requirement_card import OptimizationTargets, RequirementCard
from prompt_piper_api.services.embedding_service import EmbeddingService
from prompt_piper_api.services.optimization.constraint_graph_pass import ConstraintGraphPass
from prompt_piper_api.services.optimization.engine import TokenOptimizationEngine
from prompt_piper_api.services.pre_inference_metrics_service import PreInferenceMetricsService
from prompt_piper_api.services.requirement_capture import (
    RequirementCaptureEvaluator,
    body_chunks,
    normalize_phrase_for_capture,
)
from prompt_piper_api.services.similarity_utils import hash_embed


class GroupedSemanticEmbedder:
    """Test embedder that maps concept groups to identical vectors."""

    _GROUPS: tuple[frozenset[str], ...] = (
        frozenset({"propeller", "fan looking part of an airplane", "the fan looking part of an airplane"}),
        frozenset({"hood scoop", "part the air goes into a car hood", "a hood scoop"}),
        frozenset({"fastapi", "python with fastapi"}),
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


def test_normalize_phrase_for_capture_ignores_vague_words() -> None:
    original = "Don't use really big words for beginners"
    cleaned = "Don't use big words for beginners"
    assert normalize_phrase_for_capture(original) == normalize_phrase_for_capture(cleaned)


def test_binding_capture_ignores_optional_card_fields() -> None:
    card = RequirementCard(
        core_task_scope={
            "objective": "Add FastAPI endpoint for weekly engineering status summaries.",
            "task_type": "new feature logic",
        },
        technical_context={"environment": "Python with FastAPI"},
        edge_cases_error_strategy={"edge_cases": ["when sources conflict"]},
        inputs_outputs_contracts={"examples": ["one-page JSON example"]},
        optimization_targets=OptimizationTargets(richness="include enough detail"),
    )
    body = "\n".join(
        [
            "Core Task and Scope",
            "-------------------",
            "Task type: new feature logic",
            "Objective: Add FastAPI endpoint for weekly engineering status summaries.",
            "",
            "Technical Context",
            "-----------------",
            "Environment: Python with FastAPI",
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
    card = RequirementCard(
        core_task_scope={"objective": "Summarize weekly status"},
        technical_context={"environment": "Python with FastAPI"},
    )
    body = (
        "Core Task and Scope\n-------------------\nObjective: Summarize weekly status\n\n"
        "Technical Context\n-----------------\nEnvironment: Python with FastAPI"
    )

    assert evaluator.score(body, card) == 1.0


def test_rephrased_constraint_can_capture_lexically() -> None:
    evaluator = RequirementCaptureEvaluator(EmbeddingService(prefer_fallback=True))
    card = RequirementCard(
        architectural_rules={"non_functional": ["Keep the response within 300 words"]}
    )
    body = (
        "Architectural Rules and Constraints\n"
        "-----------------------------------\n"
        "Keep the response within 300 words."
    )

    assert evaluator.captures_phrase(
        card.architectural_rules.non_functional[0],
        body,
        body_chunks(body),
    )


def test_precise_refinement_counts_as_capture() -> None:
    embedding = EmbeddingService(embedder=GroupedSemanticEmbedder())
    evaluator = RequirementCaptureEvaluator(embedding)
    requirement = "the fan looking part of an airplane"
    body = (
        "Inputs, Outputs, and Contracts\n"
        "------------------------------\n"
        "Output contract: Inspect the propeller assembly before flight."
    )

    assert evaluator.captures_phrase(requirement, body, body_chunks(body))


def test_unrelated_phrase_does_not_capture() -> None:
    embedding = EmbeddingService(embedder=GroupedSemanticEmbedder())
    evaluator = RequirementCaptureEvaluator(embedding)
    requirement = "the fan looking part of an airplane"
    body = (
        "Core Task and Scope\n-------------------\n"
        "Objective: Write release notes for the billing team."
    )

    assert not evaluator.captures_phrase(requirement, body, body_chunks(body))


def test_optimized_prompt_meets_capture_gate_for_typical_session() -> None:
    card = RequirementCard(
        core_task_scope={
            "objective": "Add FastAPI endpoint for weekly engineering status summaries.",
            "task_type": "new feature logic",
        },
        technical_context={"environment": "Python with FastAPI and Pydantic"},
        inputs_outputs_contracts={
            "output_contract": "JSON with blockers, owners, and next steps",
        },
        architectural_rules={"non_functional": ["Keep the response within 300 words"]},
    )
    body = "\n".join(
        [
            "Technical Context",
            "-----------------",
            "Environment: Python with FastAPI and Pydantic",
            "",
            "Core Task and Scope",
            "-------------------",
            "Task type: new feature logic",
            "Objective: Add FastAPI endpoint for weekly engineering status summaries.",
            "",
            "Inputs, Outputs, and Contracts",
            "------------------------------",
            "Output contract: JSON with blockers, owners, and next steps.",
            "",
            "Architectural Rules and Constraints",
            "-----------------------------------",
            "Keep the response within 300 words.",
        ]
    )
    optimization = TokenOptimizationEngine().optimize(body, card)
    metrics = PreInferenceMetricsService(
        capture_evaluator=RequirementCaptureEvaluator(EmbeddingService(prefer_fallback=True)),
    ).compute(optimization.optimized_body, card, optimization=optimization)

    assert metrics.requirement_capture_score >= 0.90
