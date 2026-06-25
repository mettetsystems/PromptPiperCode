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


REQUIREMENT_CARD_FIELD_NAMES: frozenset[str] = frozenset(
    {
        "objective",
        "context_background",
        "audience",
        "persona_role",
        "input_materials",
        "constraints",
        "desired_output_shape",
        "tone_style",
        "verbosity",
        "forbidden_content_actions",
        "success_criteria",
        "example_outputs",
        "edge_cases",
        "language",
        "optimization_targets",
    }
)


class RequirementCard(BaseModel):
    """Structured intake card capturing what the prompt must accomplish."""

    objective: str = Field(default="", description="Primary goal of the prompt.")
    context_background: str = Field(
        default="",
        description="Domain, situational, or product background the model should assume.",
    )
    audience: str = Field(default="", description="Who will consume the model output.")
    persona_role: str = Field(
        default="",
        description="Role or persona the model should adopt when responding.",
    )
    input_materials: list[str] = Field(
        default_factory=list,
        description="Reference documents, notes, or source material.",
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="Hard limits on scope, format, length, or behavior.",
    )
    desired_output_shape: str = Field(
        default="",
        description="Expected structure or format of the final output.",
    )
    tone_style: str = Field(default="", description="Voice, register, and stylistic guidance.")
    verbosity: str = Field(
        default="",
        description="Desired length, detail level, or response size.",
    )
    forbidden_content_actions: list[str] = Field(
        default_factory=list,
        description="Topics, actions, or patterns the prompt must avoid.",
    )
    success_criteria: list[str] = Field(
        default_factory=list,
        description="Observable conditions that define a successful result.",
    )
    example_outputs: list[str] = Field(
        default_factory=list,
        description="Example outputs, few-shot references, or formatting exemplars.",
    )
    edge_cases: list[str] = Field(
        default_factory=list,
        description="Edge cases, failure modes, or exceptions the prompt must handle.",
    )
    language: str = Field(default="en", description="Primary language for the prompt and output.")
    optimization_targets: OptimizationTargets = Field(
        default_factory=OptimizationTargets,
        description="Optional tuning goals across five fixed dimensions.",
    )
    unresolved_fields: list[str] = Field(
        default_factory=list,
        description="Requirement card field names still needing clarification.",
    )

    def mark_unresolved(self, *field_names: str) -> None:
        """Replace unresolved_fields with validated field names."""
        unknown = set(field_names) - REQUIREMENT_CARD_FIELD_NAMES
        if unknown:
            msg = f"Unknown requirement card fields: {sorted(unknown)}"
            raise ValueError(msg)
        self.unresolved_fields = list(field_names)
