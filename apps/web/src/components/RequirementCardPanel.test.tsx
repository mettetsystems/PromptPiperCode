import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RequirementCardPanel } from "../components/RequirementCardPanel";

describe("RequirementCardPanel", () => {
  it("renders objective and unresolved fields", () => {
    render(
      <RequirementCardPanel
        card={{
          objective: "Summarize weekly status",
          context_background: "",
          audience: "Engineering managers",
          persona_role: "",
          input_materials: [],
          constraints: ["Keep under 300 words"],
          desired_output_shape: "Bulleted summary",
          tone_style: "",
          verbosity: "",
          forbidden_content_actions: [],
          success_criteria: [],
          example_outputs: [],
          edge_cases: [],
          language: "en",
          optimization_targets: {},
          unresolved_fields: ["tone_style"],
        }}
      />,
    );

    expect(screen.getByText("Summarize weekly status")).toBeInTheDocument();
    expect(screen.getByText("Engineering managers")).toBeInTheDocument();
    expect(screen.getByText("tone_style")).toBeInTheDocument();
  });
});
