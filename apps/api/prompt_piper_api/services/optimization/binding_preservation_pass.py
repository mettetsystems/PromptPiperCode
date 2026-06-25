from __future__ import annotations

import re

from prompt_piper_api.domain.optimization import ConstraintGraph
from prompt_piper_api.domain.requirement_card import RequirementCard
from prompt_piper_api.services.optimization.constraint_graph_pass import extract_section
from prompt_piper_api.services.requirement_capture import (
    RequirementCaptureEvaluator,
    body_chunks,
    collect_optimization_binding_phrases,
    normalize_phrase_for_capture,
)


class BindingPreservationPass:
    """Ensure binding constraint-graph instructions survive compression passes."""

    def __init__(self, evaluator: RequirementCaptureEvaluator | None = None) -> None:
        self._evaluator = evaluator or RequirementCaptureEvaluator()

    def run(
        self,
        body: str,
        graph: ConstraintGraph,
        card: RequirementCard,
    ) -> tuple[str, list[str]]:
        phrases = collect_optimization_binding_phrases(graph, card)
        chunks = body_chunks(body)
        missing = [
            phrase
            for phrase in phrases
            if not self._evaluator.captures_phrase(phrase, body, chunks)
        ]
        if not missing:
            return body, []

        preserved: list[str] = []
        constraints = extract_section(body, "Constraints")
        existing = {normalize_phrase_for_capture(line) for line in constraints}
        for phrase in missing:
            key = normalize_phrase_for_capture(phrase)
            if key in existing:
                continue
            constraints.append(phrase)
            existing.add(key)
            preserved.append(f"Preserved binding requirement: {phrase}")

        if not preserved:
            return body, []

        if re.search(r"^Constraints\n-+\n", body, re.MULTILINE | re.IGNORECASE):
            body = self._replace_section(body, "Constraints", constraints)
        else:
            divider = "-" * len("Constraints")
            body = f"{body.rstrip()}\n\nConstraints\n{divider}\n" + "\n".join(constraints)

        return body, preserved

    @staticmethod
    def _replace_section(body: str, title: str, lines: list[str]) -> str:
        pattern = re.compile(
            rf"^({re.escape(title)}\n-+\n)(.*?)(?=\n[A-Za-z].*\n-+\n|\Z)",
            re.MULTILINE | re.DOTALL | re.IGNORECASE,
        )
        replacement = rf"\1" + "\n".join(lines) + "\n"
        updated, count = pattern.subn(replacement, body, count=1)
        return updated if count else body
