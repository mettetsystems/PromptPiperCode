import { describe, expect, it } from "vitest";
import { isSpaNavigation } from "./vite.proxy";

const sessionId = "11111111-1111-4111-8111-111111111111";

describe("isSpaNavigation", () => {
  it("proxies DELETE /sessions/:id even when Accept includes text/html", () => {
    expect(
      isSpaNavigation(`/sessions/${sessionId}`, "text/html,application/xhtml+xml", "DELETE"),
    ).toBe(false);
  });

  it("proxies JSON GET /sessions/:id to the API", () => {
    expect(isSpaNavigation(`/sessions/${sessionId}`, "*/*", "GET")).toBe(false);
  });

  it("serves the SPA for browser GET of a workflow step", () => {
    expect(
      isSpaNavigation(`/sessions/${sessionId}/edit`, "text/html", "GET"),
    ).toBe(true);
  });

  it("proxies POST /sessions/:id/delete", () => {
    expect(
      isSpaNavigation(`/sessions/${sessionId}/delete`, "text/html,application/xhtml+xml", "POST"),
    ).toBe(false);
  });
});
