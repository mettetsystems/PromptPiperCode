from __future__ import annotations

from prompt_piper_api.domain.optimization import ConstraintGraph, ConstraintSlot
from prompt_piper_api.domain.requirement_card import RequirementCard
from prompt_piper_api.services.optimization.constraint_graph_pass import extract_section
from prompt_piper_api.services.requirement_capture import dedupe_phrases


class RewriteCompressionPass:
    """Pass 2: rebuild into canonical coding-dimension structure and front-load instructions."""

    def run(
        self,
        body: str,
        card: RequirementCard,
        graph: ConstraintGraph,
    ) -> tuple[str, list[str]]:
        compressed_notes: list[str] = []

        core_task = dedupe_phrases(
            self._slot_values(graph, ConstraintSlot.OBJECTIVE)
            or extract_section(body, "Core Task and Scope")
        )[:4]
        technical = self._build_technical_context(body, card, graph)
        io_contract = dedupe_phrases(
            self._slot_values(graph, ConstraintSlot.FORMAT)
            or extract_section(body, "Inputs, Outputs, and Contracts")
        )[:4]
        architectural = dedupe_phrases(
            self._slot_values(graph, ConstraintSlot.SCOPE)
            + self._slot_values(graph, ConstraintSlot.MUST_CITE)
        ) or extract_section(body, "Architectural Rules and Constraints")
        tools = self._build_tools(graph)
        edge_errors = extract_section(body, "Edge Cases and Error Strategy")
        response_fmt = extract_section(body, "Response Formatting") or self._build_response_fmt(
            card
        )
        artifact_rules = self._slot_values(graph, ConstraintSlot.ARTIFACT_REQUIRED)

        if card.architectural_rules.non_functional and len(architectural) > len(
            card.architectural_rules.non_functional
        ):
            compressed_notes.append("Merged duplicate constraint statements.")

        sections: list[tuple[str, list[str]]] = [
            ("Technical Context", technical[:5]),
            ("Core Task and Scope", core_task[:4]),
            ("Inputs, Outputs, and Contracts", io_contract[:4]),
            ("Architectural Rules and Constraints", architectural[:8]),
            ("Tools", tools),
            ("Edge Cases and Error Strategy", edge_errors[:5]),
            ("Response Formatting", response_fmt[:4]),
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
    def _build_technical_context(
        body: str,
        card: RequirementCard,
        graph: ConstraintGraph,
    ) -> list[str]:
        lines: list[str] = []
        environment = graph.slots.get(ConstraintSlot.AUDIENCE.value, [])
        if environment:
            lines.append(f"Environment: {environment[0]}")
        elif card.technical_context.environment.strip():
            lines.append(f"Environment: {card.technical_context.environment.strip()}")
        if card.technical_context.dependency_policy.strip():
            lines.append(f"Dependency policy: {card.technical_context.dependency_policy.strip()}")
        if card.technical_context.integration_points:
            lines.append(
                "Integration points: " + "; ".join(card.technical_context.integration_points)
            )
        for line in extract_section(body, "Technical Context"):
            if line.lower().startswith("environment:"):
                continue
            if line not in lines:
                lines.append(line)
        return lines

    @staticmethod
    def _build_response_fmt(card: RequirementCard) -> list[str]:
        lines: list[str] = []
        if card.response_formatting.explanation_level.strip():
            lines.append(
                f"Explanation level: {card.response_formatting.explanation_level.strip()}"
            )
        if card.response_formatting.verbosity.strip():
            lines.append(f"Verbosity: {card.response_formatting.verbosity.strip()}")
        if card.response_formatting.extra_artifacts:
            lines.append(
                "Extra artifacts: " + "; ".join(card.response_formatting.extra_artifacts)
            )
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
