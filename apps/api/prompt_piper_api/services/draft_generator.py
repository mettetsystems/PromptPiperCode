import json
import re

from prompt_piper_api.domain.requirement_card import (
    DIMENSION_SECTION_TITLES,
    RequirementCard,
)
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
    "Separate the six coding dimensions: Technical Context; Core Task and Scope; "
    "Inputs, Outputs, and Contracts; Architectural Rules and Constraints; "
    "Edge Cases and Error Strategy; Response Formatting. "
    "Use clear, direct, auditable language. Prefer positive instructions. "
    "Do not use XML or markdown headings."
)


class DraftGenerator:
    """Builds an auditable plain-text coding prompt draft from a RequirementCard."""

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
                            "section_titles": list(DIMENSION_SECTION_TITLES),
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
            self._render_section("Technical Context", self._technical_context_lines(card)),
            self._render_section("Core Task and Scope", self._core_task_lines(card)),
            self._render_section(
                "Inputs, Outputs, and Contracts",
                self._io_contract_lines(card),
            ),
            self._render_section(
                "Architectural Rules and Constraints",
                self._architectural_lines(card),
            ),
            self._render_section(
                "Edge Cases and Error Strategy",
                self._edge_error_lines(card),
            ),
            self._render_section("Response Formatting", self._response_formatting_lines(card)),
        ]
        body = "\n\n".join(section for section in sections if section)
        return DraftGenerationResult.from_parts(body=body, unresolved_fields=unresolved)

    def _technical_context_lines(self, card: RequirementCard) -> list[str]:
        ctx = card.technical_context
        lines = [
            f"Environment: {self._text_or_unspecified(ctx.environment)}",
            self._list_label("Integration points", ctx.integration_points),
            f"Dependency policy: {self._text_or_unspecified(ctx.dependency_policy)}",
            self._list_label("Forbidden libraries", ctx.forbidden_libraries),
        ]
        optimization = self._optimization_lines(card)
        if optimization:
            lines.extend(optimization)
        return lines

    def _core_task_lines(self, card: RequirementCard) -> list[str]:
        scope = card.core_task_scope
        return [
            f"Task type: {self._text_or_unspecified(scope.task_type)}",
            f"Objective: {self._text_or_unspecified(scope.objective)}",
            self._list_label("Out of scope", scope.out_of_scope),
        ]

    def _io_contract_lines(self, card: RequirementCard) -> list[str]:
        io = card.inputs_outputs_contracts
        lines = [
            f"Inputs: {self._text_or_unspecified(io.inputs)}",
            f"Output contract: {self._text_or_unspecified(io.output_contract)}",
        ]
        if io.examples:
            lines.extend(f"Example: {item}" for item in io.examples)
        elif "inputs_outputs_contracts.examples" in card.unresolved_fields:
            lines.append("Examples: unspecified")
        return lines

    def _architectural_lines(self, card: RequirementCard) -> list[str]:
        rules = card.architectural_rules
        lines = [
            self._list_label("Design patterns", rules.design_patterns),
            f"Coding style: {self._text_or_unspecified(rules.coding_style)}",
        ]
        if rules.non_functional:
            lines.extend(
                self._positive_instruction(item) for item in rules.non_functional
            )
        else:
            lines.append(f"Non-functional requirements: {UNSPECIFIED}")
        return lines

    def _edge_error_lines(self, card: RequirementCard) -> list[str]:
        edge = card.edge_cases_error_strategy
        lines = [
            f"Failure handling: {self._text_or_unspecified(edge.failure_handling)}",
            self._list_label("Bad inputs", edge.bad_inputs),
        ]
        if edge.edge_cases:
            lines.extend(f"Handle edge case: {item}" for item in edge.edge_cases)
        elif "edge_cases_error_strategy.edge_cases" in card.unresolved_fields:
            lines.append("Edge cases: unspecified")
        return lines

    def _response_formatting_lines(self, card: RequirementCard) -> list[str]:
        fmt = card.response_formatting
        return [
            f"Explanation level: {self._text_or_unspecified(fmt.explanation_level)}",
            f"Verbosity: {self._text_or_unspecified(fmt.verbosity)}",
            self._list_label("Extra artifacts", fmt.extra_artifacts),
        ]

    def _optimization_lines(self, card: RequirementCard) -> list[str]:
        targets = card.optimization_targets
        labels = {
            "richness": targets.richness,
            "density": targets.density,
            "efficiency": targets.efficiency,
            "denoising": targets.denoising,
            "deconfliction": targets.deconfliction,
        }
        return [
            f"Optimization ({name}): {value}"
            for name, value in labels.items()
            if value and value.strip()
        ]

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
        unspecified = [
            field for field in CLARIFICATION_FIELD_PRIORITY if card.is_leaf_missing(field)
        ]
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

    def _looks_like_hallucinated(
        self,
        body: str,
        card: RequirementCard,
        unresolved: list[str],
    ) -> bool:
        if "<" in body and ">" in body:
            return True
        env_path = "technical_context.environment"
        if env_path in unresolved and not card.technical_context.environment.strip():
            env_pattern = re.compile(
                r"Environment:\s*(?!unspecified\b)([\w\s.+\d/-]+)",
                re.I,
            )
            match = env_pattern.search(body)
            if match and match.group(1).strip().lower() != UNSPECIFIED:
                return True
        return False
