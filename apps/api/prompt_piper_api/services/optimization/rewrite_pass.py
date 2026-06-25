from __future__ import annotations

from prompt_piper_api.domain.optimization import ConstraintGraph, ConstraintSlot
from prompt_piper_api.domain.requirement_card import RequirementCard
from prompt_piper_api.services.optimization.constraint_graph_pass import extract_section
from prompt_piper_api.services.requirement_capture import dedupe_phrases


class RewriteCompressionPass:
    """Pass 2: rebuild into canonical structure and front-load salient instructions."""

    def run(
        self,
        body: str,
        card: RequirementCard,
        graph: ConstraintGraph,
    ) -> tuple[str, list[str]]:
        compressed_notes: list[str] = []

        mission = dedupe_phrases(
            self._slot_values(graph, ConstraintSlot.OBJECTIVE) or extract_section(body, "Mission")
        )[:2]
        context = self._build_context(body, card, graph)
        constraints = dedupe_phrases(
            self._slot_values(graph, ConstraintSlot.SCOPE)
            + self._slot_values(graph, ConstraintSlot.MUST_CITE)
        ) or extract_section(body, "Constraints")
        tools = self._build_tools(graph)
        style = extract_section(body, "Style") or (
            [card.tone_style.strip()] if card.tone_style.strip() else []
        )
        output_contract = dedupe_phrases(
            self._slot_values(graph, ConstraintSlot.FORMAT) or extract_section(body, "Output contract")
        )[:2]
        acceptance = extract_section(body, "Acceptance criteria")
        artifact_rules = self._slot_values(graph, ConstraintSlot.ARTIFACT_REQUIRED)

        if card.constraints and len(constraints) > len(card.constraints):
            compressed_notes.append("Merged duplicate constraint statements.")

        sections: list[tuple[str, list[str]]] = [
            ("Mission", mission[:2]),
            ("Context", context[:3]),
            ("Constraints", constraints[:8]),
            ("Tools", tools),
            ("Style", style[:2]),
            ("Output contract", output_contract[:2]),
            ("Acceptance tests", acceptance[:5]),
            ("Artifact rules", artifact_rules),
        ]

        rendered = "\n\n".join(
            self._render_section(title, lines) for title, lines in sections if lines
        )
        return rendered, compressed_notes

    @staticmethod
    def _slot_values(graph: ConstraintGraph, slot: ConstraintSlot) -> list[str]:
        return list(graph.slots.get(slot.value, []))

    @staticmethod
    def _build_context(body: str, card: RequirementCard, graph: ConstraintGraph) -> list[str]:
        lines: list[str] = []
        audience = graph.slots.get(ConstraintSlot.AUDIENCE.value, [])
        if audience:
            lines.append(f"Audience: {audience[0]}")
        elif card.audience.strip():
            lines.append(f"Audience: {card.audience.strip()}")
        if card.context_background.strip():
            lines.append(f"Background: {card.context_background.strip()}")
        if card.language.strip():
            lines.append(f"Language: {card.language.strip()}")
        context_lines = extract_section(body, "Context")
        for line in context_lines:
            if line.lower().startswith("audience:"):
                continue
            if line.lower().startswith("language:"):
                continue
            if line not in lines:
                lines.append(line)
        return lines

    @staticmethod
    def _build_tools(graph: ConstraintGraph) -> list[str]:
        tools: list[str] = []
        tool_slots = (
            ConstraintSlot.MUST_CITE,
            ConstraintSlot.SOURCE_LIMIT,
            ConstraintSlot.FINAL_VENDOR,
        )
        for slot in tool_slots:
            tools.extend(graph.slots.get(slot.value, []))
        return tools[:4]

    @staticmethod
    def _render_section(title: str, lines: list[str]) -> str:
        divider = "-" * len(title)
        return f"{title}\n{divider}\n" + "\n".join(lines)
