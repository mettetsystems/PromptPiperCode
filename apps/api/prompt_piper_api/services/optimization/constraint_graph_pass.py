from __future__ import annotations

import re

from prompt_piper_api.domain.optimization import ConstraintGraph, ConstraintSlot, DetectedConflict
from prompt_piper_api.domain.requirement_card import RequirementCard

_SECTION_RE = re.compile(
    r"^(Technical Context|Core Task and Scope|Inputs, Outputs, and Contracts|"
    r"Architectural Rules and Constraints|Edge Cases and Error Strategy|"
    r"Response Formatting)\n-+\n",
    re.MULTILINE | re.IGNORECASE,
)

_FILLER_PATTERNS = (
    re.compile(r"\b(please note that|it is important to|in order to)\b", re.I),
    re.compile(r"\b(as mentioned above|as stated earlier)\b", re.I),
)

_CONFLICT_RULES: tuple[tuple[str, str, str, bool], ...] = (
    (
        r"\b(exhaustive|comprehensive|all details)\b",
        r"\b(minimal tokens|be concise|keep it brief|short answer|code only)\b",
        "be exhaustive vs minimal tokens",
        True,
    ),
    (
        r"\b(cite|sources|references|must cite)\b",
        (
            r"\b(no external references|without citations|do not cite|"
            r"do not use external references)\b"
        ),
        "cite heavily vs no external references",
        True,
    ),
    (
        r"\b(plain text only|no markdown|plain text)\b",
        r"\b(table|chart|markdown|diagram)\b",
        "plain text only vs include tables and charts",
        True,
    ),
)


def estimate_tokens(text: str) -> int:
    return len(text.split())


def extract_section(body: str, title: str) -> list[str]:
    pattern = re.compile(
        rf"^{re.escape(title)}\n-+\n(.*?)(?=\n[A-Za-z].*\n-+\n|\Z)",
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(body)
    if not match:
        return []
    return [line.strip() for line in match.group(1).splitlines() if line.strip()]


class ConstraintGraphPass:
    """Pass 1: normalize instructions into typed slots and detect contradictions."""

    def run(self, body: str, card: RequirementCard) -> ConstraintGraph:
        slots: dict[str, list[str]] = {slot.value: [] for slot in ConstraintSlot}

        if card.objective.strip():
            slots[ConstraintSlot.OBJECTIVE.value].append(card.objective.strip())
        slots[ConstraintSlot.OBJECTIVE.value].extend(
            extract_section(body, "Core Task and Scope")
        )

        if card.technical_context.environment.strip():
            slots[ConstraintSlot.AUDIENCE.value].append(
                card.technical_context.environment.strip()
            )
        for line in extract_section(body, "Technical Context"):
            if line.lower().startswith("environment:"):
                slots[ConstraintSlot.AUDIENCE.value].append(line.split(":", 1)[1].strip())

        slots[ConstraintSlot.SCOPE.value].extend(card.technical_context.integration_points)
        slots[ConstraintSlot.SCOPE.value].extend(card.core_task_scope.out_of_scope)
        slots[ConstraintSlot.EXCLUSIONS.value].extend(card.technical_context.forbidden_libraries)
        slots[ConstraintSlot.EXCLUSIONS.value].extend(card.core_task_scope.out_of_scope)

        if card.inputs_outputs_contracts.output_contract.strip():
            slots[ConstraintSlot.FORMAT.value].append(
                card.inputs_outputs_contracts.output_contract.strip()
            )
        slots[ConstraintSlot.FORMAT.value].extend(
            extract_section(body, "Inputs, Outputs, and Contracts")
        )

        for constraint in card.architectural_rules.non_functional:
            lowered = constraint.lower()
            if "token" in lowered or "length" in lowered:
                slots[ConstraintSlot.TOKEN_BUDGET.value].append(constraint)
            elif "cite" in lowered or "source" in lowered:
                slots[ConstraintSlot.MUST_CITE.value].append(constraint)
            elif "vendor" in lowered:
                slots[ConstraintSlot.FINAL_VENDOR.value].append(constraint)
            elif "artifact" in lowered or "attachment" in lowered or "test" in lowered:
                slots[ConstraintSlot.ARTIFACT_REQUIRED.value].append(constraint)
            elif "concise" in lowered or "brief" in lowered or "short" in lowered:
                slots[ConstraintSlot.VERBOSITY.value].append(constraint)
            else:
                slots[ConstraintSlot.SCOPE.value].append(constraint)

        slots[ConstraintSlot.SCOPE.value].extend(card.architectural_rules.design_patterns)
        slots[ConstraintSlot.SCOPE.value].extend(
            extract_section(body, "Architectural Rules and Constraints")
        )
        slots[ConstraintSlot.SCOPE.value].extend(
            extract_section(body, "Edge Cases and Error Strategy")
        )

        if card.response_formatting.verbosity.strip():
            slots[ConstraintSlot.VERBOSITY.value].append(
                card.response_formatting.verbosity.strip()
            )
        if card.response_formatting.extra_artifacts:
            slots[ConstraintSlot.ARTIFACT_REQUIRED.value].extend(
                card.response_formatting.extra_artifacts
            )

        binding = self._binding_instructions(slots)
        contradictions = self._detect_contradictions(body, slots)

        return ConstraintGraph(
            slots={key: values for key, values in slots.items() if values},
            binding_instructions=binding,
            contradictions=contradictions,
        )

    @staticmethod
    def _binding_instructions(slots: dict[str, list[str]]) -> list[str]:
        binding: list[str] = []
        for slot in (
            ConstraintSlot.OBJECTIVE,
            ConstraintSlot.TOKEN_BUDGET,
            ConstraintSlot.FORMAT,
            ConstraintSlot.MUST_CITE,
            ConstraintSlot.ARTIFACT_REQUIRED,
        ):
            binding.extend(slots.get(slot.value, []))
        return binding

    @staticmethod
    def _detect_contradictions(body: str, slots: dict[str, list[str]]) -> list[DetectedConflict]:
        combined = body + "\n" + "\n".join(
            value for values in slots.values() for value in values
        )
        conflicts: list[DetectedConflict] = []
        for left_pattern, right_pattern, description, requires_human in _CONFLICT_RULES:
            left_match = re.search(left_pattern, combined, re.I)
            right_match = re.search(right_pattern, combined, re.I)
            if left_match and right_match:
                conflicts.append(
                    DetectedConflict(
                        left_instruction=left_match.group(0),
                        right_instruction=right_match.group(0),
                        description=description,
                        requires_human_decision=requires_human,
                    )
                )
        return conflicts
