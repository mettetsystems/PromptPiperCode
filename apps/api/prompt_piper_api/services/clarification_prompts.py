"""Clarification question wording at beginner, standard, and advanced levels."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ClarificationLevel(StrEnum):
    BEGINNER = "beginner"
    STANDARD = "standard"
    ADVANCED = "advanced"


LEVEL_LABELS: dict[ClarificationLevel, str] = {
    ClarificationLevel.BEGINNER: "Beginner",
    ClarificationLevel.STANDARD: "Standard",
    ClarificationLevel.ADVANCED: "Advanced",
}


class ClarificationVersionText(BaseModel):
    """One wording of a clarification question."""

    level: ClarificationLevel
    label: str
    prompt: str = Field(description="The question to ask the user.")
    rationale: str | None = Field(
        default=None,
        description="Why this question matters (emphasized for beginner).",
    )


# Current product wording — people with some development skill.
STANDARD_PROMPTS: dict[str, str] = {
    "core_task_scope.objective": "What single coding job should this prompt accomplish?",
    "core_task_scope.task_type": (
        "Is this writing a feature, refactoring, debugging, or generating tests?"
    ),
    "core_task_scope.out_of_scope": (
        "What should the model explicitly not try to solve or include?"
    ),
    "technical_context.environment": (
        "What is the precise stack (language version, framework, key dependencies)?"
    ),
    "technical_context.integration_points": (
        "What existing functions, types, schemas, or names must the output match?"
    ),
    "technical_context.dependency_policy": (
        "Stdlib only, allow listed third-party packages, or open package use?"
    ),
    "technical_context.forbidden_libraries": "Which libraries or packages are forbidden?",
    "inputs_outputs_contracts.inputs": (
        "What do the inputs look like (params, payloads, or sample structures)?"
    ),
    "inputs_outputs_contracts.output_contract": (
        "What exact return structure is required (JSON schema, SQL, interface, object)?"
    ),
    "inputs_outputs_contracts.examples": (
        "What example inputs or outputs should guide the model?"
    ),
    "architectural_rules.design_patterns": (
        "Which design patterns should it follow (OOP, FP, repository, async/await)?"
    ),
    "architectural_rules.coding_style": (
        "What coding style or design approach should it follow?"
    ),
    "architectural_rules.non_functional": (
        "Any memory, complexity, thread-safety, or security requirements?"
    ),
    "edge_cases_error_strategy.failure_handling": (
        "How should failures be handled (exceptions, null, log, retry)?"
    ),
    "edge_cases_error_strategy.bad_inputs": (
        "What bad inputs will it face (null, empty lists, rate limits, wrong types)?"
    ),
    "edge_cases_error_strategy.edge_cases": (
        "What edge cases or exceptions must be handled?"
    ),
    "response_formatting.explanation_level": (
        "Code only, brief rationale, or step-by-step breakdown before the code?"
    ),
    "response_formatting.verbosity": "How long or detailed should the response be?",
    "response_formatting.extra_artifacts": (
        "Should tests, comments, or other artifacts be appended?"
    ),
    "optimization_targets": "Which optimization goals matter most right now?",
}

# 10th-grade / layman wording with why-it-matters rationales.
BEGINNER_PROMPTS: dict[str, tuple[str, str]] = {
    "core_task_scope.objective": (
        "In plain words, what one job should the AI help you write code for?",
        "A clear goal keeps the AI from guessing. Without it, the answer can wander "
        "into unrelated work and waste time.",
    ),
    "core_task_scope.task_type": (
        "Are you asking for a new feature, a cleanup of old code, a bug fix, or tests?",
        "Different jobs need different instructions. Naming the type helps the AI "
        "pick the right approach from the start.",
    ),
    "core_task_scope.out_of_scope": (
        "What should the AI leave alone or not try to solve?",
        "Saying what is out of bounds stops surprise changes—like rewriting files "
        "you did not ask to touch.",
    ),
    "technical_context.environment": (
        "What tools and versions are you using (for example Python 3.12 with FastAPI)?",
        "Code that fits your real tools works when you paste it. Vague stacks lead "
        "to examples that will not run in your project.",
    ),
    "technical_context.integration_points": (
        "Are there existing function names, types, or APIs the new code must match?",
        "Matching names and shapes lets the new code plug into what you already have "
        "instead of inventing a parallel design.",
    ),
    "technical_context.dependency_policy": (
        "Can the AI only use built-in libraries, your current packages, or add new ones?",
        "Package rules protect your project from surprise installs and license issues.",
    ),
    "technical_context.forbidden_libraries": (
        "Are there any libraries the AI must not use?",
        "Forbidden lists keep deprecated or heavy tools out of the generated code.",
    ),
    "inputs_outputs_contracts.inputs": (
        "What does the code receive as input (form fields, JSON, function arguments)?",
        "Clear inputs prevent the AI from inventing data shapes that do not match "
        "your real calls.",
    ),
    "inputs_outputs_contracts.output_contract": (
        "What exact result should the code return (JSON fields, a type, a query string)?",
        "An exact return shape is how you know the answer is usable—and how other "
        "code can rely on it.",
    ),
    "inputs_outputs_contracts.examples": (
        "Do you have a small example of good input and output to show the AI?",
        "Examples teach by demo. They cut down on wrong formats more than long prose.",
    ),
    "architectural_rules.design_patterns": (
        "Should the code follow a particular style of design (classes, small functions, async)?",
        "Design patterns keep new code consistent with how your team already builds things.",
    ),
    "architectural_rules.coding_style": (
        "How should the code look and feel compared with the rest of your project?",
        "Style guidance makes review easier and avoids a patch that looks foreign.",
    ),
    "architectural_rules.non_functional": (
        "Any rules about speed, safety, memory, or security (for example sanitize inputs)?",
        "These rules catch problems that “it works on the happy path” still misses.",
    ),
    "edge_cases_error_strategy.failure_handling": (
        "When something goes wrong, should the code raise an error, return empty, log, or retry?",
        "Failure plans decide how your app behaves under stress—silent bugs vs clear errors.",
    ),
    "edge_cases_error_strategy.bad_inputs": (
        "What messy or missing data might show up (empty lists, nulls, wrong types)?",
        "Naming bad inputs up front makes the AI write guards instead of assuming perfect data.",
    ),
    "edge_cases_error_strategy.edge_cases": (
        "What unusual situations should still be handled correctly?",
        "Edge cases are where production bugs hide. Listing them improves reliability.",
    ),
    "response_formatting.explanation_level": (
        "Do you want only code, a short why, or a step-by-step before the code?",
        "Explanation level controls how much reading you do versus how fast you can copy code.",
    ),
    "response_formatting.verbosity": (
        "Should the answer be short, medium, or very detailed?",
        "Length limits keep answers scannable and reduce filler that hides the real code.",
    ),
    "response_formatting.extra_artifacts": (
        "Should the AI also add tests, usage notes, or other extras at the end?",
        "Extras save a follow-up turn when you already know you need tests or examples.",
    ),
    "optimization_targets": (
        "Should this prompt favor detail, brevity, speed, clarity, or resolving conflicts?",
        "Optimization goals tell later steps what to keep when shortening the prompt.",
    ),
}

# Compact, thorough wording for experienced developers.
ADVANCED_PROMPTS: dict[str, str] = {
    "core_task_scope.objective": (
        "State the single coding objective and the observable success condition."
    ),
    "core_task_scope.task_type": (
        "Classify the job: feature implementation, refactor, defect isolation, or test generation."
    ),
    "core_task_scope.out_of_scope": (
        "Enumerate explicit non-goals (refactors, deps, UI, speculative features) the model must not pursue."
    ),
    "technical_context.environment": (
        "Pin language/runtime, frameworks, and key dependency versions the solution must target."
    ),
    "technical_context.integration_points": (
        "List symbols, types, schemas, routes, or persistence models the output must bind to."
    ),
    "technical_context.dependency_policy": (
        "Constrain package use: stdlib-only, existing lockfile deps, or allowlisted additions."
    ),
    "technical_context.forbidden_libraries": (
        "Name banned packages/frameworks and any licensing constraints."
    ),
    "inputs_outputs_contracts.inputs": (
        "Specify input surface: signatures, request schemas, CLI/stdin, or typed call-site objects."
    ),
    "inputs_outputs_contracts.output_contract": (
        "Define the exact return contract (schema, interface, SQL, status codes, error envelope)."
    ),
    "inputs_outputs_contracts.examples": (
        "Provide canonical I/O exemplars or schema fixtures the model must mirror."
    ),
    "architectural_rules.design_patterns": (
        "Mandate patterns (repository, pure FP, OOP services, async boundaries) and layering rules."
    ),
    "architectural_rules.coding_style": (
        "State style invariants: project conventions, typing/validation strictness, idioms."
    ),
    "architectural_rules.non_functional": (
        "Capture NFRs: complexity bounds, injection/sanitization, concurrency, fail-fast policy."
    ),
    "edge_cases_error_strategy.failure_handling": (
        "Choose failure semantics: typed exceptions, nullish returns, structured logs, retries/backoff."
    ),
    "edge_cases_error_strategy.bad_inputs": (
        "Catalog adversarial/malformed inputs (nulls, empties, rate limits, type drift)."
    ),
    "edge_cases_error_strategy.edge_cases": (
        "List residual edge cases (empty collections, partial batch failure, dup keys, cancel/timeout)."
    ),
    "response_formatting.explanation_level": (
        "Set response mode: code-only, brief rationale+code, or sequenced plan then code (+tests)."
    ),
    "response_formatting.verbosity": (
        "Bound response length/detail (concise, moderate, exhaustive, follow-up adjustable)."
    ),
    "response_formatting.extra_artifacts": (
        "Require appended artifacts: unit tests, usage sample, migration notes—or none."
    ),
    "optimization_targets": (
        "Prioritize optimization axes: richness, density, efficiency, denoising, deconfliction."
    ),
}

# Back-compat alias used by suggestion service and older imports.
FOCUSED_PROMPTS = STANDARD_PROMPTS


def build_version_texts(field_name: str) -> list[ClarificationVersionText]:
    """Return beginner, standard, and advanced wording for a field."""
    standard = STANDARD_PROMPTS[field_name]
    beginner_prompt, beginner_rationale = BEGINNER_PROMPTS[field_name]
    advanced = ADVANCED_PROMPTS[field_name]
    return [
        ClarificationVersionText(
            level=ClarificationLevel.BEGINNER,
            label=LEVEL_LABELS[ClarificationLevel.BEGINNER],
            prompt=beginner_prompt,
            rationale=beginner_rationale,
        ),
        ClarificationVersionText(
            level=ClarificationLevel.STANDARD,
            label=LEVEL_LABELS[ClarificationLevel.STANDARD],
            prompt=standard,
            rationale=None,
        ),
        ClarificationVersionText(
            level=ClarificationLevel.ADVANCED,
            label=LEVEL_LABELS[ClarificationLevel.ADVANCED],
            prompt=advanced,
            rationale=None,
        ),
    ]
