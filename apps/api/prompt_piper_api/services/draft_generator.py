import json
import re

from prompt_piper_api.domain.requirement_card import RequirementCard
from prompt_piper_api.llm.base import ChatMessage, LLMClient
from prompt_piper_api.llm.fallback import with_llm_fallback
from prompt_piper_api.services.clarification_question_ranker import (
    CLARIFICATION_FIELD_PRIORITY,
    ClarificationQuestionRanker,
)
from prompt_piper_api.services.draft_result import DraftGenerationResult

UNSPECIFIED = "unspecified"

SECTION_RULES = (
    "Use plain text only. Do not invent unspecified fields; write 'unspecified' instead. "
    "Separate mission, context, constraints, style, output contract, and acceptance criteria. "
    "Use clear, direct, auditable language. Prefer positive instructions. "
    "Include forbidden content only when specified. Do not use XML or markdown headings."
)


class DraftGenerator:
    """Builds an auditable plain-text prompt draft from a RequirementCard."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm
        self._ranker = ClarificationQuestionRanker(llm=llm)

    def generate(self, card: RequirementCard) -> DraftGenerationResult:
        return with_llm_fallback(
            self._llm,
            lambda client: self._generate_with_llm(client, card),
            lambda: self._generate_rule_based(card),
        )

    def generate_body(self, card: RequirementCard) -> str:
        """Return only the draft body for callers that do not need metadata."""
        return self.generate(card).body

    def _generate_with_llm(self, llm: LLMClient, card: RequirementCard) -> DraftGenerationResult:
        unresolved = self._unspecified_fields(card)
        response = llm.chat(
            [
                ChatMessage(role="system", content=SECTION_RULES),
                ChatMessage(
                    role="user",
                    content=json.dumps(
                        {
                            "requirement_card": card.model_dump(),
                            "unresolved_fields": unresolved,
                        }
                    ),
                ),
            ],
        )
        body = response.content.strip()
        if not body or self._looks_like_hallucinated(body, card, unresolved):
            return self._generate_rule_based(card)
        return DraftGenerationResult.from_parts(body=body, unresolved_fields=unresolved)

    def _generate_rule_based(self, card: RequirementCard) -> DraftGenerationResult:
        unresolved = self._unspecified_fields(card)
        sections: list[str] = [
            self._render_section("Mission", self._mission_lines(card)),
            self._render_section("Context", self._context_lines(card)),
            self._render_section("Constraints", self._constraint_lines(card)),
            self._render_section("Style", self._style_lines(card)),
            self._render_section("Output contract", self._output_contract_lines(card)),
            self._render_section("Acceptance criteria", self._acceptance_lines(card)),
        ]

        forbidden_lines = self._forbidden_lines(card)
        if forbidden_lines:
            sections.append(self._render_section("Forbidden content or actions", forbidden_lines))
        elif self._is_implementation_report(card):
            sections.append(
                self._render_section("Forbidden content or actions", [UNSPECIFIED])
            )

        body = "\n\n".join(section for section in sections if section)
        return DraftGenerationResult.from_parts(body=body, unresolved_fields=unresolved)

    def _mission_lines(self, card: RequirementCard) -> list[str]:
        return [self._text_or_unspecified(card.objective)]

    def _context_lines(self, card: RequirementCard) -> list[str]:
        lines = [
            f"Background: {self._text_or_unspecified(card.context_background)}",
            f"Audience: {self._text_or_unspecified(card.audience)}",
            f"Persona or role: {self._text_or_unspecified(card.persona_role)}",
            self._list_label("Input materials", card.input_materials),
            f"Primary language: {self._text_or_unspecified(card.language)}",
        ]
        optimization = self._optimization_lines(card)
        if optimization:
            lines.extend(optimization)
        elif self._is_implementation_report(card):
            lines.append("Optimization targets: unspecified")
        return lines

    def _constraint_lines(self, card: RequirementCard) -> list[str]:
        if not card.constraints:
            return [UNSPECIFIED]
        return [self._positive_instruction(item) for item in card.constraints]

    def _style_lines(self, card: RequirementCard) -> list[str]:
        lines = [
            self._text_or_unspecified(card.tone_style),
            f"Verbosity: {self._text_or_unspecified(card.verbosity)}",
        ]
        return lines

    def _output_contract_lines(self, card: RequirementCard) -> list[str]:
        lines: list[str] = []
        if self._is_implementation_report(card):
            lines.extend(self._implementation_report_contract_lines(card))
        else:
            lines.append(self._text_or_unspecified(card.desired_output_shape))
        example_lines = self._example_output_lines(card)
        if example_lines:
            lines.extend(example_lines)
        return lines

    def _example_output_lines(self, card: RequirementCard) -> list[str]:
        if card.example_outputs:
            return [f"Example output: {item}" for item in card.example_outputs]
        if "example_outputs" in card.unresolved_fields:
            return ["Example outputs: unspecified"]
        return []

    def _implementation_report_contract_lines(self, card: RequirementCard) -> list[str]:
        lines = [
            "Generate an implementation report for the proposed feature.",
            "Use clear plain-text section headings for:",
            "Proposed feature",
            "Architecture",
            "Delivery plan",
            "Key risks",
            "Mitigations",
        ]
        shape = card.desired_output_shape.strip()
        if shape:
            lines.append(f"Report format: {shape}")
        return lines

    def _is_implementation_report(self, card: RequirementCard) -> bool:
        blob = f"{card.objective} {card.desired_output_shape}".lower()
        return "implementation report" in blob

    def _acceptance_lines(self, card: RequirementCard) -> list[str]:
        lines: list[str] = []
        if not card.success_criteria:
            lines.append(UNSPECIFIED)
        else:
            lines.extend(f"Meet this criterion: {item}" for item in card.success_criteria)
        edge_lines = self._edge_case_lines(card)
        if edge_lines:
            lines.extend(edge_lines)
        return lines

    def _edge_case_lines(self, card: RequirementCard) -> list[str]:
        if card.edge_cases:
            return [f"Handle edge case: {item}" for item in card.edge_cases]
        if "edge_cases" in card.unresolved_fields:
            return ["Edge cases: unspecified"]
        return []

    def _forbidden_lines(self, card: RequirementCard) -> list[str]:
        if not card.forbidden_content_actions:
            return []
        return [self._forbidden_instruction(item) for item in card.forbidden_content_actions]

    def _optimization_lines(self, card: RequirementCard) -> list[str]:
        targets = card.optimization_targets
        labels = {
            "richness": targets.richness,
            "density": targets.density,
            "efficiency": targets.efficiency,
            "denoising": targets.denoising,
            "deconfliction": targets.deconfliction,
        }
        lines = [
            f"Optimization ({name}): {value}"
            for name, value in labels.items()
            if value and value.strip()
        ]
        return lines

    def _render_section(self, title: str, lines: list[str]) -> str:
        divider = "-" * len(title)
        body = "\n".join(lines)
        return f"{title}\n{divider}\n{body}"

    def _text_or_unspecified(self, value: str) -> str:
        cleaned = value.strip()
        return cleaned if cleaned else UNSPECIFIED

    def _list_label(self, label: str, values: list[str]) -> str:
        if not values:
            return f"{label}: {UNSPECIFIED}"
        return f"{label}: {'; '.join(values)}"

    def _unspecified_fields(self, card: RequirementCard) -> list[str]:
        checks: dict[str, bool] = {
            "objective": not card.objective.strip(),
            "context_background": not card.context_background.strip(),
            "desired_output_shape": not card.desired_output_shape.strip(),
            "audience": not card.audience.strip(),
            "persona_role": not card.persona_role.strip(),
            "constraints": not card.constraints,
            "success_criteria": not card.success_criteria,
            "tone_style": not card.tone_style.strip(),
            "verbosity": not card.verbosity.strip(),
            "forbidden_content_actions": not card.forbidden_content_actions,
            "edge_cases": not card.edge_cases,
            "input_materials": not card.input_materials,
            "example_outputs": not card.example_outputs,
            "language": not card.language.strip(),
            "optimization_targets": all(
                value is None for value in card.optimization_targets.model_dump().values()
            ),
        }
        unspecified = [field for field in CLARIFICATION_FIELD_PRIORITY if checks[field]]
        card.mark_unresolved(*unspecified)
        return unspecified

    def _positive_instruction(self, constraint: str) -> str:
        cleaned = constraint.strip()
        lowered = cleaned.lower()
        if re.match(r"^do not exceed\s+", lowered):
            remainder = re.sub(r"^do not exceed\s+", "", cleaned, count=1, flags=re.IGNORECASE)
            return f"Keep the response within {remainder}".strip()
        replacements = (
            (r"^do not\s+", "Avoid "),
            (r"^don't\s+", "Avoid "),
            (r"^never\s+", "Always avoid "),
            (r"^no\s+", "Avoid "),
        )
        for pattern, prefix in replacements:
            if re.match(pattern, lowered):
                remainder = re.sub(pattern, "", cleaned, count=1, flags=re.IGNORECASE).strip()
                return f"{prefix}{remainder}".strip()
        if cleaned.endswith("."):
            return cleaned
        return cleaned

    def _forbidden_instruction(self, item: str) -> str:
        cleaned = item.strip()
        lowered = cleaned.lower()
        if lowered.startswith(("do not ", "don't ", "never ", "avoid ", "no ")):
            return cleaned[0].upper() + cleaned[1:]
        return f"Do not {cleaned}"

    def _looks_like_hallucinated(
        self,
        body: str,
        card: RequirementCard,
        unresolved: list[str],
    ) -> bool:
        if "<" in body and ">" in body:
            return True
        if "audience" in unresolved and card.audience.strip() == "":
            audience_pattern = re.compile(r"audience:\s*(?!unspecified\b)([\w\s-]+)", re.I)
            match = audience_pattern.search(body)
            if match and match.group(1).strip().lower() != UNSPECIFIED:
                return True
        return False
