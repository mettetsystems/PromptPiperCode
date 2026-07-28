from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from prompt_piper_api.domain import (
    CoreTaskScope,
    OptimizationTargets,
    PromptDraft,
    PromptSession,
    RequirementCard,
    SessionState,
    TechnicalContext,
)
from pydantic import ValidationError


def test_requirement_card_creation_with_full_payload() -> None:
    card = RequirementCard(
        technical_context=TechnicalContext(
            environment="Python 3.12 + FastAPI",
            integration_points=["UserCreate schema", "create_user()"],
            dependency_policy="allow listed third-party packages",
            forbidden_libraries=["requests"],
        ),
        core_task_scope=CoreTaskScope(
            task_type="new feature logic",
            objective="Add a FastAPI endpoint that creates users via Pydantic models",
            out_of_scope=["Auth redesign", "Frontend changes"],
        ),
        inputs_outputs_contracts={
            "inputs": "JSON body with email and name",
            "output_contract": "201 JSON with id, email, name",
            "examples": ['{"email": "a@b.com", "name": "Ada"}'],
        },
        architectural_rules={
            "design_patterns": ["repository pattern"],
            "coding_style": "typed, explicit error handling",
            "non_functional": ["Max 200ms p95 latency", "No speculative DB writes"],
        },
        edge_cases_error_strategy={
            "failure_handling": "raise HTTPException with problem details",
            "bad_inputs": ["missing email", "duplicate email"],
            "edge_cases": ["unicode names"],
        },
        response_formatting={
            "explanation_level": "brief rationale then code",
            "verbosity": "concise",
            "extra_artifacts": ["pytest unit tests"],
        },
        optimization_targets=OptimizationTargets(
            richness="Include schema validation details",
            density="Prefer tight phrasing",
            efficiency="Single-file change when possible",
            denoising="Remove unrelated CRUD endpoints",
            deconfliction="Resolve conflicting status codes",
        ),
        unresolved_fields=["response_formatting.explanation_level"],
    )

    assert card.objective.startswith("Add a FastAPI")
    assert card.technical_context.integration_points == ["UserCreate schema", "create_user()"]
    assert card.optimization_targets.richness == "Include schema validation details"
    assert card.unresolved_fields == ["response_formatting.explanation_level"]


def test_requirement_card_creation_minimal_defaults() -> None:
    card = RequirementCard(core_task_scope={"objective": "Draft a pytest suite for the auth module"})

    assert card.objective == "Draft a pytest suite for the auth module"
    assert card.technical_context.environment == ""
    assert card.inputs_outputs_contracts.examples == []
    assert card.optimization_targets.richness is None
    assert card.optimization_targets.deconfliction is None


def test_requirement_card_rejects_top_level_objective_kwarg() -> None:
    with pytest.raises(ValidationError):
        RequirementCard(objective="not allowed as constructor kwarg")


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

    card.mark_unresolved("core_task_scope.objective", "technical_context.environment")
    assert card.unresolved_fields == [
        "core_task_scope.objective",
        "technical_context.environment",
    ]

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
        requirement_card=RequirementCard(
            core_task_scope={"objective": "Implement password-reset API handlers"}
        ),
        created_at=datetime(2026, 6, 15, 12, 0, tzinfo=UTC),
        updated_at=datetime(2026, 6, 15, 12, 30, tzinfo=UTC),
    )

    restored = PromptSession.model_validate(session.model_dump())

    assert restored.id == session.id
    assert restored.state is SessionState.EDIT
    assert restored.requirement_card.objective == "Implement password-reset API handlers"
