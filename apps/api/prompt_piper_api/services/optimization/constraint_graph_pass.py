from __future__ import annotations

import re

from prompt_piper_api.domain.optimization import ConstraintGraph, ConstraintSlot, DetectedConflict
from prompt_piper_api.domain.requirement_card import RequirementCard

_SECTION_RE = re.compile(
    r"^(Mission|Context|Constraints|Style|Output contract|Acceptance criteria|"
    r"Forbidden content or actions)\n-+\n",
    re.MULTILINE | re.IGNORECASE,
)

_FILLER_PATTERNS = (
    re.compile(r"\b(please note that|it is important to|in order to)\b", re.I),
    re.compile(r"\b(as mentioned above|as stated earlier)\b", re.I),
)

_CONFLICT_RULES: tuple[tuple[str, str, str, bool], ...] = (
    (
        r"\b(exhaustive|comprehensive|all details)\b",
        r"\b(minimal tokens|be concise|keep it brief|short answer)\b",
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
        mission = extract_section(body, "Mission")
        slots[ConstraintSlot.OBJECTIVE.value].extend(mission)

        if card.audience.strip():
            slots[ConstraintSlot.AUDIENCE.value].append(card.audience.strip())
        for line in extract_section(body, "Context"):
            if line.lower().startswith("audience:"):
                slots[ConstraintSlot.AUDIENCE.value].append(line.split(":", 1)[1].strip())

        slots[ConstraintSlot.SCOPE.value].extend(card.input_materials)
        slots[ConstraintSlot.EXCLUSIONS.value].extend(card.forbidden_content_actions)

        if card.desired_output_shape.strip():
            slots[ConstraintSlot.FORMAT.value].append(card.desired_output_shape.strip())
        slots[ConstraintSlot.FORMAT.value].extend(extract_section(body, "Output contract"))

        slots[ConstraintSlot.EXCLUSIONS.value].extend(
            line for line in extract_section(body, "Forbidden content or actions")
        )

        for constraint in card.constraints:
            lowered = constraint.lower()
            if "token" in lowered or "length" in lowered:
                slots[ConstraintSlot.TOKEN_BUDGET.value].append(constraint)
            elif "cite" in lowered or "source" in lowered:
                slots[ConstraintSlot.MUST_CITE.value].append(constraint)
            elif "vendor" in lowered:
                slots[ConstraintSlot.FINAL_VENDOR.value].append(constraint)
            elif "artifact" in lowered or "attachment" in lowered:
                slots[ConstraintSlot.ARTIFACT_REQUIRED.value].append(constraint)
            elif "concise" in lowered or "brief" in lowered or "short" in lowered:
                slots[ConstraintSlot.VERBOSITY.value].append(constraint)
            else:
                slots[ConstraintSlot.SCOPE.value].append(constraint)

        slots[ConstraintSlot.SCOPE.value].extend(extract_section(body, "Constraints"))
        slots[ConstraintSlot.SCOPE.value].extend(
            line.removeprefix("Meet this criterion: ").strip()
            for line in extract_section(body, "Acceptance criteria")
            if not line.lower().startswith("unspecified")
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
