from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OptimizationTargets(BaseModel):
    """Exactly five optional optimization dimensions for prompt tuning."""

    model_config = ConfigDict(extra="forbid")

    richness: str | None = Field(
        default=None,
        description="Increase detail, nuance, and contextual depth.",
    )
    density: str | None = Field(
        default=None,
        description="Pack more signal into fewer tokens.",
    )
    efficiency: str | None = Field(
        default=None,
        description="Reduce latency, cost, or cognitive load.",
    )
    denoising: str | None = Field(
        default=None,
        description="Remove ambiguity, filler, and off-topic content.",
    )
    deconfliction: str | None = Field(
        default=None,
        description="Resolve contradictory instructions or constraints.",
    )


class TechnicalContext(BaseModel):
    """Dimension 1: environment, integration points, and dependency policy."""

    model_config = ConfigDict(extra="forbid")

    environment: str = Field(
        default="",
        description="Language version, framework, and key dependencies.",
    )
    integration_points: list[str] = Field(
        default_factory=list,
        description="Functions, types, schemas, or names the output must match.",
    )
    dependency_policy: str = Field(
        default="",
        description="Stdlib-only, allow listed packages, or open third-party use.",
    )
    forbidden_libraries: list[str] = Field(
        default_factory=list,
        description="Libraries or packages that must not be used.",
    )


class CoreTaskScope(BaseModel):
    """Dimension 2: single job and explicit non-goals."""

    model_config = ConfigDict(extra="forbid")

    task_type: str = Field(
        default="",
        description="Feature, refactor, debug, tests, or other coding job type.",
    )
    objective: str = Field(default="", description="Primary coding goal of the prompt.")
    out_of_scope: list[str] = Field(
        default_factory=list,
        description="Problems the model must not try to solve or include.",
    )


class InputsOutputsContracts(BaseModel):
    """Dimension 3: inputs, return shape, and examples."""

    model_config = ConfigDict(extra="forbid")

    inputs: str = Field(
        default="",
        description="Sample data structures, parameters, or request payloads.",
    )
    output_contract: str = Field(
        default="",
        description="Exact return structure (JSON schema, SQL, interface, etc.).",
    )
    examples: list[str] = Field(
        default_factory=list,
        description="Example inputs/outputs or formatting exemplars.",
    )


class ArchitecturalRules(BaseModel):
    """Dimension 4: design patterns, style, and non-functional requirements."""

    model_config = ConfigDict(extra="forbid")

    design_patterns: list[str] = Field(
        default_factory=list,
        description="Patterns such as repository, functional, OOP, async/await.",
    )
    coding_style: str = Field(
        default="",
        description="Coding style or design approach the model should follow.",
    )
    non_functional: list[str] = Field(
        default_factory=list,
        description="Memory, complexity, thread-safety, security, and similar NFRs.",
    )


class EdgeCasesErrorStrategy(BaseModel):
    """Dimension 5: failure handling and bad-input behavior."""

    model_config = ConfigDict(extra="forbid")

    failure_handling: str = Field(
        default="",
        description="How failures should be handled (exceptions, null, retry, log).",
    )
    bad_inputs: list[str] = Field(
        default_factory=list,
        description="Bad inputs the code will face (null, empty, rate limits, etc.).",
    )
    edge_cases: list[str] = Field(
        default_factory=list,
        description="Edge cases or exceptions the prompt must handle.",
    )


class ResponseFormatting(BaseModel):
    """Dimension 6: explanation level and response packaging."""

    model_config = ConfigDict(extra="forbid")

    explanation_level: str = Field(
        default="",
        description="Code-only, brief rationale, or step-by-step before code.",
    )
    verbosity: str = Field(
        default="",
        description="Desired length or detail level of the response.",
    )
    extra_artifacts: list[str] = Field(
        default_factory=list,
        description="Appended artifacts such as tests, comments, or migration notes.",
    )


# Leaf paths used by clarification, unresolved tracking, and edit patches.
LEAF_FIELD_NAMES: frozenset[str] = frozenset(
    {
        "technical_context.environment",
        "technical_context.integration_points",
        "technical_context.dependency_policy",
        "technical_context.forbidden_libraries",
        "core_task_scope.task_type",
        "core_task_scope.objective",
        "core_task_scope.out_of_scope",
        "inputs_outputs_contracts.inputs",
        "inputs_outputs_contracts.output_contract",
        "inputs_outputs_contracts.examples",
        "architectural_rules.design_patterns",
        "architectural_rules.coding_style",
        "architectural_rules.non_functional",
        "edge_cases_error_strategy.failure_handling",
        "edge_cases_error_strategy.bad_inputs",
        "edge_cases_error_strategy.edge_cases",
        "response_formatting.explanation_level",
        "response_formatting.verbosity",
        "response_formatting.extra_artifacts",
        "optimization_targets",
    }
)

LIST_LEAF_FIELDS: frozenset[str] = frozenset(
    {
        "technical_context.integration_points",
        "technical_context.forbidden_libraries",
        "core_task_scope.out_of_scope",
        "inputs_outputs_contracts.examples",
        "architectural_rules.design_patterns",
        "architectural_rules.non_functional",
        "edge_cases_error_strategy.bad_inputs",
        "edge_cases_error_strategy.edge_cases",
        "response_formatting.extra_artifacts",
    }
)

# Back-compat alias for imports that still use the old constant name.
REQUIREMENT_CARD_FIELD_NAMES = LEAF_FIELD_NAMES

DIMENSION_SECTION_TITLES: tuple[str, ...] = (
    "Technical Context",
    "Core Task and Scope",
    "Inputs, Outputs, and Contracts",
    "Architectural Rules and Constraints",
    "Edge Cases and Error Strategy",
    "Response Formatting",
)


class RequirementCard(BaseModel):
    """Coding-prompt intake card organized around six fundamental dimensions."""

    model_config = ConfigDict(extra="forbid")

    technical_context: TechnicalContext = Field(default_factory=TechnicalContext)
    core_task_scope: CoreTaskScope = Field(default_factory=CoreTaskScope)
    inputs_outputs_contracts: InputsOutputsContracts = Field(
        default_factory=InputsOutputsContracts
    )
    architectural_rules: ArchitecturalRules = Field(default_factory=ArchitecturalRules)
    edge_cases_error_strategy: EdgeCasesErrorStrategy = Field(
        default_factory=EdgeCasesErrorStrategy
    )
    response_formatting: ResponseFormatting = Field(default_factory=ResponseFormatting)
    optimization_targets: OptimizationTargets = Field(default_factory=OptimizationTargets)
    unresolved_fields: list[str] = Field(
        default_factory=list,
        description="Leaf field paths still needing clarification.",
    )

    @property
    def objective(self) -> str:
        """Convenience accessor used by titles, precision, and metrics."""
        return self.core_task_scope.objective

    @objective.setter
    def objective(self, value: str) -> None:
        self.core_task_scope.objective = value

    def mark_unresolved(self, *field_names: str) -> None:
        """Replace unresolved_fields with validated leaf field names."""
        unknown = set(field_names) - LEAF_FIELD_NAMES
        if unknown:
            msg = f"Unknown requirement card fields: {sorted(unknown)}"
            raise ValueError(msg)
        self.unresolved_fields = list(field_names)

    def get_leaf(self, field_name: str) -> Any:
        """Return a leaf value by dotted path (or optimization_targets model)."""
        if field_name == "optimization_targets":
            return self.optimization_targets
        parent_name, leaf_name = _split_leaf(field_name)
        parent = getattr(self, parent_name)
        return getattr(parent, leaf_name)

    def set_leaf(self, field_name: str, value: Any) -> None:
        """Set a leaf value by dotted path."""
        if field_name == "optimization_targets":
            if isinstance(value, OptimizationTargets):
                self.optimization_targets = value
            elif isinstance(value, dict):
                self.optimization_targets = OptimizationTargets.model_validate(value)
            else:
                msg = "optimization_targets expects a model or dict"
                raise TypeError(msg)
            return
        parent_name, leaf_name = _split_leaf(field_name)
        parent = getattr(self, parent_name)
        setattr(parent, leaf_name, value)

    def is_leaf_missing(self, field_name: str) -> bool:
        """True when a leaf is empty or still marked unresolved."""
        if field_name not in LEAF_FIELD_NAMES:
            return False
        if field_name in self.unresolved_fields:
            return True
        if field_name == "optimization_targets":
            targets = self.optimization_targets.model_dump()
            return all(value is None for value in targets.values())
        value = self.get_leaf(field_name)
        if isinstance(value, str):
            return not value.strip()
        if isinstance(value, list):
            return len(value) == 0
        return False

    def clear_leaf(self, field_name: str) -> None:
        """Empty a leaf without inventing a value (used for unspecified answers)."""
        if field_name == "optimization_targets":
            self.optimization_targets = OptimizationTargets()
            return
        if field_name in LIST_LEAF_FIELDS:
            self.set_leaf(field_name, [])
            return
        self.set_leaf(field_name, "")

    def coding_spec_dict(self) -> dict[str, Any]:
        """Structured coding-prompt spec for JSON/YAML export (no unresolved list)."""
        data = self.model_dump()
        data.pop("unresolved_fields", None)
        return data


def _split_leaf(field_name: str) -> tuple[str, str]:
    if field_name not in LEAF_FIELD_NAMES or field_name == "optimization_targets":
        msg = f"Unknown or non-leaf field: {field_name}"
        raise ValueError(msg)
    parent_name, leaf_name = field_name.split(".", 1)
    return parent_name, leaf_name
