from __future__ import annotations

from prompt_piper_api.domain.requirement_card import RequirementCard, OptimizationTargets
from prompt_piper_api.services.embedding_service import EmbeddingService
from prompt_piper_api.services.optimization.engine import TokenOptimizationEngine
from prompt_piper_api.services.pre_inference_metrics_service import PreInferenceMetricsService
from prompt_piper_api.services.quality_gate_service import QualityGateService
from prompt_piper_api.services.requirement_capture import RequirementCaptureEvaluator


def _mustang_card() -> RequirementCard:
    return RequirementCard(
        objective=(
            "I would like to write a paper the covers the key part of a Mustang plane "
            "and how the spinning bit works"
        ),
        context_background="research or analysis task",
        audience=(
            "mixed technical and business audience; It for a bunch of new people that came "
            "from the local college trying to improve their skills"
        ),
        language="en",
        constraints=["no speculative claims", "cite sources only", "easy to scan quickly"],
        tone_style=(
            "neutral and professional; Don't use really big words for people who are not "
            "the best at the field"
        ),
        desired_output_shape="short paragraph; bulleted summary",
        success_criteria=["easy to scan quickly"],
        persona_role="technical writer explaining aviation mechanics",
        verbosity="moderate length accessible to beginners",
        edge_cases=["when sources conflict", "when technical terms need defining"],
        example_outputs=["one-page explainer with bullet summary"],
        input_materials=["course notes from college workshop"],
        forbidden_content_actions=["invent historical facts"],
        optimization_targets=OptimizationTargets(richness="include enough detail for newcomers"),
    )


def _mustang_canonical() -> str:
    return "\n".join(
        [
            "Mission",
            "-------",
            "I would like to write a paper the covers the key part of a Mustang plane "
            "and how the spinning bit works",
            "",
            "Context",
            "-------",
            "Audience: mixed technical and business audience; It for a bunch of new people "
            "that came from the local college trying to improve their skills",
            "Primary language: en",
            "Background: research or analysis task",
            "",
            "Constraints",
            "---------------",
            "no speculative claims",
            "cite sources only",
            "easy to scan quickly",
            "",
            "Style",
            "-----",
            "neutral and professional; Don't use really big words for people who are not "
            "the best at the field",
            "",
            "Output contract",
            "----------------",
            "short paragraph; bulleted summary",
            "",
            "Acceptance criteria",
            "-------------------",
            "Meet this criterion: easy to scan quickly",
        ]
    )


def test_mustang_like_optimization_passes_binding_capture_gate() -> None:
    card = _mustang_card()
    canonical = _mustang_canonical()
    optimization = TokenOptimizationEngine().optimize(canonical, card)
    metrics_service = PreInferenceMetricsService(
        capture_evaluator=RequirementCaptureEvaluator(EmbeddingService(prefer_fallback=True)),
    )
    metrics = metrics_service.compute(
        optimization.optimized_body,
        card,
        optimization=optimization,
    )

    assert metrics.requirement_capture_score >= 0.90
    assert metrics.unspecified_field_honesty == 1.0
    assert metrics.format_adherence == 1.0
    assert QualityGateService(metrics_service=metrics_service).evaluate_for_approval(
        optimization.optimized_body,
        card,
        optimization,
    ).passed
