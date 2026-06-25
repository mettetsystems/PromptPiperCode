import { describe, expect, it } from "vitest";
import { buildClarificationAnswer, toggleClarificationOption } from "./clarificationAnswer";

describe("buildClarificationAnswer", () => {
  it("combines multiple quick replies", () => {
    expect(
      buildClarificationAnswer(["bulleted summary", "markdown report"], ""),
    ).toBe("bulleted summary; markdown report");
  });

  it("appends custom text", () => {
    expect(
      buildClarificationAnswer(["engineering team"], "new hires"),
    ).toBe("engineering team; new hires");
  });

  it("returns unspecified when that option is selected", () => {
    expect(buildClarificationAnswer(["engineering team", "unspecified"], "extra")).toBe(
      "unspecified",
    );
  });

  it("returns null when nothing is selected", () => {
    expect(buildClarificationAnswer([], "  ")).toBeNull();
  });
});

describe("toggleClarificationOption", () => {
  it("selects and deselects options", () => {
    let selected: string[] = [];
    selected = toggleClarificationOption(selected, "bulleted summary");
    expect(selected).toEqual(["bulleted summary"]);
    selected = toggleClarificationOption(selected, "bulleted summary");
    expect(selected).toEqual([]);
  });

  it("clears other options when unspecified is chosen", () => {
    expect(toggleClarificationOption(["engineering team"], "unspecified")).toEqual(["unspecified"]);
  });
});
