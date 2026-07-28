import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RequirementCardPanel } from "../components/RequirementCardPanel";

describe("RequirementCardPanel", () => {
  it("renders objective and unresolved fields", () => {
    render(
      <RequirementCardPanel
        card={{
          technical_context: {
            environment: "Python 3.12 + FastAPI",
            integration_points: [],
            dependency_policy: "",
            forbidden_libraries: [],
          },
          core_task_scope: {
            task_type: "new feature logic",
            objective: "Add a health endpoint",
            out_of_scope: [],
          },
          inputs_outputs_contracts: {
            inputs: "",
            output_contract: "JSON {status: ok}",
            examples: [],
          },
          architectural_rules: {
            design_patterns: [],
            coding_style: "",
            non_functional: ["O(n) or better"],
          },
          edge_cases_error_strategy: {
            failure_handling: "",
            bad_inputs: [],
            edge_cases: [],
          },
          response_formatting: {
            explanation_level: "",
            verbosity: "",
            extra_artifacts: [],
          },
          optimization_targets: {},
          unresolved_fields: ["response_formatting.explanation_level"],
        }}
      />,
    );

    expect(screen.getByText("Add a health endpoint")).toBeInTheDocument();
    expect(screen.getByText("Python 3.12 + FastAPI")).toBeInTheDocument();
    expect(screen.getByText("response_formatting.explanation_level")).toBeInTheDocument();
  });
});
