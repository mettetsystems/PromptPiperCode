"""Ask The Locals — model insight about the current clarification question."""

from __future__ import annotations

import json

from pydantic import BaseModel

from prompt_piper_api.domain.requirement_card import RequirementCard
from prompt_piper_api.llm.base import ChatMessage, LLMClient
from prompt_piper_api.llm.fallback import with_llm_fallback
from prompt_piper_api.services.clarification_option_guides import build_quick_reply_guides
from prompt_piper_api.services.clarification_prompts import BEGINNER_PROMPTS, STANDARD_PROMPTS


class AskTheLocalsInsight(BaseModel):
    field_name: str
    insight: str = ""
    model_available: bool = False
    model_source: str | None = None
    message: str | None = None


class AskTheLocalsService:
    """On-demand explanatory insight for the active clarification question."""

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

        def unavailable(message: str) -> AskTheLocalsInsight:
            return AskTheLocalsInsight(
                field_name=field_name,
                insight="",
                model_available=False,
                model_source=model_source,
                message=message,
            )

        return with_llm_fallback(
            self._llm,
            lambda client: self._ask_with_llm(
                client,
                initial_request=initial_request,
                card=card,
                field_name=field_name,
                standard_prompt=standard_prompt,
                beginner_prompt=beginner_prompt,
                beginner_rationale=beginner_rationale,
                option_guides=option_guides,
                last_answer=last_answer,
                asked_fields=asked_fields or [],
                model_source=model_source,
            ),
            lambda: unavailable(
                "Ask The Locals is unavailable. Configure the current AI tooling model "
                "or an Ask The Locals API in Settings."
            ),
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
        last_answer: str | None,
        asked_fields: list[str],
        model_source: str | None,
    ) -> AskTheLocalsInsight:
        context = {
            "initial_request": initial_request,
            "requirement_card": card.model_dump(),
            "field_name": field_name,
            "standard_prompt": standard_prompt,
            "beginner_prompt": beginner_prompt,
            "beginner_rationale": beginner_rationale,
            "option_guides": option_guides,
            "last_answer": last_answer,
            "asked_fields": asked_fields,
        }
        response = llm.chat(
            [
                ChatMessage(
                    role="system",
                    content=(
                        "You help a person understand one clarification question for a coding "
                        "prompt workbench. Explain what the question is asking, why it matters "
                        "for the user's request, and how to choose among the default options. "
                        "Use plain, clear language (about 10th-grade reading level). "
                        "Do not invent project facts that are not in the context. "
                        "Return JSON with key: insight (2 to 4 short paragraphs of helpful "
                        "guidance; no markdown headings)."
                    ),
                ),
                ChatMessage(role="user", content=json.dumps(context)),
            ],
            response_format={"type": "json_object"},
        )
        payload = json.loads(response.content)
        insight = str(payload.get("insight", "")).strip()
        if not insight:
            insight = (
                f"{beginner_prompt}\n\n"
                f"{beginner_rationale or ''}\n\n"
                "Review the default options below and pick the closest match, "
                "or write your own answer."
            ).strip()

        return AskTheLocalsInsight(
            field_name=field_name,
            insight=insight,
            model_available=True,
            model_source=model_source,
            message="Local insight is ready.",
        )
