import { describe, expect, it } from "vitest";
import {
  canVisitStep,
  isSessionClosed,
  isStepAhead,
  sessionPath,
  sessionStepForState,
} from "./sessionRouting";

describe("sessionStepForState", () => {
  it("maps clarification states to clarify step", () => {
    expect(sessionStepForState("clarifying")).toBe("clarify");
  });

  it("maps post-finalize workflow states", () => {
    expect(sessionStepForState("edit")).toBe("edit");
    expect(sessionStepForState("similarity_check")).toBe("similarity");
    expect(sessionStepForState("optimization")).toBe("optimize");
    expect(sessionStepForState("approval")).toBe("export");
    expect(sessionStepForState("exported")).toBe("complete");
  });

  it("treats exported sessions as closed", () => {
    expect(isSessionClosed("exported")).toBe(true);
    expect(isSessionClosed("approval")).toBe(false);
  });
});

describe("sessionPath", () => {
  it("builds session workflow paths", () => {
    expect(sessionPath("abc-123", "edit")).toBe("/sessions/abc-123/edit");
  });
});

describe("workflow navigation", () => {
  it("allows visiting current and earlier steps", () => {
    expect(canVisitStep("edit", "optimization")).toBe(true);
    expect(canVisitStep("similarity", "optimization")).toBe(true);
    expect(canVisitStep("optimize", "optimization")).toBe(true);
  });

  it("blocks visiting future steps", () => {
    expect(canVisitStep("export", "optimization")).toBe(false);
    expect(isStepAhead("export", "optimization")).toBe(true);
    expect(isStepAhead("edit", "optimization")).toBe(false);
  });
});
