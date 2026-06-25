from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from prompt_piper_api.domain import (
    OptimizationTargets,
    PromptDraft,
    PromptSession,
    RequirementCard,
    SessionState,
)
from pydantic import ValidationError


def test_requirement_card_creation_with_full_payload() -> None:
    card = RequirementCard(
        objective="Summarize quarterly reports for executives",
        audience="C-suite readers with limited time",
        input_materials=["Q1_report.pdf", "Q2_report.pdf"],
        constraints=["Max 500 words", "No speculative financial advice"],
        desired_output_shape="Bulleted executive summary with risks and opportunities",
        tone_style="Direct, neutral, board-ready",
        forbidden_content_actions=["Invent metrics", "Recommend trades"],
        success_criteria=["Captures top 3 risks", "Cites source sections"],
        language="en",
        optimization_targets=OptimizationTargets(
            richness="Add sector context where material",
            density="Prefer tight phrasing",
            efficiency="Single-pass summary",
            denoising="Remove duplicate figures",
            deconfliction="Resolve conflicting revenue statements",
        ),
        unresolved_fields=["tone_style"],
    )

    assert card.objective.startswith("Summarize")
    assert card.input_materials == ["Q1_report.pdf", "Q2_report.pdf"]
    assert card.optimization_targets.richness == "Add sector context where material"
    assert card.unresolved_fields == ["tone_style"]


def test_requirement_card_creation_minimal_defaults() -> None:
    card = RequirementCard(objective="Draft a user interview guide")

    assert card.objective == "Draft a user interview guide"
    assert card.language == "en"
    assert card.input_materials == []
    assert card.optimization_targets.richness is None
    assert card.optimization_targets.deconfliction is None


def test_optimization_targets_has_exactly_five_optional_slots() -> None:
    targets = OptimizationTargets()
    field_names = set(OptimizationTargets.model_fields)

    assert field_names == {
        "richness",
        "density",
        "efficiency",
        "denoising",
        "deconfliction",
    }
    assert targets.model_dump() == {
        "richness": None,
        "density": None,
        "efficiency": None,
        "denoising": None,
        "deconfliction": None,
    }

    populated = OptimizationTargets(
        richness="high",
        density="medium",
        efficiency="low",
        denoising="moderate",
        deconfliction="strict",
    )
    assert populated.model_dump(exclude_none=True) == {
        "richness": "high",
        "density": "medium",
        "efficiency": "low",
        "denoising": "moderate",
        "deconfliction": "strict",
    }

    with pytest.raises(ValidationError) as exc_info:
        OptimizationTargets(richness="high", extra_slot="not allowed")

    assert "extra_slot" in str(exc_info.value)


def test_session_state_enum_values_are_valid_and_complete() -> None:
    expected = {
        "intake",
        "clarifying",
        "edit",
        "finalized",
        "similarity_check",
        "artifact_generation",
        "optimization",
        "approval",
        "exported",
    }

    assert {state.value for state in SessionState} == expected
    assert SessionState("edit") is SessionState.EDIT
    assert SessionState.EDIT == "edit"

    with pytest.raises(ValueError):
        SessionState("unknown_state")


def test_prompt_session_accepts_valid_state_transitions_in_model() -> None:
    session = PromptSession(title="Onboarding email prompt")

    assert session.state is SessionState.INTAKE
    session.state = SessionState.CLARIFYING
    session.touch()

    assert session.state is SessionState.CLARIFYING
    assert session.updated_at >= session.created_at


def test_unresolved_fields_default_to_empty_list() -> None:
    card = RequirementCard()

    assert card.unresolved_fields == []

    card.mark_unresolved("objective", "audience")
    assert card.unresolved_fields == ["objective", "audience"]

    with pytest.raises(ValueError, match="Unknown requirement card fields"):
        card.mark_unresolved("not_a_real_field")


def test_draft_version_starts_at_one_and_increments() -> None:
    session_id = uuid4()
    first = PromptDraft(session_id=session_id, version=1, body="Initial draft")
    second = PromptDraft.create_revision(
        session_id=session_id,
        existing_drafts=[first],
        body="Revised draft",
        change_summary="Tightened objective",
    )

    assert first.version == 1
    assert second.version == 2
    assert PromptDraft.next_version([first, second]) == 3


def test_draft_create_revision_can_promote_single_canonical_draft() -> None:
    session_id = uuid4()
    first = PromptDraft(
        session_id=session_id,
        version=1,
        body="Draft v1",
        is_canonical=True,
    )
    second = PromptDraft.create_revision(
        session_id=session_id,
        existing_drafts=[first],
        body="Draft v2",
        make_canonical=True,
    )

    assert first.is_canonical is False
    assert second.is_canonical is True
    assert second.version == 2


def test_draft_version_must_be_at_least_one() -> None:
    with pytest.raises(ValidationError):
        PromptDraft(session_id=uuid4(), version=0, body="invalid")


def test_prompt_session_round_trip_preserves_nested_requirement_card() -> None:
    session = PromptSession(
        id=UUID("00000000-0000-4000-8000-000000000001"),
        title="Support macro",
        state=SessionState.EDIT,
        requirement_card=RequirementCard(objective="Reply to billing questions"),
        created_at=datetime(2026, 6, 15, 12, 0, tzinfo=UTC),
        updated_at=datetime(2026, 6, 15, 12, 30, tzinfo=UTC),
    )

    restored = PromptSession.model_validate(session.model_dump())

    assert restored.id == session.id
    assert restored.state is SessionState.EDIT
    assert restored.requirement_card.objective == "Reply to billing questions"
