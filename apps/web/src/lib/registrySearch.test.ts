import { describe, expect, it } from "vitest";
import type { RegistryPromptSummary } from "../api/types";
import { filterRegistryPrompts, matchesRegistryKeyword } from "./registrySearch";

const sample: RegistryPromptSummary = {
  prompt_id: "weekly-status-update-b9154b85",
  version: 1,
  title: "Weekly status update",
  abstract: "Concise engineering summary for stakeholders",
  tags: ["status", "engineering"],
  output_form: "markdown report",
  evaluation_scores: {},
  artifact_paths: {},
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-02T00:00:00Z",
};

describe("registrySearch", () => {
  it("matches empty query", () => {
    expect(matchesRegistryKeyword(sample, "")).toBe(true);
    expect(matchesRegistryKeyword(sample, "   ")).toBe(true);
  });

  it("matches title and prompt id terms", () => {
    expect(matchesRegistryKeyword(sample, "weekly")).toBe(true);
    expect(matchesRegistryKeyword(sample, "b9154b85")).toBe(true);
    expect(matchesRegistryKeyword(sample, "missing-term")).toBe(false);
  });

  it("requires all whitespace-separated terms", () => {
    expect(matchesRegistryKeyword(sample, "weekly engineering")).toBe(true);
    expect(matchesRegistryKeyword(sample, "weekly finance")).toBe(false);
  });

  it("filters prompt lists", () => {
    expect(filterRegistryPrompts([sample], "status").length).toBe(1);
    expect(filterRegistryPrompts([sample], "missing").length).toBe(0);
  });
});
