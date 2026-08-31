"""Long-horizon coding-agent control schema: 16 questions, defaults, and expansions."""

from __future__ import annotations

from dataclasses import dataclass

UNSPECIFIED_LABEL = "unspecified"


@dataclass(frozen=True)
class ContractOption:
    """One quick-reply choice. `label` is shown in the UI; `body` is stored on the card."""

    label: str
    body: str
    explanation: str
    when_to_use: str


@dataclass(frozen=True)
class ContractQuestion:
    """One operational-control question on the agent contract."""

    field_name: str
    section_title: str
    standard_prompt: str
    beginner_prompt: str
    beginner_rationale: str
    advanced_prompt: str
    options: tuple[ContractOption, ...]


_UNSPECIFIED = ContractOption(
    label=UNSPECIFIED_LABEL,
    body="",
    explanation="Skip this choice for now and leave the policy open.",
    when_to_use="Use when you will write a custom policy, or you are not ready to decide.",
)


CONTRACT_QUESTIONS: tuple[ContractQuestion, ...] = (
    ContractQuestion(
        field_name="agent_contract.definition_of_done",
        section_title="Definition of Done",
        standard_prompt='What does "done" actually mean?',
        beginner_prompt=(
            "When should the agent treat this work as finished, only partly done, blocked, or failed?"
        ),
        beginner_rationale=(
            "Without an explicit finish line, a coding agent will often declare success after "
            "writing files. Named completion states keep the result honest."
        ),
        advanced_prompt=(
            "Specify evidence-based completion states (COMPLETE / PARTIAL / BLOCKED / FAILED) "
            "and the acceptance criteria that distinguish them."
        ),
        options=(
            ContractOption(
                label="Recommended: evidence-based COMPLETE / PARTIAL / BLOCKED / FAILED",
                body=(
                    "The task is complete only when all explicitly stated acceptance criteria are "
                    "satisfied. The implementation must compile/build successfully where applicable, "
                    "applicable tests must pass, the requested behavior must be demonstrable, and no "
                    "known regression caused by the implementation may remain unresolved. If an "
                    "acceptance criterion cannot be completed, the task must be marked PARTIAL, not "
                    "COMPLETE. Allowed completion states: COMPLETE, PARTIAL, BLOCKED, FAILED. The "
                    "agent must not redefine failure as success."
                ),
                explanation=(
                    "Done is proven with tests, a working demo, and unmet criteria marked PARTIAL."
                ),
                when_to_use="Use for almost every long-horizon coding task. This is the default.",
            ),
            ContractOption(
                label="Stricter: tests, demo, docs, and no known regressions",
                body=(
                    "COMPLETE requires passing applicable tests, a demonstrated run using documented "
                    "commands, updated relevant documentation, and zero known regressions. Anything "
                    "less is PARTIAL, BLOCKED, or FAILED. The agent must not redefine failure as success."
                ),
                explanation="Adds documentation and a documented run command on top of tests and demo.",
                when_to_use="Use when this work will be handed to someone else to operate.",
            ),
            ContractOption(
                label="Minimal: requested behavior is demonstrable",
                body=(
                    "COMPLETE when the requested behavior can be demonstrated. Tests and docs are "
                    "preferred but not required unless the task states them. Use PARTIAL when the "
                    "core behavior works but follow-up remains."
                ),
                explanation="A lower bar: showing the behavior is enough if tests were not requested.",
                when_to_use="Use only for spikes or throwaway prototypes.",
            ),
            _UNSPECIFIED,
        ),
    ),
    ContractQuestion(
        field_name="agent_contract.change_scope",
        section_title="Change Scope",
        standard_prompt="What is the agent allowed to change—and what must it not change?",
        beginner_prompt="Which files may the agent edit, and what must it leave alone?",
        beginner_rationale=(
            "Long-horizon runs drift. A minimum-necessary change policy stops unrelated rewrites."
        ),
        advanced_prompt=(
            "State a minimum-necessary change policy, allowed supporting edits, and a hard list of "
            "protected resources (secrets, public APIs, production infra)."
        ),
        options=(
            ContractOption(
                label="Recommended: minimum necessary change",
                body=(
                    "Follow a minimum-necessary change policy. The agent may modify directly related "
                    "code, create required files, create or update tests, update relevant "
                    "documentation, perform small supporting refactors, and add lightweight "
                    "dependencies when justified. It may not automatically delete user data, modify "
                    "credentials or secrets, disable security controls, remove tests simply because "
                    "they fail, rewrite unrelated subsystems, change public APIs without necessity, "
                    "perform destructive migrations, or modify production infrastructure."
                ),
                explanation="Edit what the task needs; do not wander into unrelated files or secrets.",
                when_to_use="Use as the default for almost all repository work.",
            ),
            ContractOption(
                label="Stricter: only files named in the task",
                body=(
                    "The agent may modify only files, modules, or paths explicitly named in the task "
                    "or discovered as direct compile/test dependencies of those files. Supporting "
                    "refactors, new dependencies, public API changes, migrations, and infrastructure "
                    "edits require escalation. Secrets, credentials, and production data must never "
                    "be modified."
                ),
                explanation="A tight fence: stay inside the named files unless blocked.",
                when_to_use="Use in production-critical or tightly reviewed codebases.",
            ),
            ContractOption(
                label="Broader: allow supporting refactors and docs",
                body=(
                    "The agent may modify files required by the task and may make supporting "
                    "refactors, documentation, and test updates in neighboring modules when that "
                    "keeps the change coherent. It must still minimize unrelated diffs and must never "
                    "modify secrets, credentials, production data, or security controls."
                ),
                explanation="Allows nearby cleanup when it helps the main change stay consistent.",
                when_to_use="Use when the surrounding code is already being touched anyway.",
            ),
            _UNSPECIFIED,
        ),
    ),
    ContractQuestion(
        field_name="agent_contract.architecture_policy",
        section_title="Architecture Policy",
        standard_prompt="What architectural principles must remain true?",
        beginner_prompt="How should new code fit the way this project is already built?",
        beginner_rationale=(
            "Agents invent parallel architectures. A reuse-first policy keeps the repo coherent."
        ),
        advanced_prompt=(
            "Rank preferred building blocks (existing patterns, stdlib, mature OSS, new frameworks) "
            "and the engineering priority order (correctness before performance)."
        ),
        options=(
            ContractOption(
                label="Recommended: reuse existing patterns; correctness first",
                body=(
                    "Prefer, in order: existing project patterns; existing project dependencies; "
                    "standard language/runtime capabilities; mature open-source libraries; small "
                    "custom implementations; new frameworks; external proprietary dependencies. "
                    "Engineering priorities: correctness, simplicity, modularity, maintainability, "
                    "testability, portability, observability, performance, then optimization. "
                    "Performance may move upward when the task specifically demands it. Do not "
                    "create a new abstraction until determining whether the repository already "
                    "contains one serving the same purpose."
                ),
                explanation="Match the repo first. Correctness and simplicity beat clever new stacks.",
                when_to_use="Use as the default unless the task is an architecture migration.",
            ),
            ContractOption(
                label="Stricter: stdlib and existing dependencies only",
                body=(
                    "Reuse existing project patterns and dependencies. Prefer standard library "
                    "capabilities. New third-party libraries, frameworks, and proprietary services "
                    "require escalation. Priorities: correctness, simplicity, testability, then "
                    "maintainability. Do not introduce a parallel architecture."
                ),
                explanation="No new packages unless a human approves them.",
                when_to_use="Use when dependency review is strict or the lockfile is frozen.",
            ),
            ContractOption(
                label="Portable: prefer open standards and loose coupling",
                body=(
                    "Prefer modular, loosely coupled, portable, testable, maintainable code. Reuse "
                    "existing abstractions before introducing new ones. Prefer simple solutions over "
                    "unnecessary frameworks. Preserve clear interfaces, avoid hidden dependencies, "
                    "minimize vendor lock-in, and favor open standards and open-source dependencies."
                ),
                explanation="Optimizes for moving the work between environments later.",
                when_to_use="Use when this code must stay portable across vendors or runtimes.",
            ),
            _UNSPECIFIED,
        ),
    ),
    ContractQuestion(
        field_name="agent_contract.discovery_policy",
        section_title="Discovery Policy",
        standard_prompt="What must the agent understand before coding?",
        beginner_prompt="What should the agent read in the repo before it starts changing files?",
        beginner_rationale=(
            "Coding before looking causes duplicate modules and broken integrations."
        ),
        advanced_prompt=(
            "Require inspect-before-modify: structure, docs, deps, tests, APIs, data models, then "
            "a short implementation plan. Ban new abstractions until reuse is checked."
        ),
        options=(
            ContractOption(
                label="Recommended: inspect repo, then write a short plan",
                body=(
                    "Before making substantial changes: inspect repository structure; read project "
                    "documentation; inspect dependency and configuration files; identify relevant "
                    "modules; inspect related tests; search for existing implementations; identify "
                    "external interfaces; identify relevant data models; identify architectural "
                    "constraints; then produce an implementation plan. Do not create a new "
                    "abstraction until determining whether the repository already contains one "
                    "serving the same purpose."
                ),
                explanation="Look around, reuse what exists, then plan before large edits.",
                when_to_use="Use as the default for any non-trivial coding task.",
            ),
            ContractOption(
                label="Stricter: written plan required before the first substantial edit",
                body=(
                    "Complete the full discovery checklist (structure, docs, deps, modules, tests, "
                    "existing implementations, interfaces, data models, constraints) and write the "
                    "plan into .agent/PLAN.md before the first substantial code change. Trivial "
                    "one-line fixes may proceed after locating the relevant test."
                ),
                explanation="Forces a durable plan file before the agent starts rewriting.",
                when_to_use="Use for multi-hour or multi-module work.",
            ),
            ContractOption(
                label="Lightweight: skim README, tests, and the target module",
                body=(
                    "Before coding, read the README or architecture notes, open the target module, "
                    "and inspect the most relevant tests. Search for an existing helper before "
                    "adding a new one. A short in-response plan is enough unless the change spans "
                    "multiple packages."
                ),
                explanation="A lighter look-around for small, well-scoped edits.",
                when_to_use="Use for small, well-localized changes.",
            ),
            _UNSPECIFIED,
        ),
    ),
    ContractQuestion(
        field_name="agent_contract.execution_strategy",
        section_title="Execution Strategy",
        standard_prompt="How should the agent decompose and manage the work?",
        beginner_prompt="Should the agent do the whole job at once, or in small checked-off steps?",
        beginner_rationale=(
            "Small, reversible milestones are how long-horizon runs stay recoverable."
        ),
        advanced_prompt=(
            "Mandate an incremental lifecycle (discover → plan → implement small unit → test → "
            "integrate) with independently verifiable milestones."
        ),
        options=(
            ContractOption(
                label="Recommended: small reversible milestones with a full lifecycle",
                body=(
                    "Use this lifecycle: DISCOVER → UNDERSTAND → PLAN → IMPLEMENT SMALL UNIT → "
                    "TEST → INTEGRATE → TEST → NEXT UNIT → SYSTEM VALIDATION → DOCUMENT → FINAL "
                    "REVIEW. Each implementation milestone should be small, reversible, testable, "
                    "observable, and independently understandable. Maintain a task checklist and "
                    "complete the smallest logical unit of work before moving to the next one."
                ),
                explanation="Break the job into tiny pieces that can be tested and undone.",
                when_to_use="Use as the strongest default for long-horizon coding agents.",
            ),
            ContractOption(
                label="Stricter: one independently testable unit before the next",
                body=(
                    "Do not start the next implementation unit until the current unit builds, the "
                    "relevant tests pass, and .agent/STATUS.md is updated. Follow DISCOVER → PLAN → "
                    "IMPLEMENT SMALL UNIT → TEST → INTEGRATE. No batching of unrelated units."
                ),
                explanation="Hard gate: the current slice must be green before the next slice starts.",
                when_to_use="Use when previous agent runs have sprawled.",
            ),
            ContractOption(
                label="Coarser: plan once, then implement in larger slices",
                body=(
                    "Discover and plan once, then implement in larger but still testable slices. "
                    "Re-validate after each slice. Prefer fewer checkpoints when the change is "
                    "localized to one module."
                ),
                explanation="Fewer checkpoints when the work is already small and local.",
                when_to_use="Use for single-file or single-module tasks.",
            ),
            _UNSPECIFIED,
        ),
    ),
    ContractQuestion(
        field_name="agent_contract.validation_strategy",
        section_title="Validation Strategy",
        standard_prompt="How should correctness be continuously verified?",
        beginner_prompt="How should the agent prove the change works as it goes, not only at the end?",
        beginner_rationale=(
            "\"Tests probably pass\" is not evidence. Named commands and results are."
        ),
        advanced_prompt=(
            "Require an incremental validation pyramid with recorded command output. Ban claiming "
            "success from assumed test results. Ban weakening tests to obtain a green run."
        ),
        options=(
            ContractOption(
                label="Recommended: validation pyramid with recorded command evidence",
                body=(
                    "Validate incrementally rather than waiting until the end. Use the validation "
                    "pyramid, running only layers relevant to the project: syntax/compilation; "
                    "static analysis; unit tests; component tests; integration tests; build/package "
                    "validation; runtime smoke test; end-to-end validation; acceptance criteria "
                    "validation. Add or update tests for new behavior. Existing tests should "
                    "continue passing. Do not disable, weaken, or remove failing tests solely to "
                    "obtain a successful result. Never use \"tests probably pass\" as evidence; "
                    "record the command and its pass/fail output."
                ),
                explanation="Run the real checks after meaningful changes and paste the results.",
                when_to_use="Use as the default whenever the repo has tests or a build.",
            ),
            ContractOption(
                label="Stricter: relevant tests must be green after every unit",
                body=(
                    "After every implementation unit, run the most relevant tests, type checks, "
                    "and linters, and record the command plus pass/fail counts. A unit is not done "
                    "while those checks fail. Do not skip, skip-mark, or delete failing tests to "
                    "force a green result."
                ),
                explanation="Every slice must leave the relevant tests green.",
                when_to_use="Use for high-risk or regression-prone areas.",
            ),
            ContractOption(
                label="Lightweight: smoke-test the changed path",
                body=(
                    "After meaningful changes, run the smallest relevant test or smoke command and "
                    "record the result. Full-suite runs are required before declaring COMPLETE. Do "
                    "not claim tests passed without command evidence."
                ),
                explanation="Cheap checks while working; a fuller run before calling it done.",
                when_to_use="Use when the full suite is very slow and the change is local.",
            ),
            _UNSPECIFIED,
        ),
    ),
    ContractQuestion(
        field_name="agent_contract.failure_recovery",
        section_title="Failure Recovery",
        standard_prompt="What should happen when something fails?",
        beginner_prompt="If a change breaks, should the agent keep retrying blindly or stop and diagnose?",
        beginner_rationale=(
            "Blind retries waste budget and can destroy a working state. Diagnose, then fix small."
        ),
        advanced_prompt=(
            "Require observe → capture → localize → hypothesize → test → minimal fix → revalidate. "
            "Ban suppressing errors without understanding them. After repeated failure, update the plan."
        ),
        options=(
            ContractOption(
                label="Recommended: diagnose, minimal fix, no blind retries",
                body=(
                    "Use OBSERVE → CAPTURE ERROR → LOCALIZE FAILURE → FORM HYPOTHESIS → TEST "
                    "HYPOTHESIS → APPLY MINIMAL FIX → REVALIDATE. After repeated unsuccessful "
                    "attempts: stop, review assumptions, inspect related architecture, consider an "
                    "alternative implementation, and update the plan. Never suppress an error "
                    "without understanding why it occurs. Do not repeatedly mutate the code hoping "
                    "the failure disappears."
                ),
                explanation="Stop, understand the error, try one small fix, then re-check.",
                when_to_use="Use as the default. This prevents thrashing.",
            ),
            ContractOption(
                label="Stricter: stop after two failed hypotheses and update the plan",
                body=(
                    "Follow the diagnose-and-minimal-fix loop. After two failed hypotheses on the "
                    "same error, stop coding, document the failure in .agent/ISSUES.md, revise "
                    ".agent/PLAN.md, and only then try an alternative approach. Never suppress an "
                    "error without understanding why it occurs."
                ),
                explanation="A tighter stop: two misses and the plan must change.",
                when_to_use="Use when prior runs burned budget on retry loops.",
            ),
            ContractOption(
                label="Allow more retries before changing approach",
                body=(
                    "Diagnose and apply minimal fixes. A few extra retry cycles are allowed when "
                    "each attempt tests a distinct hypothesis. If retries become repetitive, stop, "
                    "document the failure, and change approach. Never suppress an error without "
                    "understanding why it occurs."
                ),
                explanation="A little more room to try distinct ideas before abandoning a path.",
                when_to_use="Use for flaky environments where the first failure is often environmental.",
            ),
            _UNSPECIFIED,
        ),
    ),
    ContractQuestion(
        field_name="agent_contract.autonomy_policy",
        section_title="Autonomy Policy",
        standard_prompt="What can the agent decide autonomously?",
        beginner_prompt="Which decisions may the agent make alone, and which need a human?",
        beginner_rationale=(
            "Risk-weighted autonomy beats a blanket yes/no. Routine edits proceed; high-impact ones pause."
        ),
        advanced_prompt=(
            "Classify low-risk reversible actions as autonomous and high-impact irreversible actions "
            "as escalate (API breaks, security, data loss, production, licensing)."
        ),
        options=(
            ContractOption(
                label="Recommended: autonomous on low-risk work; escalate high-impact",
                body=(
                    "The agent may autonomously perform low-risk, reversible actions: variable "
                    "names, internal function design, test structure, small refactors, and adding a "
                    "small library when documented. Escalate / request human review for high-impact "
                    "or difficult-to-reverse actions: new major frameworks, database migrations, "
                    "public API breaks, security model changes, data deletion, production "
                    "deployment, destructive operations, licensing conflicts, major new "
                    "infrastructure, or unclear/conflicting requirements."
                ),
                explanation="Everyday coding can proceed. Big or irreversible calls wait for you.",
                when_to_use="Use as the default risk-weighted autonomy policy.",
            ),
            ContractOption(
                label="Stricter: escalate any new dependency, migration, or API change",
                body=(
                    "Autonomous: naming, local refactors, tests, and implementation inside existing "
                    "modules. Escalate: any new dependency, schema change, public API change, "
                    "security-related edit, data deletion, production change, or requirement conflict."
                ),
                explanation="A tighter human gate for anything that leaves the current module design.",
                when_to_use="Use in regulated, production, or high-review environments.",
            ),
            ContractOption(
                label="Broader: proceed unless the action is destructive or irreversible",
                body=(
                    "The agent may make implementation, refactoring, testing, and dependency "
                    "decisions that stay within architecture and scope. Escalate only for destructive "
                    "operations, data loss, security reductions, production deployment, or clearly "
                    "conflicting requirements."
                ),
                explanation="More freedom, still with a stop on irreversible harm.",
                when_to_use="Use for greenfield or sandbox repositories.",
            ),
            _UNSPECIFIED,
        ),
    ),
    ContractQuestion(
        field_name="agent_contract.persistent_memory",
        section_title="Persistent Agent Memory",
        standard_prompt="How should progress and reasoning be preserved?",
        beginner_prompt="Where should the agent write down the plan, status, and problems so work can resume later?",
        beginner_rationale=(
            "Long-horizon runs lose the chat. Durable .agent/ files are how another session continues."
        ),
        advanced_prompt=(
            "Require .agent/PLAN.md, STATUS.md, DECISIONS.md, and ISSUES.md with narrowly defined "
            "roles so another agent can resume without reconstructing history."
        ),
        options=(
            ContractOption(
                label="Recommended: .agent/ PLAN, STATUS, DECISIONS, ISSUES",
                body=(
                    "Maintain lightweight durable project state under .agent/: PLAN.md (objective, "
                    "milestones, dependencies, validation requirements); STATUS.md (current "
                    "milestone, completed work, current operation, next action); DECISIONS.md "
                    "(decision, reason, alternatives considered, consequences); ISSUES.md (problem, "
                    "evidence, attempts, current hypothesis, status). Keep them concise enough that "
                    "another agent can resume without reconstructing the entire history."
                ),
                explanation="Four small markdown files that another agent can pick up later.",
                when_to_use="Use as the default for any task that might span more than one session.",
            ),
            ContractOption(
                label="Stricter: update .agent/ after every milestone",
                body=(
                    "Use .agent/PLAN.md, STATUS.md, DECISIONS.md, and ISSUES.md. Update STATUS.md "
                    "after every milestone and before any pause, context reset, or escalation. Do "
                    "not rely on chat history as the source of truth."
                ),
                explanation="Same files, but they must be current at every checkpoint.",
                when_to_use="Use for multi-hour runs that will be interrupted.",
            ),
            ContractOption(
                label="Lightweight: STATUS.md plus DECISIONS.md only",
                body=(
                    "Maintain .agent/STATUS.md and .agent/DECISIONS.md. Fold the plan and open "
                    "issues into STATUS.md when the task is small. Prefer repository-local markdown "
                    "over chat memory."
                ),
                explanation="Fewer files when the work is short and unlikely to be handed off.",
                when_to_use="Use for short tasks that should still survive a refresh.",
            ),
            _UNSPECIFIED,
        ),
    ),
    ContractQuestion(
        field_name="agent_contract.completion_contract",
        section_title="Completion Contract",
        standard_prompt="What evidence is required before declaring completion?",
        beginner_prompt="What report must the agent produce before it is allowed to say the work is done?",
        beginner_rationale=(
            "Completion is determined by evidence against acceptance criteria, not by how much code was written."
        ),
        advanced_prompt=(
            "Require a completion report with status, summary, criteria checklist, changes, "
            "validation commands/results, decisions, limitations, issues, run instructions, and next steps."
        ),
        options=(
            ContractOption(
                label="Recommended: evidence report with COMPLETE / PARTIAL / BLOCKED / FAILED",
                body=(
                    "Before marking a task complete, produce a completion report containing: TASK "
                    "STATUS (COMPLETE | PARTIAL | BLOCKED | FAILED); SUMMARY of what was implemented; "
                    "ACCEPTANCE CRITERIA checklist; CHANGES (files/components modified); VALIDATION "
                    "(tests and commands executed); RESULTS (pass/fail); ARCHITECTURAL DECISIONS; "
                    "KNOWN LIMITATIONS; KNOWN ISSUES; RUN INSTRUCTIONS; NEXT STEPS. Completion is "
                    "determined by evidence against the acceptance criteria, not by the amount of "
                    "code produced. Do not declare COMPLETE while required tests are failing or "
                    "acceptance criteria remain unmet."
                ),
                explanation="A structured proof package, not a vibe that the code looks done.",
                when_to_use="Use as the default completion gate.",
            ),
            ContractOption(
                label="Stricter: no COMPLETE without pasted passing validation output",
                body=(
                    "Same completion report as the recommended default, plus: COMPLETE is forbidden "
                    "unless the report includes the exact validation commands and their pass/fail "
                    "output. Missing evidence means PARTIAL or BLOCKED."
                ),
                explanation="Adds a hard rule: no green status without pasted command results.",
                when_to_use="Use when another agent or reviewer will audit the run.",
            ),
            ContractOption(
                label="Lightweight: short summary, commands run, and remaining issues",
                body=(
                    "Before completing, report status, a short summary, commands run with results, "
                    "and remaining issues. Use PARTIAL when follow-up remains. Do not declare "
                    "COMPLETE while known required tests are failing."
                ),
                explanation="A shorter report that still demands evidence.",
                when_to_use="Use for small tasks where a full template is overhead.",
            ),
            _UNSPECIFIED,
        ),
    ),
    ContractQuestion(
        field_name="agent_contract.resource_budget",
        section_title="Resource and Budget Governance",
        standard_prompt="What are the operational budget, API call, and execution time boundaries before pausing?",
        beginner_prompt="How long may the agent keep going before it must pause and ask you?",
        beginner_rationale=(
            "Long-horizon runs are expensive. Hard pause limits stop infinite loops from burning budget."
        ),
        advanced_prompt=(
            "Set max API calls, iteration loops, and wall-clock time per sub-task, with "
            "PAUSE_AND_PERSIST to .agent/STATUS.md on exceed."
        ),
        options=(
            ContractOption(
                label="Recommended: 150 API calls, 50 loops, 2 hours per sub-task",
                body=(
                    "Set a maximum budget of 150 LLM API calls, 50 continuous iteration loops, and "
                    "2 hours of wall-clock time per sub-task. If any limit is reached, pause "
                    "execution, flush state to .agent/STATUS.md, and request human review rather "
                    "than spinning indefinitely. on_budget_exceeded: PAUSE_AND_PERSIST."
                ),
                explanation="Sensible caps so a stuck agent stops and saves its work.",
                when_to_use="Use as the default budget for long-horizon coding runs.",
            ),
            ContractOption(
                label="Stricter: 80 API calls, 25 loops, 60 minutes per sub-task",
                body=(
                    "Maximum budget: 80 LLM API calls, 25 continuous iteration loops, and 60 minutes "
                    "of wall-clock time per sub-task. On any limit, pause, persist .agent/STATUS.md, "
                    "and request human review. on_budget_exceeded: PAUSE_AND_PERSIST."
                ),
                explanation="Tighter caps for cost-sensitive or experimental runs.",
                when_to_use="Use when you want an earlier human checkpoint.",
            ),
            ContractOption(
                label="Larger: 300 API calls, 80 loops, 4 hours per sub-task",
                body=(
                    "Maximum budget: 300 LLM API calls, 80 continuous iteration loops, and 4 hours "
                    "of wall-clock time per sub-task. On any limit, pause, persist .agent/STATUS.md, "
                    "and request human review rather than spinning indefinitely."
                ),
                explanation="More room for genuinely large migrations, still with a hard stop.",
                when_to_use="Use for large refactors you expect to run for hours.",
            ),
            _UNSPECIFIED,
        ),
    ),
    ContractQuestion(
        field_name="agent_contract.tool_safety",
        section_title="Tool Safety and Shell Restrictions",
        standard_prompt="Which CLI commands, network permissions, and file paths are strictly restricted?",
        beginner_prompt="What commands and network access must the agent never use?",
        beginner_rationale=(
            "A coding agent with a shell can destroy data or leak secrets. Spell out the fence."
        ),
        advanced_prompt=(
            "Restrict network to package registries and local dev servers; ban destructive commands, "
            "force pushes, and secret printing; require sandboxed execution and secret redaction."
        ),
        options=(
            ContractOption(
                label="Recommended: sandboxed shell; no secrets, force-push, or rm -rf /",
                body=(
                    "Network access is isolated to package registries and local dev servers. "
                    "Destructive commands (rm -rf outside build artifacts, force pushes, credential "
                    "reads) are prohibited. Sandboxed execution only. Secrets and credentials must "
                    "never be printed, logged, or committed. Blacklisted examples include rm -rf /, "
                    "git push --force, and chmod 777. secret_redaction: true."
                ),
                explanation="Normal installs are fine. Wiping disks, force-pushing, and dumping secrets are not.",
                when_to_use="Use as the default tool fence.",
            ),
            ContractOption(
                label="Stricter: no network except named package registries",
                body=(
                    "Network is limited to explicitly named package registries. No browsing, no "
                    "arbitrary downloads, no production hosts. Destructive git and filesystem "
                    "commands are prohibited. Secrets must never be printed, logged, or committed. "
                    "Sandboxed execution is required."
                ),
                explanation="Even tighter: the agent should not reach the open internet.",
                when_to_use="Use on sensitive machines or when supply-chain risk is high.",
            ),
            ContractOption(
                label="Standard repo hygiene: no force-push, no secret commits",
                body=(
                    "Do not force-push, do not rewrite published history, do not commit secrets, "
                    "and do not run destructive filesystem commands outside build artifacts. Local "
                    "dev servers and package registries are allowed."
                ),
                explanation="The usual git/safety rules without a full sandbox story.",
                when_to_use="Use when the agent already runs in a trusted developer environment.",
            ),
            _UNSPECIFIED,
        ),
    ),
    ContractQuestion(
        field_name="agent_contract.context_compaction",
        section_title="Context Compaction and State Persistence",
        standard_prompt=(
            "How does the agent manage context window decay without losing progress during "
            "multi-hour runs? For locally run models in 2026, a 100,000-token context is "
            "considered large — compact well before the window is full."
        ),
        beginner_prompt=(
            "When the conversation gets too long, what must the agent keep versus summarize? "
            "On a locally run model in 2026, 100,000 tokens is a large window, so compact "
            "early rather than assuming there is room to keep everything."
        ),
        beginner_rationale=(
            "Long runs fill the context window. The task contract and .agent/ files must "
            "survive compaction. A 100,000-token window is large for locally run models in "
            "2026, so do not treat that size as a reason to skip or delay compaction."
        ),
        advanced_prompt=(
            "Compact at 80% window capacity. Treat 100,000 tokens as a large local-model "
            "window in 2026. Preserve system prompt, task contract, .agent/*, and modified "
            "file list. Prune verbose logs and superseded planning chatter. Reinject state "
            "on reset."
        ),
        options=(
            ContractOption(
                label="Recommended: compact at 80%; keep contract and .agent/ state",
                body=(
                    "Trigger context compaction at 80% window capacity. For locally run models "
                    "in 2026, 100,000 tokens is a large context window, so do not wait until "
                    "the window is nearly full. Summarize raw terminal outputs and conversational "
                    "history while forcibly preserving the primary task contract, active goal, "
                    "modified file tree, and current .agent/ state files across context resets. "
                    "Prune verbose terminal logs and superseded planning chatter. Reinject "
                    "state on reset. Clarity of the surviving contract matters more than "
                    "retaining every intermediate token."
                ),
                explanation="Drop noisy logs; never drop the task contract or the .agent/ files.",
                when_to_use=(
                    "Use as the default for multi-hour agent runs on locally run models, "
                    "including 100,000-token windows."
                ),
            ),
            ContractOption(
                label="Stricter: compact at 70%; never drop the task contract",
                body=(
                    "Compact at 70% window capacity. The task contract, current goal, .agent/* "
                    "files, and modified file list are never summarized away. Terminal logs are "
                    "first to go. Reinject state on every reset. Use this when the local window "
                    "is smaller than 100,000 tokens."
                ),
                explanation="Compacts sooner so the contract always has room.",
                when_to_use="Use with smaller-context locally run models.",
            ),
            ContractOption(
                label="Preserve more history; compact only at 90%",
                body=(
                    "Delay compaction until 90% window capacity. Still preserve the task contract "
                    "and .agent/ files first. Summarize logs before dropping decisions. In 2026, "
                    "100,000 tokens is already large for locally run models, so this option is "
                    "only for windows well beyond that size."
                ),
                explanation=(
                    "Keeps more conversation only when the window is unusually large. A "
                    "100,000-token local window in 2026 should still compact at 80%."
                ),
                when_to_use=(
                    "Use only with context windows well beyond 100,000 tokens. Typical locally "
                    "run models in 2026 should compact at 80% instead."
                ),
            ),
            _UNSPECIFIED,
        ),
    ),
    ContractQuestion(
        field_name="agent_contract.rollback_protocol",
        section_title="Rollback and Backtracking",
        standard_prompt="When and how does the agent restore code state when an implementation strategy fails?",
        beginner_prompt="If a plan is not working, should the agent rewind to the last good commit?",
        beginner_rationale=(
            "Failed strategies should be abandoned cleanly, not stacked on top of broken code."
        ),
        advanced_prompt=(
            "Checkpoint on test pass; after 3 consecutive failed fix attempts, reset to last green, "
            "document in ISSUES.md, and clear failed plan branches."
        ),
        options=(
            ContractOption(
                label="Recommended: checkpoint on green tests; reset after 3 failed fixes",
                body=(
                    "Create short-lived atomic git commits after every passing test suite. Upon "
                    "reaching 3 consecutive failed fix attempts, execute git reset to the last green "
                    "checkpoint, clear invalid branches from .agent/PLAN.md, document the failure in "
                    ".agent/ISSUES.md, and attempt an alternative approach."
                ),
                explanation="Save a good snapshot, then rewind if three fixes in a row fail.",
                when_to_use="Use as the default backtracking protocol.",
            ),
            ContractOption(
                label="Stricter: reset after 2 consecutive failed fixes",
                body=(
                    "Checkpoint on passing tests. After 2 consecutive failed fix attempts, reset to "
                    "the last green checkpoint, update .agent/ISSUES.md, clear the failed plan "
                    "branch, and choose an alternative approach."
                ),
                explanation="Rewinds sooner so a bad approach cannot dig a deep hole.",
                when_to_use="Use when the repo is easy to break and hard to untangle.",
            ),
            ContractOption(
                label="Manual: document failure and ask before resetting",
                body=(
                    "Checkpoint on passing tests. After repeated failed fixes, document the failure "
                    "in .agent/ISSUES.md and escalate before running a hard git reset. Do not keep "
                    "stacking failed patches."
                ),
                explanation="Asks a human before discarding work, while still refusing to thrash.",
                when_to_use="Use when uncommitted work may include irreplaceable investigation.",
            ),
            _UNSPECIFIED,
        ),
    ),
    ContractQuestion(
        field_name="agent_contract.escalation_rules",
        section_title="Escalation and HITL Interruption",
        standard_prompt="What specific trigger conditions require halting execution to request human intervention?",
        beginner_prompt="When must the agent stop and ask you instead of guessing?",
        beginner_rationale=(
            "Guessing through missing secrets or conflicting criteria wastes a long-horizon run."
        ),
        advanced_prompt=(
            "Pause immediately on missing secrets, ambiguous acceptance criteria, schema-breaking "
            "migrations, license conflicts, or recovery-loop exhaustion."
        ),
        options=(
            ContractOption(
                label="Recommended: pause on secrets, conflicts, migrations, licenses, exhausted recovery",
                body=(
                    "Pause execution immediately upon encountering missing credentials/secrets, "
                    "ambiguous or conflicting acceptance criteria, schema-breaking database "
                    "migrations, licensing policy conflicts, or 3 consecutive failed recovery "
                    "attempts. Persist .agent/STATUS.md before waiting."
                ),
                explanation="Stops at the moments where a wrong guess is expensive or unsafe.",
                when_to_use="Use as the default human-in-the-loop gate.",
            ),
            ContractOption(
                label="Stricter: also pause on any public API or security-model change",
                body=(
                    "Pause on missing secrets, ambiguous criteria, schema-breaking migrations, "
                    "license conflicts, recovery-loop exhaustion, public API changes, and security "
                    "model changes. Persist state before waiting."
                ),
                explanation="Adds API and security changes to the stop list.",
                when_to_use="Use for shared libraries and production services.",
            ),
            ContractOption(
                label="Minimal: pause only for secrets, data loss, or exhausted recovery",
                body=(
                    "Pause for missing credentials/secrets, likely data loss, or 3 consecutive "
                    "failed recovery attempts. Other ambiguities may be documented in ISSUES.md "
                    "and continued only when a reversible default exists."
                ),
                explanation="Fewer interruptions; still will not guess at secrets or destroy data.",
                when_to_use="Use for trusted sandbox work where you want fewer pauses.",
            ),
            _UNSPECIFIED,
        ),
    ),
    ContractQuestion(
        field_name="agent_contract.dependency_security",
        section_title="Dependency and Security Verification",
        standard_prompt="What static security checks and package management rules must run prior to completion?",
        beginner_prompt="What license and vulnerability rules apply before adding a new package?",
        beginner_rationale=(
            "A new dependency can import license and security debt that outlives the task."
        ),
        advanced_prompt=(
            "Require SAST and vulnerability audits before new packages; allow only OSI-permissive "
            "licenses (MIT, Apache-2.0, BSD); pin minor versions; fail on high/critical vulns."
        ),
        options=(
            ContractOption(
                label="Recommended: SAST + audit; MIT/Apache/BSD; pin minor versions",
                body=(
                    "Run static analysis (SAST) and vulnerability scans (npm audit, pip-audit, or "
                    "the project equivalent) before introducing external packages. New dependencies "
                    "must use OSI-approved permissive licenses (MIT, Apache-2.0, BSD-3-Clause) and "
                    "be locked to specific minor versions. High or critical vulnerabilities are "
                    "disallowed. vulnerability_audit: strict_zero_high_critical."
                ),
                explanation="Scan, stick to common open licenses, and pin versions.",
                when_to_use="Use as the default before adding packages.",
            ),
            ContractOption(
                label="Stricter: no new dependencies unless the task names them",
                body=(
                    "Do not add dependencies unless the task explicitly names them. If a named "
                    "dependency is added, run SAST and vulnerability scans, require MIT / Apache-2.0 "
                    " / BSD-3-Clause, pin the minor version, and fail on high or critical findings."
                ),
                explanation="Default is zero new packages.",
                when_to_use="Use when the lockfile is frozen or review is expensive.",
            ),
            ContractOption(
                label="Existing-policy: follow the repo's current license and audit rules",
                body=(
                    "Follow the repository's existing dependency, license, and security-scan "
                    "conventions. If none are documented, prefer OSI-permissive licenses, pin "
                    "versions, and run the project's audit command before completion."
                ),
                explanation="Mirror whatever this repo already does, with a safe fallback.",
                when_to_use="Use when the project already has a security/dependency policy.",
            ),
            _UNSPECIFIED,
        ),
    ),
)


CONTRACT_FIELD_NAMES: tuple[str, ...] = tuple(question.field_name for question in CONTRACT_QUESTIONS)

CONTRACT_SECTION_TITLES: tuple[str, ...] = tuple(
    question.section_title for question in CONTRACT_QUESTIONS
)

CONTRACT_QUESTION_BY_FIELD: dict[str, ContractQuestion] = {
    question.field_name: question for question in CONTRACT_QUESTIONS
}


def quick_reply_labels(field_name: str) -> tuple[str, ...]:
    question = CONTRACT_QUESTION_BY_FIELD.get(field_name)
    if question is None:
        return (UNSPECIFIED_LABEL,)
    return tuple(option.label for option in question.options)


def option_body_map(field_name: str) -> dict[str, str]:
    question = CONTRACT_QUESTION_BY_FIELD.get(field_name)
    if question is None:
        return {}
    return {option.label: option.body for option in question.options if option.body}


def expand_clarification_answer(field_name: str, answer: str) -> str:
    """Replace known quick-reply labels with their full default policy text."""
    mapping = option_body_map(field_name)
    if not mapping:
        return answer.strip()
    parts = [part.strip() for part in answer.split(";") if part.strip()]
    expanded = [mapping.get(part, part) for part in parts]
    return "\n\n".join(expanded).strip()


def beginner_option_text(field_name: str) -> dict[str, tuple[str, str]]:
    question = CONTRACT_QUESTION_BY_FIELD.get(field_name)
    if question is None:
        return {}
    return {
        option.label: (option.explanation, option.when_to_use) for option in question.options
    }
