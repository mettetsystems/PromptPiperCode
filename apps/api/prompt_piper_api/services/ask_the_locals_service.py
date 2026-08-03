"""Ask The Locals — contextual recommendations for the current clarification question."""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field

from prompt_piper_api.domain.requirement_card import LEAF_FIELD_NAMES, RequirementCard
from prompt_piper_api.llm.base import ChatMessage, LLMClient
from prompt_piper_api.services.clarification_option_guides import build_quick_reply_guides
from prompt_piper_api.services.clarification_prompts import BEGINNER_PROMPTS, STANDARD_PROMPTS


class AskTheLocalsInsight(BaseModel):
    field_name: str
    insight: str = ""
    recommended_answer: str = ""
    previous_answers_used: list[str] = Field(default_factory=list)
    model_available: bool = False
    model_source: str | None = None
    message: str | None = None


def collect_previous_answers(
    card: RequirementCard,
    *,
    exclude_field: str | None = None,
) -> dict[str, Any]:
    """Return non-empty requirement-card answers, excluding the active field."""
    answers: dict[str, Any] = {}
    for field_name in sorted(LEAF_FIELD_NAMES):
        if field_name == exclude_field:
            continue
        if card.is_leaf_missing(field_name):
            continue
        value = card.get_leaf(field_name)
        if field_name == "optimization_targets":
            dumped = value.model_dump() if hasattr(value, "model_dump") else value
            filled = {key: item for key, item in dumped.items() if item}
            if filled:
                answers[field_name] = filled
            continue
        answers[field_name] = value
    return answers


def parse_json_object(content: str) -> dict[str, Any]:
    """Parse a JSON object from model output, tolerating fences and extra text."""
    text = (content or "").strip()
    if not text:
        raise ValueError("Empty model response")

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]

    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("Model JSON was not an object")
    return payload


def build_guide_fallback(
    *,
    field_name: str,
    beginner_prompt: str,
    beginner_rationale: str | None,
    option_guides: list[dict[str, str]],
    previous_answers: dict[str, Any],
    initial_request: str,
    model_source: str | None,
    message: str,
) -> AskTheLocalsInsight:
    """Build a useful recommendation when the model is unavailable or fails."""
    usable_guides = [
        guide
        for guide in option_guides
        if str(guide.get("option", "")).strip().lower() not in {"", "unspecified"}
    ]
    recommended = usable_guides[0]["option"].strip() if usable_guides else ""
    if not recommended:
        recommended = (
            f"Based on your request ({initial_request[:160].strip()}), "
            "write a short concrete answer for this field."
        )

    insight_parts = [
        beginner_prompt.strip(),
    ]
    if beginner_rationale:
        insight_parts.append(beginner_rationale.strip())
    if previous_answers:
        prior = "; ".join(
            f"{key}={_short_value(value)}" for key, value in list(previous_answers.items())[:4]
        )
        insight_parts.append(
            "Stay consistent with answers you already gave: " + prior + "."
        )
    if usable_guides:
        top = usable_guides[0]
        insight_parts.append(
            f'A strong default option is "{top["option"]}": {top.get("explanation", "").strip()} '
            f'Best when: {top.get("when_to_use", "").strip()}'
        )
    insight_parts.append(
        "Copy the recommendation below into Custom answer, or pick a quick reply that matches."
    )

    return AskTheLocalsInsight(
        field_name=field_name,
        insight="\n\n".join(part for part in insight_parts if part),
        recommended_answer=recommended,
        previous_answers_used=list(previous_answers.keys()),
        model_available=False,
        model_source=model_source,
        message=message,
    )


def _short_value(value: Any, limit: int = 80) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=True)
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


class AskTheLocalsService:
    """On-demand contextual recommendations for the active clarification question."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm

    def ask(
        self,
        *,
        initial_request: str,
        card: RequirementCard,
        field_name: str,
        last_answer: str | None = None,
        asked_fields: list[str] | None = None,
        model_source: str | None = None,
    ) -> AskTheLocalsInsight:
        standard_prompt = STANDARD_PROMPTS.get(field_name, "What should this field contain?")
        beginner = BEGINNER_PROMPTS.get(field_name)
        beginner_prompt = beginner[0] if beginner else standard_prompt
        beginner_rationale = beginner[1] if beginner else None
        option_guides = [guide.model_dump() for guide in build_quick_reply_guides(field_name)]
        previous_answers = collect_previous_answers(card, exclude_field=field_name)

        if self._llm is None:
            return build_guide_fallback(
                field_name=field_name,
                beginner_prompt=beginner_prompt,
                beginner_rationale=beginner_rationale,
                option_guides=option_guides,
                previous_answers=previous_answers,
                initial_request=initial_request,
                model_source=model_source,
                message=(
                    "Model unavailable — showing guide-based recommendation. "
                    "Start your local model or configure Ask The Locals API in Settings."
                ),
            )

        try:
            health = self._llm.health_check()
            if not health.ok:
                return build_guide_fallback(
                    field_name=field_name,
                    beginner_prompt=beginner_prompt,
                    beginner_rationale=beginner_rationale,
                    option_guides=option_guides,
                    previous_answers=previous_answers,
                    initial_request=initial_request,
                    model_source=model_source,
                    message=(
                        f"Model unreachable ({health.message}). "
                        "Showing guide-based recommendation instead."
                    ),
                )
            return self._ask_with_llm(
                self._llm,
                initial_request=initial_request,
                card=card,
                field_name=field_name,
                standard_prompt=standard_prompt,
                beginner_prompt=beginner_prompt,
                beginner_rationale=beginner_rationale,
                option_guides=option_guides,
                previous_answers=previous_answers,
                last_answer=last_answer,
                asked_fields=asked_fields or [],
                model_source=model_source,
            )
        except Exception as exc:  # noqa: BLE001 - surface failure as useful fallback
            return build_guide_fallback(
                field_name=field_name,
                beginner_prompt=beginner_prompt,
                beginner_rationale=beginner_rationale,
                option_guides=option_guides,
                previous_answers=previous_answers,
                initial_request=initial_request,
                model_source=model_source,
                message=f"Ask The Locals model call failed ({exc}). Showing guide-based recommendation.",
            )

    def _ask_with_llm(
        self,
        llm: LLMClient,
        *,
        initial_request: str,
        card: RequirementCard,
        field_name: str,
        standard_prompt: str,
        beginner_prompt: str,
        beginner_rationale: str | None,
        option_guides: list[dict[str, str]],
        previous_answers: dict[str, Any],
        last_answer: str | None,
        asked_fields: list[str],
        model_source: str | None,
    ) -> AskTheLocalsInsight:
        context = {
            "initial_request": initial_request,
            "requirement_card": card.model_dump(),
            "previous_answers": previous_answers,
            "field_name": field_name,
            "standard_prompt": standard_prompt,
            "beginner_prompt": beginner_prompt,
            "beginner_rationale": beginner_rationale,
            "option_guides": option_guides,
            "last_answer": last_answer,
            "asked_fields": asked_fields,
        }
        messages = [
            ChatMessage(
                role="system",
                content=(
                    "You help a person answer one clarification question for a coding "
                    "prompt workbench. Use previous_answers and the requirement card to "
                    "give contextualized recommendations that stay consistent with what "
                    "they already decided. Explain briefly what the question is asking "
                    "and why it matters for their request. Prefer concrete wording they "
                    "can paste into a custom answer field. "
                    "Use plain, clear language (about 10th-grade reading level). "
                    "Do not invent project facts that contradict previous_answers; when "
                    "prior answers are empty, ground suggestions only in initial_request. "
                    "Return ONLY a JSON object with keys: "
                    "insight (2 to 4 short paragraphs of guidance; no markdown headings), "
                    "recommended_answer (one concise paste-ready answer for this field, "
                    "1 to 3 sentences or a short bullet-like phrase, no surrounding quotes)."
                ),
            ),
            ChatMessage(role="user", content=json.dumps(context)),
        ]

        response = self._chat_for_json(llm, messages)
        payload = parse_json_object(response.content)
        insight = str(payload.get("insight", "")).strip()
        recommended_answer = str(
            payload.get("recommended_answer") or payload.get("recommendation") or ""
        ).strip()
        if not insight:
            insight = (
                f"{beginner_prompt}\n\n"
                f"{beginner_rationale or ''}\n\n"
                "Review the default options below and pick the closest match, "
                "or write your own answer."
            ).strip()
        if not recommended_answer:
            recommended_answer = insight

        return AskTheLocalsInsight(
            field_name=field_name,
            insight=insight,
            recommended_answer=recommended_answer,
            previous_answers_used=list(previous_answers.keys()),
            model_available=True,
            model_source=model_source,
            message=(
                "Contextual recommendation ready."
                if previous_answers
                else "Local insight is ready."
            ),
        )

    @staticmethod
    def _chat_for_json(llm: LLMClient, messages: list[ChatMessage]):
        """Prefer json_object mode; retry without it for servers that reject the param."""
        try:
            return llm.chat(messages, response_format={"type": "json_object"})
        except Exception:
            return llm.chat(messages)
