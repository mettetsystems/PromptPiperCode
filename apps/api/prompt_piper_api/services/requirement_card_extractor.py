import json
import re

from prompt_piper_api.domain.requirement_card import RequirementCard
from prompt_piper_api.llm.base import ChatMessage, LLMClient
from prompt_piper_api.llm.fallback import with_llm_fallback
from prompt_piper_api.services.clarification_question_ranker import is_unspecified_answer

_LINE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^audience:\s*(.+)$", re.IGNORECASE), "audience"),
    (re.compile(r"^for:\s*(.+)$", re.IGNORECASE), "audience"),
    (re.compile(r"^tone:\s*(.+)$", re.IGNORECASE), "tone_style"),
    (re.compile(r"^style:\s*(.+)$", re.IGNORECASE), "tone_style"),
    (re.compile(r"^output(?:\s+shape)?:\s*(.+)$", re.IGNORECASE), "desired_output_shape"),
    (re.compile(r"^format:\s*(.+)$", re.IGNORECASE), "desired_output_shape"),
    (re.compile(r"^constraint:\s*(.+)$", re.IGNORECASE), "constraints"),
    (re.compile(r"^constraints:\s*(.+)$", re.IGNORECASE), "constraints"),
    (re.compile(r"^avoid:\s*(.+)$", re.IGNORECASE), "forbidden_content_actions"),
    (re.compile(r"^success:\s*(.+)$", re.IGNORECASE), "success_criteria"),
    (re.compile(r"^language:\s*(.+)$", re.IGNORECASE), "language"),
    (re.compile(r"^inputs?:\s*(.+)$", re.IGNORECASE), "input_materials"),
    (re.compile(r"^materials:\s*(.+)$", re.IGNORECASE), "input_materials"),
    (re.compile(r"^objective:\s*(.+)$", re.IGNORECASE), "objective"),
    (re.compile(r"^goal:\s*(.+)$", re.IGNORECASE), "objective"),
    (re.compile(r"^context:\s*(.+)$", re.IGNORECASE), "context_background"),
    (re.compile(r"^background:\s*(.+)$", re.IGNORECASE), "context_background"),
    (re.compile(r"^persona:\s*(.+)$", re.IGNORECASE), "persona_role"),
    (re.compile(r"^role:\s*(.+)$", re.IGNORECASE), "persona_role"),
    (re.compile(r"^verbosity:\s*(.+)$", re.IGNORECASE), "verbosity"),
    (re.compile(r"^length:\s*(.+)$", re.IGNORECASE), "verbosity"),
    (re.compile(r"^examples?:\s*(.+)$", re.IGNORECASE), "example_outputs"),
    (re.compile(r"^edge cases:\s*(.+)$", re.IGNORECASE), "edge_cases"),
]


class RequirementCardExtractor:
    """Maps free-text requests onto RequirementCard fields with LLM + rule fallback."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm

    def extract(self, initial_request: str) -> RequirementCard:
        return with_llm_fallback(
            self._llm,
            lambda client: self._extract_with_llm(client, initial_request),
            lambda: self._extract_rule_based(initial_request),
        )

    def apply_answer(self, card: RequirementCard, field_name: str, answer: str) -> None:
        """Write a clarification answer onto the requirement card."""
        cleaned = answer.strip()
        if not cleaned:
            msg = "Clarification answer cannot be empty"
            raise ValueError(msg)

        if is_unspecified_answer(cleaned):
            self._mark_unspecified(card, field_name)
            return

        if field_name == "optimization_targets":
            card.optimization_targets.richness = cleaned
            if field_name in card.unresolved_fields:
                card.unresolved_fields = [
                    name for name in card.unresolved_fields if name != field_name
                ]
            return

        self._assign(card, field_name, cleaned)
        if field_name in card.unresolved_fields:
            card.unresolved_fields = [name for name in card.unresolved_fields if name != field_name]

    def _mark_unspecified(self, card: RequirementCard, field_name: str) -> None:
        """Keep a field empty and explicitly unresolved rather than inventing a value."""
        if field_name == "optimization_targets":
            card.optimization_targets.richness = None
            card.optimization_targets.density = None
            card.optimization_targets.efficiency = None
            card.optimization_targets.denoising = None
            card.optimization_targets.deconfliction = None
        elif field_name in {
            "constraints",
            "success_criteria",
            "forbidden_content_actions",
            "input_materials",
            "example_outputs",
            "edge_cases",
        }:
            setattr(card, field_name, [])
        elif field_name == "language":
            card.language = ""
        else:
            setattr(card, field_name, "")

        if field_name not in card.unresolved_fields:
            card.unresolved_fields.append(field_name)

    def _extract_with_llm(self, llm: LLMClient, initial_request: str) -> RequirementCard:
        response = llm.chat(
            [
                ChatMessage(
                    role="system",
                    content=(
                        "Extract prompt requirements into JSON matching RequirementCard fields: "
                        "objective, context_background, audience, persona_role, input_materials, "
                        "constraints, desired_output_shape, tone_style, verbosity, "
                        "forbidden_content_actions, success_criteria, example_outputs, "
                        "edge_cases, language."
                    ),
                ),
                ChatMessage(role="user", content=initial_request),
            ],
            response_format={"type": "json_object"},
        )
        payload = json.loads(response.content)
        card = RequirementCard.model_validate(payload)
        if not card.objective:
            card.objective = initial_request.strip()[:500]
        return card

    def _extract_rule_based(self, initial_request: str) -> RequirementCard:
        card = RequirementCard()
        objective_lines: list[str] = []

        for raw_line in initial_request.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            matched = False
            for pattern, field_name in _LINE_PATTERNS:
                match = pattern.match(line)
                if match is None:
                    continue
                value = match.group(1).strip()
                self._assign(card, field_name, value)
                matched = True
                break

            if not matched:
                objective_lines.append(line)

        if not card.objective and objective_lines:
            card.objective = " ".join(objective_lines).strip()

        if re.search(r"\bimplementation reports?\b", initial_request, re.I):
            card.objective = (
                "Help an internal AI tool generate implementation reports for new features."
            )

        if card.language == "en" and re.search(
            r"\b(español|spanish|français|french|deutsch|german)\b", initial_request, re.I
        ):
            if re.search(r"\b(spanish|español)\b", initial_request, re.I):
                card.language = "es"
            elif re.search(r"\bfrench\b", initial_request, re.I):
                card.language = "fr"
            elif re.search(r"\bgerman\b", initial_request, re.I):
                card.language = "de"

        return card

    def _assign(self, card: RequirementCard, field_name: str, value: str) -> None:
        if field_name in {
            "constraints",
            "success_criteria",
            "forbidden_content_actions",
            "input_materials",
            "example_outputs",
            "edge_cases",
        }:
            items = [part.strip() for part in re.split(r"[;\n]|,(?!\s)", value) if part.strip()]
            current: list[str] = getattr(card, field_name)
            for item in items:
                if item not in current:
                    current.append(item)
            return

        setattr(card, field_name, value)
