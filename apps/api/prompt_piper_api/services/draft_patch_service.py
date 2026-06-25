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
                        "requirement card, and return JSON with intent, semantic_diff, and "
                        "updated_requirement_card. semantic_diff must be one short sentence."
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
        card.objective = updated.objective
        card.audience = updated.audience
        card.input_materials = updated.input_materials
        card.constraints = updated.constraints
        card.desired_output_shape = updated.desired_output_shape
        card.tone_style = updated.tone_style
        card.forbidden_content_actions = updated.forbidden_content_actions
        card.success_criteria = updated.success_criteria
        card.language = updated.language
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
            r"\b(clarify|specify|fill in|define)\b.*\b(audience|objective|output|tone)\b",
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
        if re.search(r"\b(tone|style|formal|casual|analytical|friendly|professional)\b", text):
            return EditIntent.CHANGE_TONE
        if re.search(r"\b(format|output shape|output:|shape:|bullet|json|table|structure)\b", text):
            return EditIntent.CHANGE_OUTPUT_SHAPE
        return EditIntent.OTHER

    def _patch_card(self, card: RequirementCard, intent: EditIntent, instruction: str) -> None:
        cleaned = instruction.strip()
        if intent is EditIntent.ADD_REQUIREMENT:
            requirement = self._extract_payload(
                cleaned,
                ("add requirement:", "include requirement:"),
            )
            card.success_criteria.append(requirement or cleaned)
        elif intent is EditIntent.REMOVE_REQUIREMENT:
            target = self._extract_payload(cleaned, ("remove requirement:", "drop requirement:"))
            self._remove_matching(card.success_criteria, target or cleaned)
        elif intent is EditIntent.CHANGE_TONE:
            tone = self._extract_payload(
                cleaned,
                ("tone:", "style:", "make it", "switch tone to", "change tone to"),
            )
            card.tone_style = tone or cleaned
        elif intent is EditIntent.CHANGE_OUTPUT_SHAPE:
            shape = self._extract_payload(
                cleaned,
                (
                    "change output shape to",
                    "output shape:",
                    "format:",
                    "output:",
                    "shape:",
                    "change output to",
                ),
            )
            card.desired_output_shape = shape or cleaned
        elif intent is EditIntent.ADD_CONSTRAINT:
            constraint = self._extract_payload(
                cleaned,
                ("add constraint:", "constraint:", "must not", "avoid", "prefer"),
            )
            value = constraint or cleaned.split(" and change tone")[0].strip()
            if value not in card.constraints:
                card.constraints.append(value)
            if "change tone to" in cleaned.lower():
                tone = self._extract_payload(cleaned, ("change tone to", "tone to"))
                if tone:
                    card.tone_style = tone
        elif intent is EditIntent.REMOVE_CONSTRAINT:
            target = self._extract_payload(cleaned, ("remove constraint:", "drop constraint:"))
            self._remove_matching(card.constraints, target or cleaned)
        elif intent is EditIntent.TIGHTEN_LANGUAGE:
            if _TIGHTEN_CONSTRAINT not in card.constraints:
                card.constraints.append(_TIGHTEN_CONSTRAINT)
        elif intent is EditIntent.EXPAND_DETAIL:
            if _EXPAND_CONSTRAINT not in card.constraints:
                card.constraints.append(_EXPAND_CONSTRAINT)
        elif intent is EditIntent.OPTIMIZE_FOR_TOKENS:
            card.optimization_targets.efficiency = "reduce token usage"
            if _TOKEN_CONSTRAINT not in card.constraints:
                card.constraints.append(_TOKEN_CONSTRAINT)
        elif intent is EditIntent.CLARIFY_UNSPECIFIED_FIELD:
            self._clarify_unspecified_field(card, cleaned)
        else:
            if card.objective:
                card.objective = f"{card.objective} ({cleaned})"
            else:
                card.objective = cleaned

    def _clarify_unspecified_field(self, card: RequirementCard, instruction: str) -> None:
        lowered = instruction.lower()
        value = self._extract_payload(
            instruction,
            ("clarify audience:", "audience:", "specify audience:", "set audience to"),
        )
        if "audience" in lowered:
            self._extractor.apply_answer(card, "audience", value or instruction)
            return
        value = self._extract_payload(
            instruction,
            ("clarify objective:", "objective:", "specify objective:", "set objective to"),
        )
        if "objective" in lowered:
            self._extractor.apply_answer(card, "objective", value or instruction)
            return
        value = self._extract_payload(
            instruction,
            ("output shape:", "format:", "specify output:", "set output to"),
        )
        if "output" in lowered or "shape" in lowered or "format" in lowered:
            self._extractor.apply_answer(card, "desired_output_shape", value or instruction)
            return
        value = self._extract_payload(instruction, ("tone:", "style:", "set tone to"))
        if "tone" in lowered or "style" in lowered:
            self._extractor.apply_answer(card, "tone_style", value or instruction)

    def _semantic_diff_summary(
        self,
        before: RequirementCard,
        after: RequirementCard,
        intent: EditIntent,
        instruction: str,
    ) -> str:
        parts: list[str] = []

        added_constraints = [item for item in after.constraints if item not in before.constraints]
        removed_constraints = [item for item in before.constraints if item not in after.constraints]
        added_requirements = [
            item for item in after.success_criteria if item not in before.success_criteria
        ]

        if before.tone_style != after.tone_style and after.tone_style.strip():
            parts.append(f"switched tone to {after.tone_style.strip()}")
        if (
            before.desired_output_shape != after.desired_output_shape
            and after.desired_output_shape.strip()
        ):
            parts.append(f"changed output shape to {after.desired_output_shape.strip()}")
        if added_requirements:
            parts.append(f"added requirement: {added_requirements[0]}")
        if added_constraints:
            parts.append(f"added {added_constraints[0].lower()}")
        if removed_constraints:
            parts.append(f"removed {removed_constraints[0].lower()}")
        if (
            before.optimization_targets.efficiency != after.optimization_targets.efficiency
            and after.optimization_targets.efficiency
        ):
            parts.append("optimized for token efficiency")
        if before.audience != after.audience and after.audience.strip():
            parts.append(f"clarified audience as {after.audience.strip()}")

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
        default = (
            f"Updated the draft based on the {intent.value.replace('_', ' ')} request."
        )
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
