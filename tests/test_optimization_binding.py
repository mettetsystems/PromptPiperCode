from __future__ import annotations

from prompt_piper_api.domain.requirement_card import OptimizationTargets, RequirementCard
from prompt_piper_api.services.embedding_service import EmbeddingService
from prompt_piper_api.services.optimization.engine import TokenOptimizationEngine
from prompt_piper_api.services.pre_inference_metrics_service import PreInferenceMetricsService
from prompt_piper_api.services.quality_gate_service import QualityGateService
from prompt_piper_api.services.requirement_capture import RequirementCaptureEvaluator


def _fastapi_card() -> RequirementCard:
    return RequirementCard(
        core_task_scope={
            "task_type": "new feature logic",
            "objective": (
                "Implement a FastAPI endpoint that creates users with Pydantic validation "
                "and returns the persisted user record"
            ),
            "out_of_scope": ["Auth redesign", "Frontend changes"],
        },
        technical_context={
            "environment": "Python 3.12 with FastAPI and Pydantic v2",
            "integration_points": ["UserCreate", "UserRead", "create_user()"],
            "dependency_policy": "allow listed third-party packages",
            "forbidden_libraries": ["requests"],
        },
        inputs_outputs_contracts={
            "inputs": "JSON body with email and full_name",
            "output_contract": "201 JSON with id, email, full_name",
            "examples": ['POST /users {"email":"a@b.com","full_name":"Ada"}'],
        },
        architectural_rules={
            "design_patterns": ["repository pattern", "async/await"],
            "coding_style": "typed, explicit error handling",
            "non_functional": [
                "no speculative claims about schema",
                "cite existing model fields only",
                "easy to scan quickly",
            ],
        },
        edge_cases_error_strategy={
            "failure_handling": "raise HTTPException with problem details",
            "bad_inputs": ["missing email", "duplicate email"],
            "edge_cases": ["unicode names", "empty full_name"],
        },
        response_formatting={
            "explanation_level": "brief rationale then code",
            "verbosity": "concise",
            "extra_artifacts": ["pytest unit tests"],
        },
        optimization_targets=OptimizationTargets(richness="include enough detail for newcomers"),
    )


def _fastapi_canonical() -> str:
    return "\n".join(
        [
            "Technical Context",
            "-----------------",
            "Environment: Python 3.12 with FastAPI and Pydantic v2",
            "Integration points: UserCreate; UserRead; create_user()",
            "Dependency policy: allow listed third-party packages",
            "Forbidden libraries: requests",
            "",
            "Core Task and Scope",
            "-------------------",
            "Task type: new feature logic",
            "Objective: Implement a FastAPI endpoint that creates users with Pydantic "
            "validation and returns the persisted user record",
            "Out of scope: Auth redesign; Frontend changes",
            "",
            "Inputs, Outputs, and Contracts",
            "------------------------------",
            "Inputs: JSON body with email and full_name",
            "Output contract: 201 JSON with id, email, full_name",
            'Example: POST /users {"email":"a@b.com","full_name":"Ada"}',
            "",
            "Architectural Rules and Constraints",
            "-----------------------------------",
            "Design patterns: repository pattern; async/await",
            "Coding style: typed, explicit error handling",
            "no speculative claims about schema",
            "cite existing model fields only",
            "easy to scan quickly",
            "",
            "Edge Cases and Error Strategy",
            "-----------------------------",
            "Failure handling: raise HTTPException with problem details",
            "Bad inputs: missing email; duplicate email",
            "Handle edge case: unicode names",
            "Handle edge case: empty full_name",
            "",
            "Response Formatting",
            "-------------------",
            "Explanation level: brief rationale then code",
            "Verbosity: concise",
            "Extra artifacts: pytest unit tests",
        ]
    )


def test_mustang_like_optimization_passes_binding_capture_gate() -> None:
    card = _fastapi_card()
    canonical = _fastapi_canonical()
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
