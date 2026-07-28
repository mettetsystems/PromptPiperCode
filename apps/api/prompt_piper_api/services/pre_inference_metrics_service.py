from __future__ import annotations

import re

from prompt_piper_api.config import get_settings
from prompt_piper_api.domain.optimization import OptimizationResult
from prompt_piper_api.domain.pre_inference_metrics import PreInferenceMetrics
from prompt_piper_api.domain.requirement_card import RequirementCard
from prompt_piper_api.services.draft_generator import UNSPECIFIED
from prompt_piper_api.services.embedding_service import EmbeddingService
from prompt_piper_api.services.format_checker import format_adherence_score
from prompt_piper_api.services.optimization.constraint_graph_pass import ConstraintGraphPass
from prompt_piper_api.services.optimization.metrics import OptimizationMetricsCalculator
from prompt_piper_api.services.requirement_capture import RequirementCaptureEvaluator
from prompt_piper_api.services.semantic_precision import SemanticPrecisionEvaluator
from prompt_piper_api.services.tokenizer_approx import estimate_token_cost

_FIELD_SECTION_HINTS: dict[str, tuple[str, ...]] = {
    "core_task_scope.objective": ("objective", "core task"),
    "core_task_scope.task_type": ("task type", "core task"),
    "core_task_scope.out_of_scope": ("out of scope", "core task"),
    "technical_context.environment": ("environment", "technical context"),
    "technical_context.integration_points": ("integration points", "technical context"),
    "technical_context.dependency_policy": ("dependency policy", "technical context"),
    "technical_context.forbidden_libraries": ("forbidden libraries", "technical context"),
    "inputs_outputs_contracts.inputs": ("inputs", "inputs, outputs"),
    "inputs_outputs_contracts.output_contract": ("output contract", "inputs, outputs"),
    "inputs_outputs_contracts.examples": ("example", "inputs, outputs"),
    "architectural_rules.design_patterns": ("design patterns", "architectural"),
    "architectural_rules.coding_style": ("coding style", "architectural"),
    "architectural_rules.non_functional": ("non-functional", "architectural"),
    "edge_cases_error_strategy.failure_handling": ("failure handling", "edge cases"),
    "edge_cases_error_strategy.bad_inputs": ("bad inputs", "edge cases"),
    "edge_cases_error_strategy.edge_cases": ("edge case", "edge cases"),
    "response_formatting.explanation_level": ("explanation level", "response formatting"),
    "response_formatting.verbosity": ("verbosity", "response formatting"),
    "response_formatting.extra_artifacts": ("extra artifacts", "response formatting"),
    "optimization_targets": ("optimization", "technical context"),
}


class PreInferenceMetricsService:
    """Compute deterministic pre-inference quality metrics."""

    def __init__(
        self,
        *,
        embedding: EmbeddingService | None = None,
        capture_evaluator: RequirementCaptureEvaluator | None = None,
    ) -> None:
        if capture_evaluator is not None:
            self._capture = capture_evaluator
        else:
            if embedding is None:
                settings = get_settings()
                embedding = EmbeddingService(
                    model_name=settings.prompt_piper_embedding_model,
                    prefer_fallback=settings.prompt_piper_embedding_fallback,
                )
            self._capture = RequirementCaptureEvaluator(embedding)
        self._precision = SemanticPrecisionEvaluator()

    def compute(
        self,
        body: str,
        card: RequirementCard,
        *,
        optimization: OptimizationResult | None = None,
        baseline_body: str | None = None,
    ) -> PreInferenceMetrics:
        graph = (
            optimization.constraint_graph
            if optimization is not None
            else ConstraintGraphPass().run(body, card)
        )
        hard_conflicts = (
            optimization.hard_conflicts
            if optimization is not None
            else graph.contradictions
        )

        if optimization is not None:
            targets = optimization.metrics.targets
        else:
            calc = OptimizationMetricsCalculator()
            targets = calc.compute(
                original_body=baseline_body or body,
                optimized_body=body,
                graph=graph,
                removed_count=0,
                hard_conflicts=list(hard_conflicts),
                resolved_count=0,
            ).targets

        precision = self._precision.evaluate(body)

        return PreInferenceMetrics(
            requirement_capture_score=self._capture.score(
                body,
                card,
                constraint_graph=graph if optimization is not None else None,
            ),
            unspecified_field_honesty=self._unspecified_field_honesty(body, card),
            instruction_clarity=self._instruction_clarity(body),
            hard_conflict_count=len(hard_conflicts),
            format_adherence=format_adherence_score(body),
            token_cost_estimate=estimate_token_cost(body),
            richness_score=targets.richness,
            density_score=targets.density,
            efficiency_score=targets.efficiency,
            denoising_score=targets.denoising,
            deconfliction_score=targets.deconfliction,
            semantic_precision_score=precision.score,
            vague_language_count=len(precision.findings),
        )

    def _unspecified_field_honesty(self, body: str, card: RequirementCard) -> float:
        if not card.unresolved_fields:
            return 1.0

        for field_name in card.unresolved_fields:
            if not self._field_marked_unspecified(body, card, field_name):
                return 0.0
        return 1.0

    @staticmethod
    def _field_marked_unspecified(body: str, card: RequirementCard, field_name: str) -> bool:
        if field_name == "optimization_targets":
            targets = card.optimization_targets.model_dump()
            if any(value is not None and str(value).strip() for value in targets.values()):
                return True
        else:
            try:
                value = card.get_leaf(field_name)
            except ValueError:
                value = ""
            if isinstance(value, list):
                if value:
                    return True
            elif isinstance(value, str) and value.strip():
                return True

        hints = _FIELD_SECTION_HINTS.get(
            field_name,
            (field_name.split(".")[-1].replace("_", " "),),
        )
        for hint in hints:
            pattern = re.compile(
                rf"{re.escape(hint)}[^\n]*\b{re.escape(UNSPECIFIED)}\b",
                re.IGNORECASE,
            )
            if pattern.search(body):
                return True
            if re.search(rf"\b{re.escape(UNSPECIFIED)}\b", body, re.I) and hint in body.lower():
                return True
        return False

    @staticmethod
    def _instruction_clarity(body: str) -> float:
        if not body.strip():
            return 0.0
        lines = [line.strip() for line in body.splitlines() if line.strip()]
        if not lines:
            return 0.0

        score = 0.0
        if any(
            line.lower().startswith(
                ("technical context", "core task", "architectural", "inputs")
            )
            for line in lines
        ):
            score += 0.4
        imperative = sum(
            1
            for line in lines
            if re.match(
                r"^(keep|use|meet|avoid|do not|provide|implement|write|return|raise)\b",
                line,
                re.I,
            )
        )
        score += min(0.3, imperative * 0.1)
        avg_len = sum(len(line.split()) for line in lines) / len(lines)
        if 4 <= avg_len <= 24:
            score += 0.3
        elif avg_len < 40:
            score += 0.15
        return round(min(1.0, score), 2)
