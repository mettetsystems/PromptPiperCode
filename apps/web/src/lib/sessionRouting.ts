import type { SessionState } from "../api/types";

export type SessionStep =
  | "clarify"
  | "edit"
  | "similarity"
  | "optimize"
  | "export"
  | "complete";

export const SESSION_STEPS: readonly SessionStep[] = [
  "clarify",
  "edit",
  "similarity",
  "optimize",
  "export",
  "complete",
] as const;

export const SESSION_STEP_LABELS: Record<SessionStep, string> = {
  clarify: "Clarify",
  edit: "Edit draft",
  similarity: "Similarity",
  optimize: "Optimize",
  export: "Export",
  complete: "Complete",
};

export function sessionStepIndex(step: SessionStep): number {
  return SESSION_STEPS.indexOf(step);
}

export function sessionStepForState(state: SessionState): SessionStep {
  switch (state) {
    case "intake":
    case "clarifying":
      return "clarify";
    case "edit":
      return "edit";
    case "similarity_check":
      return "similarity";
    case "optimization":
      return "optimize";
    case "approval":
    case "artifact_generation":
      return "export";
    case "exported":
      return "complete";
    default:
      return "edit";
  }
}

export function isSessionClosed(state: SessionState): boolean {
  return state === "exported";
}

export function sessionPath(sessionId: string, step: SessionStep): string {
  return `/sessions/${sessionId}/${step}`;
}

/** True when the user may open this step (current or earlier in the workflow). */
export function canVisitStep(target: SessionStep, state: SessionState): boolean {
  const targetIndex = sessionStepIndex(target);
  const currentIndex = sessionStepIndex(sessionStepForState(state));
  return targetIndex >= 0 && targetIndex <= currentIndex;
}

/** True when the requested step is ahead of session progress (should redirect forward). */
export function isStepAhead(target: SessionStep, state: SessionState): boolean {
  return sessionStepIndex(target) > sessionStepIndex(sessionStepForState(state));
}

export function formatSessionState(state: SessionState): string {
  return state.replaceAll("_", " ");
}

export function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

export function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}
