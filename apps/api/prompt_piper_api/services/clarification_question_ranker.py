import textwrap

from pydantic import BaseModel, Field, field_validator

from prompt_piper_api.domain.limits import MAX_CLARIFICATION_QUESTIONS
from prompt_piper_api.domain.requirement_card import LEAF_FIELD_NAMES, RequirementCard
from prompt_piper_api.llm.base import LLMClient
from prompt_piper_api.services.clarification_option_guides import (
    QuickReplyGuide,
    build_quick_reply_guides,
)
from prompt_piper_api.services.clarification_prompts import (
    FOCUSED_PROMPTS,
    ClarificationVersionText,
    build_version_texts,
)

REQUIRED_CLARIFICATION_COUNT = MAX_CLARIFICATION_QUESTIONS

CLARIFICATION_FIELD_PRIORITY: tuple[str, ...] = (
    "core_task_scope.objective",
    "core_task_scope.task_type",
    "technical_context.environment",
    "inputs_outputs_contracts.output_contract",
    "inputs_outputs_contracts.inputs",
    "architectural_rules.coding_style",
    "architectural_rules.non_functional",
    "edge_cases_error_strategy.failure_handling",
    "core_task_scope.out_of_scope",
    "technical_context.dependency_policy",
    "technical_context.integration_points",
    "architectural_rules.design_patterns",
    "edge_cases_error_strategy.bad_inputs",
    "edge_cases_error_strategy.edge_cases",
    "response_formatting.explanation_level",
    "response_formatting.verbosity",
    "response_formatting.extra_artifacts",
    "inputs_outputs_contracts.examples",
    "technical_context.forbidden_libraries",
    "optimization_targets",
)

REFINEMENT_FIELD_PRIORITY: tuple[str, ...] = (
    "inputs_outputs_contracts.output_contract",
    "architectural_rules.non_functional",
    "edge_cases_error_strategy.failure_handling",
    "response_formatting.explanation_level",
    "technical_context.integration_points",
    "inputs_outputs_contracts.examples",
    "edge_cases_error_strategy.edge_cases",
)

QUICK_REPLY_OPTIONS: dict[str, tuple[str, ...]] = {
    "core_task_scope.objective": (
        "implement a new feature",
        "refactor for performance or clarity",
        "debug a failing behavior",
        "generate a test suite",
        "unspecified",
    ),
    "core_task_scope.task_type": (
        "new feature logic",
        "refactor legacy code",
        "debugging an issue",
        "generating tests",
        "unspecified",
    ),
    "core_task_scope.out_of_scope": (
        "no unrelated refactors",
        "no dependency upgrades",
        "no UI or docs changes",
        "no speculative features",
        "unspecified",
    ),
    "technical_context.environment": (
        "Python 3.12 with FastAPI and Pydantic v2",
        "TypeScript with React and Vite",
        "Go with standard library only",
        "match the existing repo stack",
        "unspecified",
    ),
    "technical_context.integration_points": (
        "existing service and route names",
        "shared types and schemas",
        "database models and migrations",
        "no specific symbols required",
        "unspecified",
    ),
    "technical_context.dependency_policy": (
        "standard library only",
        "allow already-used packages",
        "may add well-known packages",
        "prefer existing project deps",
        "unspecified",
    ),
    "technical_context.forbidden_libraries": (
        "no new heavy frameworks",
        "no deprecated packages",
        "no GPL-only dependencies",
        "none forbidden",
        "unspecified",
    ),
    "inputs_outputs_contracts.inputs": (
        "function parameters from the call site",
        "HTTP request JSON body",
        "CLI args and stdin",
        "existing typed objects",
        "unspecified",
    ),
    "inputs_outputs_contracts.output_contract": (
        "typed function return value",
        "JSON schema object",
        "raw SQL query string",
        "TypeScript interface plus implementation",
        "unspecified",
    ),
    "inputs_outputs_contracts.examples": (
        "one happy-path example",
        "request and response pair",
        "JSON schema example",
        "no examples needed",
        "unspecified",
    ),
    "architectural_rules.design_patterns": (
        "repository pattern",
        "functional pure helpers",
        "async/await throughout",
        "object-oriented services",
        "unspecified",
    ),
    "architectural_rules.coding_style": (
        "match existing project style",
        "prefer small pure functions",
        "explicit types and validation",
        "idiomatic for the language",
        "unspecified",
    ),
    "architectural_rules.non_functional": (
        "O(n) time or better",
        "sanitize inputs against injection",
        "thread-safe shared state",
        "fail fast on invalid input",
        "unspecified",
    ),
    "edge_cases_error_strategy.failure_handling": (
        "raise custom exceptions",
        "return None or null",
        "log a warning and continue",
        "retry with backoff",
        "unspecified",
    ),
    "edge_cases_error_strategy.bad_inputs": (
        "null or missing fields",
        "empty lists or strings",
        "rate-limit responses",
        "unexpected data types",
        "unspecified",
    ),
    "edge_cases_error_strategy.edge_cases": (
        "empty input collection",
        "partial failure mid-batch",
        "duplicate keys or ids",
        "timeouts and cancellations",
        "unspecified",
    ),
    "response_formatting.explanation_level": (
        "code only with inline comments",
        "brief rationale then code",
        "step-by-step breakdown before code",
        "code plus test coverage appended",
        "unspecified",
    ),
    "response_formatting.verbosity": (
        "very concise",
        "moderate detail",
        "comprehensive and thorough",
        "adjustable by follow-up",
        "unspecified",
    ),
    "response_formatting.extra_artifacts": (
        "unit tests",
        "usage example",
        "migration notes",
        "no extra artifacts",
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
    """Field order for clarification (coding dimensions)."""
    del card  # Priority is fixed for the coding workbench.
    return CLARIFICATION_FIELD_PRIORITY


class ClarificationQuestion(BaseModel):
    field_name: str
    question_number: int = Field(ge=1, description="Current quick question index.")
    total_questions: int = Field(default=MAX_CLARIFICATION_QUESTIONS, ge=1)
    prompt: str = Field(description="Standard focused question without numbering prefix.")
    versions: list[ClarificationVersionText] = Field(
        default_factory=list,
        description="Beginner, standard, and advanced wording for this field.",
    )
    quick_reply_options: list[str] = Field(
        min_length=4,
        description="Quick-reply choices including a final unspecified option.",
    )
    quick_reply_guides: list[QuickReplyGuide] = Field(
        default_factory=list,
        description="Beginner explanations for each default quick-reply option.",
    )
    question: str = Field(description="Full formatted standard question (legacy display).")
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
    """Ranks missing coding-dimension leaves and builds one quick question at a time."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm

    def missing_fields(self, card: RequirementCard) -> list[str]:
        priority = clarification_field_priority(card)
        missing = [field for field in priority if card.is_leaf_missing(field)]
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
        del card, last_answer
        prompt = FOCUSED_PROMPTS[field_name]
        versions = build_version_texts(field_name)
        quick_reply_options = list(QUICK_REPLY_OPTIONS[field_name])
        quick_reply_guides = build_quick_reply_guides(field_name)
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
            versions=versions,
            quick_reply_options=quick_reply_options,
            quick_reply_guides=quick_reply_guides,
            question=question,
            rank=rank or question_number,
        )

    def _is_missing(self, card: RequirementCard, field_name: str) -> bool:
        if field_name not in LEAF_FIELD_NAMES:
            return False
        return card.is_leaf_missing(field_name)


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
