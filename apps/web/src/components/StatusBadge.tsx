import type { SessionState } from "../api/types";
import { formatSessionState } from "../lib/sessionRouting";

const STATE_LABELS: Partial<Record<SessionState, string>> = {
  intake: "Intake",
  clarifying: "Clarifying",
  edit: "Draft edit",
  similarity_check: "Similarity",
  optimization: "Optimize",
  approval: "Approved",
  exported: "Exported",
};

export function StatusBadge({ state }: { state: SessionState }) {
  return (
    <span className={`status-badge state-${state}`}>
      {STATE_LABELS[state] ?? formatSessionState(state)}
    </span>
  );
}
