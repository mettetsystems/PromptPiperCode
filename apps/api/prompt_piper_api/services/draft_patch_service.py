import json
import re

from pydantic import BaseModel

from prompt_piper_api.domain.edit_intent import EditIntent
from prompt_piper_api.domain.requirement_card import RequirementCard
from prompt_piper_api.llm.base import ChatMessage, LLMClient
from prompt_piper_api.llm.fallback import with_llm_fallback
from prompt_piper_api.services.draft_generator import DraftGenerator
from prompt_piper_api.services.requirement_card_extractor import RequirementCardExtractor

_TIGHTEN_CONSTRAINT = "Keep responses concise"
_EXPAND_CONSTRAINT = "Provide thorough detail where helpful"
_TOKEN_CONSTRAINT = "Optimize for token efficiency"


class EditPatchResult(BaseModel):
    intent: EditIntent
    semantic_diff: str
    change_summary: str
    updated_body: str
    updated_requirement_card: RequirementCard


class DraftPatchService:
    """Classifies edit intent, patches the requirement card, and regenerates drafts."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm
        self._generator = DraftGenerator(llm=llm)
        self._extractor = RequirementCardExtractor(llm=llm)

    def apply(self, card: RequirementCard, instruction: str, previous_body: str) -> EditPatchResult:
        return with_llm_fallback(
            self._llm,
            lambda client: self._apply_with_llm(client, card, instruction, previous_body),
            lambda: self._apply_rule_based(card, instruction, previous_body),
        )

    def classify(self, instruction: str) -> EditIntent:
        return self._classify_rule_based(instruction)

    def _apply_rule_based(
        self,
        card: RequirementCard,
        instruction: str,
        previous_body: str,
    ) -> EditPatchResult:
        before = card.model_copy(deep=True)
        intent = self._classify_rule_based(instruction)
        self._patch_card(card, intent, instruction)
        generated = self._generator.generate(card)
        card.unresolved_fields = list(generated.unresolved_fields)
        semantic_diff = self._semantic_diff_summary(before, card, intent, instruction)
        return EditPatchResult(
            intent=intent,
            semantic_diff=semantic_diff,
            change_summary=f"Applied {intent.value} edit.",
            updated_body=generated.body,
            updated_requirement_card=card.model_copy(deep=True),
        )

    def _apply_with_llm(
        self,
        llm: LLMClient,
        card: RequirementCard,
        instruction: str,
        previous_body: str,
    ) -> EditPatchResult:
        before = card.model_copy(deep=True)
        response = llm.chat(
            [
                ChatMessage(
                    role="system",
                    content=(
                        "Classify edit intent using the provided enum values, update the "
                        "coding requirement card (six nested dimensions), and return JSON with "
                        "intent, semantic_diff, and updated_requirement_card. semantic_diff must "
                        "be one short sentence."
                    ),
                ),
                ChatMessage(
                    role="user",
                    content=json.dumps(
                        {
                            "instruction": instruction,
                            "requirement_card": card.model_dump(),
                            "previous_draft": previous_body,
                            "allowed_intents": [intent.value for intent in EditIntent],
                        }
                    ),
                ),
            ],
            response_format={"type": "json_object"},
        )
        payload = json.loads(response.content)
        try:
            intent = EditIntent(str(payload.get("intent", EditIntent.OTHER.value)))
        except ValueError:
            intent = EditIntent.OTHER

        updated = RequirementCard.model_validate(payload.get("updated_requirement_card", card))
        card.technical_context = updated.technical_context
        card.core_task_scope = updated.core_task_scope
        card.inputs_outputs_contracts = updated.inputs_outputs_contracts
        card.architectural_rules = updated.architectural_rules
        card.edge_cases_error_strategy = updated.edge_cases_error_strategy
        card.response_formatting = updated.response_formatting
        card.optimization_targets = updated.optimization_targets
        card.unresolved_fields = updated.unresolved_fields

        generated = self._generator.generate(card)
        card.unresolved_fields = list(generated.unresolved_fields)
        semantic_diff = str(payload.get("semantic_diff", "")).strip()
        if not semantic_diff:
            semantic_diff = self._semantic_diff_summary(before, card, intent, instruction)

        return EditPatchResult(
            intent=intent,
            semantic_diff=semantic_diff,
            change_summary=str(payload.get("change_summary", f"Applied {intent.value} edit.")),
            updated_body=generated.body,
            updated_requirement_card=card.model_copy(deep=True),
        )

    def _classify_rule_based(self, instruction: str) -> EditIntent:
        text = instruction.strip().lower()
        if re.search(r"\b(remove requirement|drop requirement|delete requirement)\b", text):
            return EditIntent.REMOVE_REQUIREMENT
        if re.search(r"\b(add requirement|include requirement|also require|must also)\b", text):
            return EditIntent.ADD_REQUIREMENT
        if re.search(r"\b(remove constraint|drop constraint|relax constraint)\b", text):
            return EditIntent.REMOVE_CONSTRAINT
        if re.search(r"\b(add constraint|must not|do not|avoid|never)\b", text):
            return EditIntent.ADD_CONSTRAINT
        if re.search(
            r"\b(clarify|specify|fill in|define)\b.*\b("
            r"objective|environment|stack|output|contract|explanation|style)\b",
            text,
        ):
            return EditIntent.CLARIFY_UNSPECIFIED_FIELD
        if re.search(r"\b(clarify unspecified|specify unspecified)\b", text):
            return EditIntent.CLARIFY_UNSPECIFIED_FIELD
        if re.search(r"\b(token|tokens|token budget|optimize for tokens)\b", text):
            return EditIntent.OPTIMIZE_FOR_TOKENS
        if re.search(r"\b(shorter|concise|brief|trim|tighten)\b", text):
            return EditIntent.TIGHTEN_LANGUAGE
        if re.search(r"\b(longer|expand|more detail|elaborate)\b", text):
            return EditIntent.EXPAND_DETAIL
        if re.search(
            r"\b(tone|style|explanation|code only|step-by-step|formal|casual)\b",
            text,
        ):
            return EditIntent.CHANGE_TONE
        if re.search(
            r"\b(format|output contract|output shape|output:|shape:|json|sql|interface)\b",
            text,
        ):
            return EditIntent.CHANGE_OUTPUT_SHAPE
        return EditIntent.OTHER

    def _patch_card(self, card: RequirementCard, intent: EditIntent, instruction: str) -> None:
        cleaned = instruction.strip()
        if intent is EditIntent.ADD_REQUIREMENT:
            requirement = self._extract_payload(
                cleaned,
                ("add requirement:", "include requirement:"),
            )
            value = requirement or cleaned
            if value not in card.architectural_rules.non_functional:
                card.architectural_rules.non_functional.append(value)
        elif intent is EditIntent.REMOVE_REQUIREMENT:
            target = self._extract_payload(cleaned, ("remove requirement:", "drop requirement:"))
            self._remove_matching(card.architectural_rules.non_functional, target or cleaned)
        elif intent is EditIntent.CHANGE_TONE:
            tone = self._extract_payload(
                cleaned,
                (
                    "explanation:",
                    "explanation level:",
                    "tone:",
                    "style:",
                    "make it",
                    "switch tone to",
                    "change tone to",
                ),
            )
            value = tone or cleaned
            card.response_formatting.explanation_level = value
            if "style" in cleaned.lower() and "coding" in cleaned.lower():
                card.architectural_rules.coding_style = value
        elif intent is EditIntent.CHANGE_OUTPUT_SHAPE:
            shape = self._extract_payload(
                cleaned,
                (
                    "change output contract to",
                    "change output shape to",
                    "output contract:",
                    "output shape:",
                    "format:",
                    "output:",
                    "shape:",
                    "change output to",
                ),
            )
            card.inputs_outputs_contracts.output_contract = shape or cleaned
        elif intent is EditIntent.ADD_CONSTRAINT:
            constraint = self._extract_payload(
                cleaned,
                ("add constraint:", "constraint:", "must not", "avoid", "prefer"),
            )
            value = constraint or cleaned.split(" and change tone")[0].strip()
            if value not in card.architectural_rules.non_functional:
                card.architectural_rules.non_functional.append(value)
            if "change tone to" in cleaned.lower() or "explanation" in cleaned.lower():
                tone = self._extract_payload(
                    cleaned,
                    ("change tone to", "tone to", "explanation level:", "explanation:"),
                )
                if tone:
                    card.response_formatting.explanation_level = tone
        elif intent is EditIntent.REMOVE_CONSTRAINT:
            target = self._extract_payload(cleaned, ("remove constraint:", "drop constraint:"))
            self._remove_matching(card.architectural_rules.non_functional, target or cleaned)
        elif intent is EditIntent.TIGHTEN_LANGUAGE:
            if _TIGHTEN_CONSTRAINT not in card.architectural_rules.non_functional:
                card.architectural_rules.non_functional.append(_TIGHTEN_CONSTRAINT)
            card.response_formatting.verbosity = "very concise"
        elif intent is EditIntent.EXPAND_DETAIL:
            if _EXPAND_CONSTRAINT not in card.architectural_rules.non_functional:
                card.architectural_rules.non_functional.append(_EXPAND_CONSTRAINT)
            card.response_formatting.verbosity = "comprehensive and thorough"
        elif intent is EditIntent.OPTIMIZE_FOR_TOKENS:
            card.optimization_targets.efficiency = "reduce token usage"
            if _TOKEN_CONSTRAINT not in card.architectural_rules.non_functional:
                card.architectural_rules.non_functional.append(_TOKEN_CONSTRAINT)
        elif intent is EditIntent.CLARIFY_UNSPECIFIED_FIELD:
            self._clarify_unspecified_field(card, cleaned)
        else:
            if card.core_task_scope.objective:
                card.core_task_scope.objective = f"{card.core_task_scope.objective} ({cleaned})"
            else:
                card.core_task_scope.objective = cleaned

    def _clarify_unspecified_field(self, card: RequirementCard, instruction: str) -> None:
        lowered = instruction.lower()
        value = self._extract_payload(
            instruction,
            ("clarify objective:", "objective:", "specify objective:", "set objective to"),
        )
        if "objective" in lowered:
            self._extractor.apply_answer(card, "core_task_scope.objective", value or instruction)
            return
        value = self._extract_payload(
            instruction,
            ("environment:", "stack:", "specify environment:", "set environment to"),
        )
        if "environment" in lowered or "stack" in lowered:
            self._extractor.apply_answer(
                card,
                "technical_context.environment",
                value or instruction,
            )
            return
        value = self._extract_payload(
            instruction,
            ("output contract:", "output shape:", "format:", "specify output:", "set output to"),
        )
        if "output" in lowered or "shape" in lowered or "format" in lowered or "contract" in lowered:
            self._extractor.apply_answer(
                card,
                "inputs_outputs_contracts.output_contract",
                value or instruction,
            )
            return
        value = self._extract_payload(
            instruction,
            ("explanation:", "explanation level:", "tone:", "style:", "set explanation to"),
        )
        if "explanation" in lowered or "tone" in lowered or "style" in lowered:
            self._extractor.apply_answer(
                card,
                "response_formatting.explanation_level",
                value or instruction,
            )

    def _semantic_diff_summary(
        self,
        before: RequirementCard,
        after: RequirementCard,
        intent: EditIntent,
        instruction: str,
    ) -> str:
        parts: list[str] = []

        added_constraints = [
            item
            for item in after.architectural_rules.non_functional
            if item not in before.architectural_rules.non_functional
        ]
        removed_constraints = [
            item
            for item in before.architectural_rules.non_functional
            if item not in after.architectural_rules.non_functional
        ]
        before_expl = before.response_formatting.explanation_level
        after_expl = after.response_formatting.explanation_level
        before_contract = before.inputs_outputs_contracts.output_contract
        after_contract = after.inputs_outputs_contracts.output_contract
        before_env = before.technical_context.environment
        after_env = after.technical_context.environment

        if before_expl != after_expl and after_expl.strip():
            parts.append(f"set explanation level to {after_expl.strip()}")
        if before_contract != after_contract and after_contract.strip():
            parts.append(f"changed output contract to {after_contract.strip()}")
        if before_env != after_env and after_env.strip():
            parts.append(f"set environment to {after_env.strip()}")
        if added_constraints:
            parts.append(f"added {added_constraints[0].lower()}")
        if removed_constraints:
            parts.append(f"removed {removed_constraints[0].lower()}")
        if (
            before.optimization_targets.efficiency != after.optimization_targets.efficiency
            and after.optimization_targets.efficiency
        ):
            parts.append("optimized for token efficiency")
        if before.objective != after.objective and after.objective.strip():
            parts.append("updated the objective")

        if parts:
            sentence = ", ".join(parts)
            return sentence[0].upper() + sentence[1:] + "."

        fallback = {
            EditIntent.TIGHTEN_LANGUAGE: "Tightened language for brevity.",
            EditIntent.EXPAND_DETAIL: "Expanded detail in the draft.",
            EditIntent.OPTIMIZE_FOR_TOKENS: "Optimized the draft for token efficiency.",
            EditIntent.CLARIFY_UNSPECIFIED_FIELD: "Clarified a previously unspecified field.",
            EditIntent.OTHER: f"Applied edit: {instruction.strip()}.",
        }
        default = f"Updated the draft based on the {intent.value.replace('_', ' ')} request."
        return fallback.get(intent, default)

    def _extract_payload(self, text: str, prefixes: tuple[str, ...]) -> str:
        lowered = text.lower()
        for prefix in prefixes:
            if prefix in lowered:
                index = lowered.index(prefix)
                return text[index + len(prefix) :].strip(" :-")
        return ""

    def _remove_matching(self, values: list[str], target: str) -> None:
        target_lower = target.lower()
        values[:] = [value for value in values if target_lower not in value.lower()]
