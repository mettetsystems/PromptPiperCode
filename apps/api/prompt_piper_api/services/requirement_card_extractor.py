import json
import re

from prompt_piper_api.domain.requirement_card import LIST_LEAF_FIELDS, RequirementCard
from prompt_piper_api.llm.base import ChatMessage, LLMClient
from prompt_piper_api.llm.fallback import with_llm_fallback
from prompt_piper_api.services.clarification_question_ranker import is_unspecified_answer

_LINE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^objective:\s*(.+)$", re.IGNORECASE), "core_task_scope.objective"),
    (re.compile(r"^goal:\s*(.+)$", re.IGNORECASE), "core_task_scope.objective"),
    (re.compile(r"^task(?:\s+type)?:\s*(.+)$", re.IGNORECASE), "core_task_scope.task_type"),
    (re.compile(r"^out of scope:\s*(.+)$", re.IGNORECASE), "core_task_scope.out_of_scope"),
    (re.compile(r"^environment:\s*(.+)$", re.IGNORECASE), "technical_context.environment"),
    (re.compile(r"^stack:\s*(.+)$", re.IGNORECASE), "technical_context.environment"),
    (
        re.compile(r"^integration(?:\s+points)?:\s*(.+)$", re.IGNORECASE),
        "technical_context.integration_points",
    ),
    (
        re.compile(r"^dependenc(?:y|ies)(?:\s+policy)?:\s*(.+)$", re.IGNORECASE),
        "technical_context.dependency_policy",
    ),
    (
        re.compile(r"^forbidden(?:\s+libraries)?:\s*(.+)$", re.IGNORECASE),
        "technical_context.forbidden_libraries",
    ),
    (re.compile(r"^inputs?:\s*(.+)$", re.IGNORECASE), "inputs_outputs_contracts.inputs"),
    (
        re.compile(r"^output(?:\s+contract|\s+shape)?:\s*(.+)$", re.IGNORECASE),
        "inputs_outputs_contracts.output_contract",
    ),
    (re.compile(r"^format:\s*(.+)$", re.IGNORECASE), "inputs_outputs_contracts.output_contract"),
    (re.compile(r"^examples?:\s*(.+)$", re.IGNORECASE), "inputs_outputs_contracts.examples"),
    (
        re.compile(r"^design patterns?:\s*(.+)$", re.IGNORECASE),
        "architectural_rules.design_patterns",
    ),
    (re.compile(r"^style:\s*(.+)$", re.IGNORECASE), "architectural_rules.coding_style"),
    (re.compile(r"^coding style:\s*(.+)$", re.IGNORECASE), "architectural_rules.coding_style"),
    (re.compile(r"^constraint:\s*(.+)$", re.IGNORECASE), "architectural_rules.non_functional"),
    (re.compile(r"^constraints:\s*(.+)$", re.IGNORECASE), "architectural_rules.non_functional"),
    (re.compile(r"^nfr:\s*(.+)$", re.IGNORECASE), "architectural_rules.non_functional"),
    (
        re.compile(r"^failure(?:\s+handling)?:\s*(.+)$", re.IGNORECASE),
        "edge_cases_error_strategy.failure_handling",
    ),
    (re.compile(r"^errors?:\s*(.+)$", re.IGNORECASE), "edge_cases_error_strategy.failure_handling"),
    (re.compile(r"^bad inputs?:\s*(.+)$", re.IGNORECASE), "edge_cases_error_strategy.bad_inputs"),
    (re.compile(r"^edge cases:\s*(.+)$", re.IGNORECASE), "edge_cases_error_strategy.edge_cases"),
    (
        re.compile(r"^explanation(?:\s+level)?:\s*(.+)$", re.IGNORECASE),
        "response_formatting.explanation_level",
    ),
    (re.compile(r"^verbosity:\s*(.+)$", re.IGNORECASE), "response_formatting.verbosity"),
    (re.compile(r"^length:\s*(.+)$", re.IGNORECASE), "response_formatting.verbosity"),
    (
        re.compile(r"^extra artifacts?:\s*(.+)$", re.IGNORECASE),
        "response_formatting.extra_artifacts",
    ),
]


class RequirementCardExtractor:
    """Maps free-text requests onto coding RequirementCard leaves with LLM + rule fallback."""

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
        card.clear_leaf(field_name)
        if field_name not in card.unresolved_fields:
            card.unresolved_fields.append(field_name)

    def _extract_with_llm(self, llm: LLMClient, initial_request: str) -> RequirementCard:
        response = llm.chat(
            [
                ChatMessage(
                    role="system",
                    content=(
                        "Extract coding prompt requirements into JSON matching RequirementCard: "
                        "technical_context {environment, integration_points, dependency_policy, "
                        "forbidden_libraries}, core_task_scope {task_type, objective, out_of_scope}, "
                        "inputs_outputs_contracts {inputs, output_contract, examples}, "
                        "architectural_rules {design_patterns, coding_style, non_functional}, "
                        "edge_cases_error_strategy {failure_handling, bad_inputs, edge_cases}, "
                        "response_formatting {explanation_level, verbosity, extra_artifacts}."
                    ),
                ),
                ChatMessage(role="user", content=initial_request),
            ],
            response_format={"type": "json_object"},
        )
        payload = json.loads(response.content)
        card = RequirementCard.model_validate(payload)
        if not card.core_task_scope.objective:
            card.core_task_scope.objective = initial_request.strip()[:500]
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

        if not card.core_task_scope.objective and objective_lines:
            card.core_task_scope.objective = " ".join(objective_lines).strip()

        lowered = initial_request.lower()
        if not card.core_task_scope.task_type:
            if re.search(r"\b(test|pytest|unit test|coverage)\b", lowered):
                card.core_task_scope.task_type = "generating tests"
            elif re.search(r"\b(refactor|performance|optimize)\b", lowered):
                card.core_task_scope.task_type = "refactor legacy code"
            elif re.search(r"\b(debug|bug|fix|error)\b", lowered):
                card.core_task_scope.task_type = "debugging an issue"
            elif re.search(r"\b(feature|implement|add|endpoint|api)\b", lowered):
                card.core_task_scope.task_type = "new feature logic"

        if not card.technical_context.environment:
            if re.search(r"\bfastapi\b", lowered) or re.search(r"\bpydantic\b", lowered):
                card.technical_context.environment = (
                    "Python with FastAPI and Pydantic (match request details)"
                )
            elif re.search(r"\btypescript\b", lowered) or re.search(r"\breact\b", lowered):
                card.technical_context.environment = "TypeScript / React (match request details)"
            elif re.search(r"\bpython\b", lowered):
                card.technical_context.environment = "Python (match request details)"

        return card

    def _assign(self, card: RequirementCard, field_name: str, value: str) -> None:
        if field_name in LIST_LEAF_FIELDS:
            items = [part.strip() for part in re.split(r"[;\n]|,(?!\s)", value) if part.strip()]
            current: list[str] = list(card.get_leaf(field_name))
            for item in items:
                if item not in current:
                    current.append(item)
            card.set_leaf(field_name, current)
            return

        card.set_leaf(field_name, value)
