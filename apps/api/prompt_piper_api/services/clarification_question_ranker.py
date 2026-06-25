import textwrap

from pydantic import BaseModel, Field, field_validator

from prompt_piper_api.domain.limits import MAX_CLARIFICATION_QUESTIONS
from prompt_piper_api.domain.requirement_card import REQUIREMENT_CARD_FIELD_NAMES, RequirementCard
from prompt_piper_api.llm.base import LLMClient

REQUIRED_CLARIFICATION_COUNT = MAX_CLARIFICATION_QUESTIONS

CLARIFICATION_FIELD_PRIORITY: tuple[str, ...] = (
    "objective",
    "desired_output_shape",
    "audience",
    "constraints",
    "success_criteria",
    "tone_style",
    "forbidden_content_actions",
    "input_materials",
    "language",
    "context_background",
    "persona_role",
    "verbosity",
    "example_outputs",
    "edge_cases",
    "optimization_targets",
)

IMPLEMENTATION_REPORT_FIELD_PRIORITY: tuple[str, ...] = (
    "audience",
    "desired_output_shape",
    "constraints",
    "success_criteria",
    "tone_style",
    "forbidden_content_actions",
    "input_materials",
    "language",
    "context_background",
    "persona_role",
    "verbosity",
    "example_outputs",
    "edge_cases",
    "optimization_targets",
)

REFINEMENT_FIELD_PRIORITY: tuple[str, ...] = (
    "desired_output_shape",
    "success_criteria",
    "tone_style",
    "constraints",
    "input_materials",
    "verbosity",
    "example_outputs",
    "edge_cases",
)

FOCUSED_PROMPTS: dict[str, str] = {
    "objective": "what should this prompt primarily accomplish?",
    "context_background": "what background or domain context should the model assume?",
    "desired_output_shape": "what shape or format should the output take?",
    "audience": "who is the output for?",
    "persona_role": "what role or persona should the model adopt?",
    "constraints": "what hard constraints should the prompt enforce?",
    "success_criteria": "how will you know the output succeeded?",
    "tone_style": "what tone or style should the output use?",
    "verbosity": "how long or detailed should responses be?",
    "forbidden_content_actions": "what must the model avoid doing or saying?",
    "edge_cases": "what edge cases or failure modes must be handled?",
    "input_materials": "what input materials will be provided at runtime?",
    "example_outputs": "what example outputs or formatting references should guide the model?",
    "language": "what language should the prompt and output use?",
    "optimization_targets": "which optimization goals matter most right now?",
}

QUICK_REPLY_OPTIONS: dict[str, tuple[str, ...]] = {
    "objective": (
        "summarize source material",
        "generate new copy or content",
        "extract structured facts",
        "coach or guide a workflow",
        "unspecified",
    ),
    "context_background": (
        "internal product or codebase",
        "customer support workflow",
        "research or analysis task",
        "general knowledge task",
        "unspecified",
    ),
    "desired_output_shape": (
        "bulleted summary",
        "short paragraph",
        "structured JSON",
        "markdown report",
        "unspecified",
    ),
    "audience": (
        "engineering team",
        "executive stakeholders",
        "mixed technical and business audience",
        "general end users",
        "unspecified",
    ),
    "persona_role": (
        "helpful assistant",
        "senior subject-matter expert",
        "technical writer",
        "support agent",
        "unspecified",
    ),
    "constraints": (
        "keep it under 500 words",
        "cite sources only",
        "no speculative claims",
        "follow company style guide",
        "unspecified",
    ),
    "success_criteria": (
        "captures key risks",
        "actionable next steps included",
        "factually grounded in inputs",
        "easy to scan quickly",
        "unspecified",
    ),
    "tone_style": (
        "neutral and professional",
        "concise and direct",
        "friendly and approachable",
        "formal and board-ready",
        "unspecified",
    ),
    "verbosity": (
        "very concise (under 200 words)",
        "moderate detail",
        "comprehensive and thorough",
        "adjustable by user request",
        "unspecified",
    ),
    "forbidden_content_actions": (
        "no legal advice",
        "no invented metrics",
        "no personal data",
        "no unsafe instructions",
        "unspecified",
    ),
    "edge_cases": (
        "missing or incomplete inputs",
        "conflicting source material",
        "ambiguous user intent",
        "out-of-scope requests",
        "unspecified",
    ),
    "input_materials": (
        "user-provided notes",
        "uploaded documents",
        "meeting transcripts",
        "ticket or issue text",
        "unspecified",
    ),
    "example_outputs": (
        "one short sample paragraph",
        "bulleted example with headings",
        "JSON schema example",
        "no examples needed",
        "unspecified",
    ),
    "language": (
        "english",
        "spanish",
        "french",
        "german",
        "unspecified",
    ),
    "optimization_targets": (
        "richness and detail",
        "density and brevity",
        "efficiency and speed",
        "denoising and clarity",
        "unspecified",
    ),
}

UNSPECIFIED_ANSWERS = frozenset({"unspecified", "skip", "unknown", "not sure", "n/a"})


def clarification_field_priority(card: RequirementCard) -> tuple[str, ...]:
    """Field order for clarification; domain-specific overrides when detected."""
    objective = card.objective.lower()
    if "implementation report" in objective:
        return IMPLEMENTATION_REPORT_FIELD_PRIORITY
    return CLARIFICATION_FIELD_PRIORITY


class ClarificationQuestion(BaseModel):
    field_name: str
    question_number: int = Field(ge=1, description="Current quick question index.")
    total_questions: int = Field(default=MAX_CLARIFICATION_QUESTIONS, ge=1)
    prompt: str = Field(description="Focused question without numbering prefix.")
    quick_reply_options: list[str] = Field(
        min_length=4,
        description="Quick-reply choices including a final unspecified option.",
    )
    question: str = Field(description="Full formatted question shown to the user.")
    rank: int = Field(ge=1, description="Expected clarification value rank for this field.")
    allows_free_text: bool = Field(
        default=True,
        description="User may answer in their own words instead of choosing a quick reply.",
    )

    @field_validator("quick_reply_options")
    @classmethod
    def validate_quick_replies(cls, options: list[str]) -> list[str]:
        if len(options) < 4 or len(options) > 6:
            msg = "Quick reply options must include 3 to 5 choices plus unspecified."
            raise ValueError(msg)
        if options[-1].strip().lower() != "unspecified":
            msg = "Quick reply options must end with unspecified."
            raise ValueError(msg)
        return options


class ClarificationQuestionRanker:
    """Ranks missing requirement-card fields and builds one quick question at a time."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm

    def missing_fields(self, card: RequirementCard) -> list[str]:
        priority = clarification_field_priority(card)
        missing = [field for field in priority if self._is_missing(card, field)]
        card.mark_unresolved(*missing)
        return missing

    def rank(self, card: RequirementCard) -> list[ClarificationQuestion]:
        ordered_fields = self.missing_fields(card)
        return [
            self.build_question(
                field_name,
                question_number=index,
                total_questions=MAX_CLARIFICATION_QUESTIONS,
                card=card,
            )
            for index, field_name in enumerate(ordered_fields, start=1)
        ]

    def top_question(
        self,
        card: RequirementCard,
        *,
        question_number: int,
        total_questions: int = MAX_CLARIFICATION_QUESTIONS,
        exclude: frozenset[str] = frozenset(),
        last_answer: str | None = None,
    ) -> ClarificationQuestion | None:
        ranked = [question for question in self.rank(card) if question.field_name not in exclude]
        if ranked:
            field_name = ranked[0].field_name
            return self.build_question(
                field_name,
                question_number=question_number,
                total_questions=total_questions,
                rank=ranked[0].rank,
                card=card,
                last_answer=last_answer,
            )

        for index, field_name in enumerate(REFINEMENT_FIELD_PRIORITY, start=1):
            if field_name in exclude:
                continue
            return self.build_question(
                field_name,
                question_number=question_number,
                total_questions=total_questions,
                rank=index,
                card=card,
                last_answer=last_answer,
            )
        return None

    def build_question(
        self,
        field_name: str,
        *,
        question_number: int,
        total_questions: int = MAX_CLARIFICATION_QUESTIONS,
        rank: int | None = None,
        card: RequirementCard | None = None,
        last_answer: str | None = None,
    ) -> ClarificationQuestion:
        prompt = FOCUSED_PROMPTS[field_name]
        quick_reply_options = list(QUICK_REPLY_OPTIONS[field_name])
        question = format_clarification_question(
            question_number=question_number,
            total_questions=total_questions,
            prompt=prompt,
            quick_reply_options=quick_reply_options,
        )
        return ClarificationQuestion(
            field_name=field_name,
            question_number=question_number,
            total_questions=total_questions,
            prompt=prompt,
            quick_reply_options=quick_reply_options,
            question=question,
            rank=rank or question_number,
        )

    def _is_missing(self, card: RequirementCard, field_name: str) -> bool:
        if field_name not in REQUIREMENT_CARD_FIELD_NAMES:
            return False
        if field_name in card.unresolved_fields:
            return True
        if field_name == "optimization_targets":
            targets = card.optimization_targets.model_dump()
            return all(value is None for value in targets.values())
        value = getattr(card, field_name)
        if isinstance(value, str):
            if field_name == "language":
                return not value.strip()
            return not value.strip()
        if isinstance(value, list):
            return len(value) == 0
        return False


def format_clarification_question(
    *,
    question_number: int,
    total_questions: int,
    prompt: str,
    quick_reply_options: list[str],
) -> str:
    header = f"Quick question {question_number} of {total_questions}: {prompt}"
    choices = "\n".join(f"- {option}" for option in quick_reply_options)
    body = f"{header}\nChoose one or more options and/or answer in your own words:\n{choices}"
    return textwrap.dedent(body).strip()


def is_unspecified_answer(answer: str) -> bool:
    return answer.strip().lower() in UNSPECIFIED_ANSWERS
