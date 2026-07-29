import { beforeEach, describe, expect, it } from "vitest";
import {
  RECENT_SESSIONS_KEY,
  loadRecentSessions,
  saveRecentSessions,
  upsertRecentSession,
} from "./recentSessions";
import type { SessionDetailResponse } from "../api/types";

const sampleSession = {
  session: {
    id: "session-1",
    title: "Weekly status",
    state: "edit",
    current_draft_id: null,
    prompt_id: null,
    clarification_turn: 2,
    created_at: "2026-06-15T12:00:00Z",
    updated_at: "2026-06-15T12:05:00Z",
  },
  requirement_card: {
    technical_context: {
      environment: "",
      integration_points: [],
      dependency_policy: "",
      forbidden_libraries: [],
    },
    core_task_scope: {
      task_type: "",
      objective: "Summarize status",
      out_of_scope: [],
    },
    inputs_outputs_contracts: {
      inputs: "",
      output_contract: "",
      examples: [],
    },
    architectural_rules: {
      design_patterns: [],
      coding_style: "",
      non_functional: [],
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
    unresolved_fields: [],
  },
  clarification_question: null,
  clarification_field: null,
  clarification_question_number: null,
  clarification_total_questions: null,
  clarification_quick_replies: null,
  clarification_versions: null,
  current_draft: null,
  revised_draft: null,
  semantic_diff: null,
  change_summary: null,
  edit_intent: null,
  updated_requirement_card: null,
  prompt_id: null,
  registry_warning: null,
  similarity_warning: "A similar prompt pattern may already exist.",
  similarity_matches: [],
  optimization_result: null,
  artifact_manifest: null,
  artifact_warning: null,
  export_id: null,
  container_export_path: null,
  expected_host_export_path: null,
  manifest_path: null,
  generated_files: [],
  warnings: [],
} satisfies SessionDetailResponse;

describe("recentSessions", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("persists and loads recent sessions", () => {
    saveRecentSessions([
      {
        id: "a",
        title: "A",
        state: "edit",
        promptId: null,
        similarityWarning: null,
        updatedAt: "2026-06-15T12:00:00Z",
      },
    ]);
    expect(loadRecentSessions()).toHaveLength(1);
    expect(localStorage.getItem(RECENT_SESSIONS_KEY)).toContain("A");
  });

  it("upserts by session id", () => {
    upsertRecentSession(sampleSession);
    const updated = upsertRecentSession({
      ...sampleSession,
      session: { ...sampleSession.session, title: "Updated title" },
    });
    expect(updated).toHaveLength(1);
    expect(updated[0]?.title).toBe("Updated title");
    expect(updated[0]?.similarityWarning).toContain("similar prompt");
  });
});
