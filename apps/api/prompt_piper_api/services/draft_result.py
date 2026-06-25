from pydantic import BaseModel, Field


class DraftGenerationResult(BaseModel):
    """Structured output from the initial plain-text prompt draft generator."""

    body: str = Field(description="Full human-readable plain-text prompt draft.")
    unresolved_fields: list[str] = Field(
        default_factory=list,
        description="Requirement card fields still unspecified in the draft.",
    )
    unspecified_note: str = Field(
        description="Short note explaining what remains unspecified.",
    )

    @classmethod
    def from_parts(
        cls,
        *,
        body: str,
        unresolved_fields: list[str],
    ) -> "DraftGenerationResult":
        note = build_unspecified_note(unresolved_fields)
        return cls(body=body, unresolved_fields=unresolved_fields, unspecified_note=note)


def build_unspecified_note(unresolved_fields: list[str]) -> str:
    if not unresolved_fields:
        return "All tracked requirement fields are specified in this draft."
    joined = ", ".join(unresolved_fields)
    return (
        f"Still unspecified: {joined}. The draft marks these explicitly and does not invent values."
    )
