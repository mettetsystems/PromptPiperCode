from __future__ import annotations

from prompt_piper_api.domain.enums import SessionState
from prompt_piper_api.domain.optimization import (
    ConstraintGraph,
    OptimizationChangeLog,
    OptimizationMetrics,
    OptimizationResult,
    OptimizationTargetMetrics,
)
from prompt_piper_api.services.semantic_precision import (
    CATCH_ALL_NOUNS,
    LAZY_ADJECTIVES,
    PRECISION_THRESHOLD,
    SemanticPrecisionEvaluator,
)
from prompt_piper_api.services.session_service import SessionService


def test_lazy_adjectives_and_catch_all_nouns_are_detected() -> None:
    evaluator = SemanticPrecisionEvaluator()
    body = "Write a good summary about the thing and several issue areas in this field."
    result = evaluator.evaluate(body)

    terms = {finding.term.lower() for finding in result.findings}
    assert "good" in terms
    assert "thing" in terms
    assert "several" in terms
    assert "issue" in terms
    assert "field" in terms
    assert result.score < PRECISION_THRESHOLD
    for finding in result.findings:
        assert finding.line[finding.start : finding.end].lower() == finding.term.lower()


def test_finding_offsets_account_for_leading_whitespace() -> None:
    evaluator = SemanticPrecisionEvaluator()
    body = "  Write a good summary."
    findings = evaluator.evaluate(body).findings
    good = next(finding for finding in findings if finding.term.lower() == "good")
    assert good.line.startswith("  ")
    assert good.line[good.start : good.end].lower() == "good"


def test_empty_body_scores_perfectly() -> None:
    result = SemanticPrecisionEvaluator().evaluate("   \n  ")
    assert result.score == 1.0
    assert result.findings == []


def test_apply_replacement_updates_line() -> None:
    evaluator = SemanticPrecisionEvaluator()
    body = "Core Task and Scope\n-------------------\nDeliver a great outcome for the team."
    finding = evaluator.evaluate(body).findings[0]
    updated = evaluator.apply_replacement(
        body,
        line_number=finding.line_number,
        term=finding.term,
        replacement="measurable",
        start=finding.start,
        end=finding.end,
    )
    assert "measurable" in updated
    assert "great" not in updated.lower()


def test_apply_replacement_accepts_a_phrase() -> None:
    evaluator = SemanticPrecisionEvaluator()
    body = "Deliver a good summary for leadership."
    finding = next(item for item in evaluator.evaluate(body).findings if item.term.lower() == "good")
    updated = evaluator.apply_replacement(
        body,
        line_number=finding.line_number,
        term=finding.term,
        replacement="measurable weekly status",
        start=finding.start,
        end=finding.end,
    )
    assert "measurable weekly status" in updated
    assert "good" not in updated.lower()


def test_apply_replacement_treats_phrase_as_literal_text() -> None:
    evaluator = SemanticPrecisionEvaluator()
    body = "Write a good summary."
    finding = next(item for item in evaluator.evaluate(body).findings if item.term.lower() == "good")
    updated = evaluator.apply_replacement(
        body,
        line_number=finding.line_number,
        term=finding.term,
        replacement=r"passing pytest for login (\1 coverage)",
        start=finding.start,
        end=finding.end,
    )
    assert r"passing pytest for login (\1 coverage)" in updated
    assert "good" not in updated.lower()


def test_user_word_lists_are_covered() -> None:
    sample_adjective = next(iter(LAZY_ADJECTIVES))
    sample_noun = next(iter(CATCH_ALL_NOUNS))
    body = f"The {sample_adjective} {sample_noun} needs detail."
    findings = SemanticPrecisionEvaluator().evaluate(body).findings
    assert len(findings) >= 2


def test_apply_precision_replacement_updates_session_metrics() -> None:
    service = SessionService()
    created = service.create_session(
        initial_request="Summarize weekly engineering status for leadership."
    )
    session_id = created.record.session.id
    record = created.record
    record.session.state = SessionState.OPTIMIZATION
    record.optimization_result = OptimizationResult(
        original_body="Write a good summary of the thing with several big issue areas.",
        optimized_body="Write a good summary of the thing with several big issue areas.",
        constraint_graph=ConstraintGraph(),
        metrics=OptimizationMetrics(
            original_token_count=8,
            optimized_token_count=8,
            token_reduction_pct=0.0,
            constraints_per_token=0.5,
            targets=OptimizationTargetMetrics(
                richness=0.8,
                density=0.8,
                efficiency=0.8,
                denoising=0.8,
                deconfliction=1.0,
            ),
        ),
        changes=OptimizationChangeLog(),
        export_ready=True,
    )
    service._save(record)  # noqa: SLF001

    review = service.get_precision_review(session_id)
    assert review.findings
    assert review.refinement_available is True

    finding = review.findings[0]
    result = service.apply_precision_replacement(
        session_id,
        finding_id=finding.id,
        replacement="concise weekly engineering status",
    )
    assert result.pre_inference_metrics is not None
    assert result.pre_inference_metrics.semantic_precision_score >= review.score
    assert result.optimization_result is not None
    assert "concise weekly engineering status" in result.optimization_result.optimized_body
    assert result.optimization_result.changes.precision_improvements


def test_precision_refinement_available_when_score_above_threshold() -> None:
    service = SessionService()
    created = service.create_session(initial_request="Weekly status summary.")
    session_id = created.record.session.id
    record = created.record
    record.session.state = SessionState.OPTIMIZATION
    record.optimization_result = OptimizationResult(
        original_body="Deliver a good summary for leadership.",
        optimized_body="Deliver a good summary for leadership.",
        constraint_graph=ConstraintGraph(),
        metrics=OptimizationMetrics(
            original_token_count=6,
            optimized_token_count=6,
            token_reduction_pct=0.0,
            constraints_per_token=0.5,
            targets=OptimizationTargetMetrics(
                richness=0.8,
                density=0.8,
                efficiency=0.8,
                denoising=0.8,
                deconfliction=1.0,
            ),
        ),
        changes=OptimizationChangeLog(),
        export_ready=True,
    )
    service._save(record)  # noqa: SLF001

    review = service.get_precision_review(session_id)
    assert review.findings
    assert review.score >= PRECISION_THRESHOLD
    assert review.refinement_available is True
