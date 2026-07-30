"""Beginner-friendly guides for clarification quick-reply options."""

from __future__ import annotations

from pydantic import BaseModel, Field


class QuickReplyGuide(BaseModel):
    """Plain-language guide for one default quick-reply option."""

    option: str
    explanation: str = Field(description="What this option means in everyday language.")
    when_to_use: str = Field(description="When this option is usually the best fit.")


# Maps field_name -> option label -> (explanation, when_to_use)
_BEGINNER_OPTION_TEXT: dict[str, dict[str, tuple[str, str]]] = {
    "core_task_scope.objective": {
        "implement a new feature": (
            "Ask the AI to add something that does not exist yet.",
            "Use when you want new behavior, a new endpoint, or a new screen.",
        ),
        "refactor for performance or clarity": (
            "Keep the same behavior, but clean up or speed up the code.",
            "Use when the code works but is slow, messy, or hard to maintain.",
        ),
        "debug a failing behavior": (
            "Find and fix something that is broken or wrong.",
            "Use when you have a bug, failing test, or unexpected result.",
        ),
        "generate a test suite": (
            "Focus on writing tests that prove the code behaves correctly.",
            "Use when your main goal is coverage, regression safety, or QA.",
        ),
        "unspecified": (
            "Skip this choice for now and leave the goal open.",
            "Use when you are unsure, or you will describe the goal in custom text.",
        ),
    },
    "core_task_scope.task_type": {
        "new feature logic": (
            "The job is mostly writing new application logic.",
            "Use for greenfield features or net-new business rules.",
        ),
        "refactor legacy code": (
            "The job is reshaping older code without changing what it does.",
            "Use when cleaning up legacy modules or simplifying structure.",
        ),
        "debugging an issue": (
            "The job is diagnosing and repairing a defect.",
            "Use for crashes, wrong outputs, or flaky behavior.",
        ),
        "generating tests": (
            "The job is producing automated tests.",
            "Use when you need unit, integration, or regression tests.",
        ),
        "unspecified": (
            "Leave the task type undecided for now.",
            "Use when more than one type applies, or you will clarify in free text.",
        ),
    },
    "core_task_scope.out_of_scope": {
        "no unrelated refactors": (
            "Do not rewrite nearby code that is not part of the request.",
            "Use when you want a focused change and fear drive-by cleanups.",
        ),
        "no dependency upgrades": (
            "Do not bump package versions as part of this work.",
            "Use when upgrades need a separate review or release process.",
        ),
        "no UI or docs changes": (
            "Stay in backend/logic; skip screens and documentation edits.",
            "Use when the ticket is API- or library-only.",
        ),
        "no speculative features": (
            "Do not invent extras that were not asked for.",
            "Use when you want the smallest complete solution.",
        ),
        "unspecified": (
            "No special out-of-scope rules yet.",
            "Use when boundaries are still unclear.",
        ),
    },
    "technical_context.environment": {
        "Python 3.12 with FastAPI and Pydantic v2": (
            "Target a modern Python web API stack.",
            "Use when that is your real project stack or a close match.",
        ),
        "TypeScript with React and Vite": (
            "Target a TypeScript frontend built with React and Vite.",
            "Use for UI components, hooks, or client-side app work.",
        ),
        "Go with standard library only": (
            "Write Go using only the standard library.",
            "Use for lightweight Go services without third-party frameworks.",
        ),
        "match the existing repo stack": (
            "Follow whatever languages and frameworks the repo already uses.",
            "Use when the AI should inspect or mirror current project conventions.",
        ),
        "unspecified": (
            "Stack details are not locked in yet.",
            "Use when you will name the stack in custom text or later.",
        ),
    },
    "technical_context.integration_points": {
        "existing service and route names": (
            "New code must plug into current services and HTTP routes.",
            "Use when renaming or inventing new endpoints would break callers.",
        ),
        "shared types and schemas": (
            "Reuse shared TypeScript/Pydantic/types already in the project.",
            "Use when type consistency across modules matters most.",
        ),
        "database models and migrations": (
            "Fit existing ORM models and migration patterns.",
            "Use when touching persistence or schema-related code.",
        ),
        "no specific symbols required": (
            "No hard requirement to match particular names or types.",
            "Use for standalone snippets or greenfield helpers.",
        ),
        "unspecified": (
            "Integration targets are still open.",
            "Use when you are not sure what must be matched.",
        ),
    },
    "technical_context.dependency_policy": {
        "standard library only": (
            "Only built-in language libraries are allowed.",
            "Use for constrained environments or minimal footprints.",
        ),
        "allow already-used packages": (
            "You may use packages the project already depends on.",
            "Use when adding deps is restricted but existing ones are fine.",
        ),
        "may add well-known packages": (
            "Common, trusted packages may be introduced if needed.",
            "Use when a small, well-known library clearly improves the solution.",
        ),
        "prefer existing project deps": (
            "Reach for current dependencies first before adding anything new.",
            "Use as a soft preference rather than a hard ban.",
        ),
        "unspecified": (
            "No package policy chosen yet.",
            "Use when you will describe the policy in free text.",
        ),
    },
    "technical_context.forbidden_libraries": {
        "no new heavy frameworks": (
            "Do not pull in large frameworks for a small task.",
            "Use when you want to avoid bloating the project.",
        ),
        "no deprecated packages": (
            "Avoid libraries that are outdated or unmaintained.",
            "Use when security or supportability is a concern.",
        ),
        "no GPL-only dependencies": (
            "Do not introduce GPL-licensed packages.",
            "Use when licensing policy forbids copyleft dependencies.",
        ),
        "none forbidden": (
            "There is no banned-library list for this prompt.",
            "Use when package choice is flexible.",
        ),
        "unspecified": (
            "Forbidden libraries are not listed yet.",
            "Use when you still need to check policy.",
        ),
    },
    "inputs_outputs_contracts.inputs": {
        "function parameters from the call site": (
            "The code receives normal function arguments from callers.",
            "Use for helpers, services, and library functions.",
        ),
        "HTTP request JSON body": (
            "Input arrives as JSON in an HTTP request.",
            "Use for API handlers and webhooks.",
        ),
        "CLI args and stdin": (
            "Input comes from command-line flags/args or standard input.",
            "Use for scripts and developer tooling.",
        ),
        "existing typed objects": (
            "Input is already-shaped domain objects or DTOs.",
            "Use when you are extending an existing typed pipeline.",
        ),
        "unspecified": (
            "Input shape is still undecided.",
            "Use when you will paste a sample later.",
        ),
    },
    "inputs_outputs_contracts.output_contract": {
        "typed function return value": (
            "Return a clearly typed value from a function.",
            "Use for internal APIs and library methods.",
        ),
        "JSON schema object": (
            "Return a JSON object that follows a known schema.",
            "Use for REST responses and structured payloads.",
        ),
        "raw SQL query string": (
            "The main deliverable is a SQL string.",
            "Use when generating queries rather than application code.",
        ),
        "TypeScript interface plus implementation": (
            "Provide both the TypeScript type and working code.",
            "Use when consumers need a contract and an implementation.",
        ),
        "unspecified": (
            "Exact return shape is still open.",
            "Use when you will describe the contract in custom text.",
        ),
    },
    "inputs_outputs_contracts.examples": {
        "one happy-path example": (
            "Include one normal successful example.",
            "Use when a single clear demo is enough guidance.",
        ),
        "request and response pair": (
            "Show matching input and output side by side.",
            "Use for APIs where format mistakes are common.",
        ),
        "JSON schema example": (
            "Show an example that matches a JSON schema.",
            "Use when schema compliance is the hard part.",
        ),
        "no examples needed": (
            "Skip examples; prose and contracts are enough.",
            "Use when the task is simple or examples would distract.",
        ),
        "unspecified": (
            "Example needs are undecided.",
            "Use when you may attach samples later.",
        ),
    },
    "architectural_rules.design_patterns": {
        "repository pattern": (
            "Separate data access behind repository-style interfaces.",
            "Use when you want clean persistence boundaries.",
        ),
        "functional pure helpers": (
            "Prefer small functions without side effects where possible.",
            "Use for transforms, validators, and easy-to-test logic.",
        ),
        "async/await throughout": (
            "Use asynchronous style consistently for I/O.",
            "Use for network, database, or concurrent workloads.",
        ),
        "object-oriented services": (
            "Organize behavior into classes/services with clear roles.",
            "Use when the codebase is already OOP-oriented.",
        ),
        "unspecified": (
            "No design pattern preference yet.",
            "Use when any clean approach is acceptable.",
        ),
    },
    "architectural_rules.coding_style": {
        "match existing project style": (
            "Copy naming, formatting, and structure already in the repo.",
            "Use for patches that should look native to the project.",
        ),
        "prefer small pure functions": (
            "Keep units small and easy to test.",
            "Use when readability and unit testing matter most.",
        ),
        "explicit types and validation": (
            "Spell out types and validate inputs early.",
            "Use for APIs and safety-critical paths.",
        ),
        "idiomatic for the language": (
            "Follow common best practices for that language.",
            "Use when there is no stronger local convention.",
        ),
        "unspecified": (
            "Style guidance is still open.",
            "Use when you will point to a style guide later.",
        ),
    },
    "architectural_rules.non_functional": {
        "O(n) time or better": (
            "Keep algorithms roughly linear in input size.",
            "Use for large lists or hot paths where speed matters.",
        ),
        "sanitize inputs against injection": (
            "Treat user input as untrusted and sanitize/escape it.",
            "Use for SQL, HTML, shell, or other injection risks.",
        ),
        "thread-safe shared state": (
            "Shared data must be safe under concurrent access.",
            "Use for multi-threaded or async shared caches.",
        ),
        "fail fast on invalid input": (
            "Reject bad input early with a clear error.",
            "Use when silent bad data would be worse than an error.",
        ),
        "unspecified": (
            "No special non-functional rule selected.",
            "Use when performance/security needs are still vague.",
        ),
    },
    "edge_cases_error_strategy.failure_handling": {
        "raise custom exceptions": (
            "Signal failures with clear, intentional exceptions.",
            "Use when callers should catch and handle errors.",
        ),
        "return None or null": (
            "Use an empty/null result instead of throwing.",
            "Use for optional lookups where absence is normal.",
        ),
        "log a warning and continue": (
            "Record the problem but keep going if safe.",
            "Use for non-critical failures in batch jobs.",
        ),
        "retry with backoff": (
            "Try again with waiting between attempts.",
            "Use for flaky networks or temporary outages.",
        ),
        "unspecified": (
            "Failure strategy is not chosen yet.",
            "Use when you will describe error policy in free text.",
        ),
    },
    "edge_cases_error_strategy.bad_inputs": {
        "null or missing fields": (
            "Expect nulls and absent keys.",
            "Use for messy JSON or optional form fields.",
        ),
        "empty lists or strings": (
            "Expect empty collections and blank strings.",
            "Use for filters, searches, and optional multi-selects.",
        ),
        "rate-limit responses": (
            "Expect 429s or throttling from upstream services.",
            "Use when calling external APIs under load.",
        ),
        "unexpected data types": (
            "Expect wrong types (string instead of number, etc.).",
            "Use for loosely typed inputs or user-edited JSON.",
        ),
        "unspecified": (
            "Bad-input cases are not listed yet.",
            "Use when you still need to think through failure modes.",
        ),
    },
    "edge_cases_error_strategy.edge_cases": {
        "empty input collection": (
            "Handle the case where the main list/set is empty.",
            "Use for batch processors and map/filter pipelines.",
        ),
        "partial failure mid-batch": (
            "Some items succeed while others fail in one run.",
            "Use for imports, sync jobs, and multi-record APIs.",
        ),
        "duplicate keys or ids": (
            "The same key/id may appear more than once.",
            "Use for merges, upserts, and de-duplication logic.",
        ),
        "timeouts and cancellations": (
            "Operations may be canceled or run out of time.",
            "Use for long requests and user-abortable work.",
        ),
        "unspecified": (
            "Edge cases are still open.",
            "Use when you will add specifics in custom text.",
        ),
    },
    "response_formatting.explanation_level": {
        "code only with inline comments": (
            "Mostly code, with short comments inside it.",
            "Use when you want something ready to paste with minimal reading.",
        ),
        "brief rationale then code": (
            "A short why, then the code.",
            "Use when you want light context without a long essay.",
        ),
        "step-by-step breakdown before code": (
            "Explain the plan in steps, then show the code.",
            "Use when learning or reviewing design choices matters.",
        ),
        "code plus test coverage appended": (
            "Deliver code and also attach tests.",
            "Use when verification belongs in the same answer.",
        ),
        "unspecified": (
            "Explanation depth is undecided.",
            "Use when either style is fine.",
        ),
    },
    "response_formatting.verbosity": {
        "very concise": (
            "Keep the answer short and scannable.",
            "Use when you already know the domain well.",
        ),
        "moderate detail": (
            "Balanced length: enough detail without fluff.",
            "Use for most day-to-day coding prompts.",
        ),
        "comprehensive and thorough": (
            "Cover edge cases and alternatives more fully.",
            "Use for complex or high-risk changes.",
        ),
        "adjustable by follow-up": (
            "Start moderate; you can ask for more or less later.",
            "Use when you are exploring and not sure yet.",
        ),
        "unspecified": (
            "No verbosity preference yet.",
            "Use when length does not matter much.",
        ),
    },
    "response_formatting.extra_artifacts": {
        "unit tests": (
            "Also include automated unit tests.",
            "Use when you want verification alongside the solution.",
        ),
        "usage example": (
            "Also include a short how-to-use example.",
            "Use when callers need a quick integration sample.",
        ),
        "migration notes": (
            "Also include notes about upgrading or migrating.",
            "Use when the change affects existing data or APIs.",
        ),
        "no extra artifacts": (
            "Do not append tests, samples, or notes.",
            "Use when you only want the core deliverable.",
        ),
        "unspecified": (
            "Extras are undecided.",
            "Use when you may ask for them in a follow-up.",
        ),
    },
    "optimization_targets": {
        "richness and detail": (
            "Prefer a fuller, more descriptive prompt.",
            "Use early when you need thorough requirements captured.",
        ),
        "density and brevity": (
            "Prefer a shorter, packed prompt.",
            "Use when token cost or prompt length is a concern.",
        ),
        "efficiency and speed": (
            "Optimize for fast generation and lean instructions.",
            "Use when turnaround time matters more than nuance.",
        ),
        "denoising and clarity": (
            "Remove fluff and keep language clear.",
            "Use when drafts feel noisy or contradictory.",
        ),
        "unspecified": (
            "No optimization priority chosen.",
            "Use when default balancing is fine.",
        ),
    },
}


def build_quick_reply_guides(field_name: str) -> list[QuickReplyGuide]:
    """Build beginner guides aligned to the field's quick-reply options."""
    from prompt_piper_api.services.clarification_question_ranker import QUICK_REPLY_OPTIONS

    options = QUICK_REPLY_OPTIONS.get(field_name, ())
    text_by_option = _BEGINNER_OPTION_TEXT.get(field_name, {})
    guides: list[QuickReplyGuide] = []
    for option in options:
        pair = text_by_option.get(option)
        if pair is None:
            guides.append(
                QuickReplyGuide(
                    option=option,
                    explanation=f"Choose “{option}” when it matches your situation.",
                    when_to_use="Use when this label is the closest fit, or skip with unspecified.",
                )
            )
            continue
        explanation, when_to_use = pair
        guides.append(
            QuickReplyGuide(
                option=option,
                explanation=explanation,
                when_to_use=when_to_use,
            )
        )
    return guides


def assert_guides_cover_all_options() -> None:
    """Dev helper: every quick-reply option should have beginner text."""
    from prompt_piper_api.services.clarification_question_ranker import QUICK_REPLY_OPTIONS

    missing: list[str] = []
    for field_name, options in QUICK_REPLY_OPTIONS.items():
        text = _BEGINNER_OPTION_TEXT.get(field_name, {})
        for option in options:
            if option not in text:
                missing.append(f"{field_name}:{option}")
    if missing:
        raise AssertionError(f"Missing beginner option guides: {missing}")
