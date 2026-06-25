import { useState } from "react";
import { ApiError } from "../api/http";
import type { SessionDetailResponse } from "../api/types";
import { useEditDraft, useFinalizeSession } from "../api/hooks";
import { RequirementCardPanel } from "../components/RequirementCardPanel";
import {
  DraftBlock,
  ErrorBanner,
  PageHeader,
  Panel,
  WarningBanner,
} from "../components/ui";

interface DraftEditorPageProps {
  sessionId: string;
  session: SessionDetailResponse;
  readOnly?: boolean;
}

export function DraftEditorPage({ sessionId, session, readOnly = false }: DraftEditorPageProps) {
  const editDraft = useEditDraft(sessionId);
  const finalize = useFinalizeSession(sessionId);
  const [instruction, setInstruction] = useState("");

  const draft = session.current_draft;
  const unresolved = session.requirement_card.unresolved_fields;

  async function handleEdit(event: React.FormEvent) {
    event.preventDefault();
    if (!instruction.trim()) {
      return;
    }
    await editDraft.mutateAsync(instruction.trim());
    setInstruction("");
  }

  const editError =
    editDraft.error instanceof ApiError ? editDraft.error.message : editDraft.error ? "Edit failed." : null;
  const finalizeError =
    finalize.error instanceof ApiError
      ? finalize.error.message
      : finalize.error
        ? "Finalization failed."
        : null;

  return (
    <div className="page">
      <PageHeader
        title="Draft editor"
        subtitle="Revise the draft with natural-language instructions, then finalize to write the canonical prompt to the registry."
      />
      <div className="grid-workflow">
        <div className="workflow-main stack-form">
          {draft ? (
            <Panel title={`Draft v${draft.version}`}>
              <DraftBlock body={draft.body} />
              {draft.change_summary && <p className="muted">{draft.change_summary}</p>}
            </Panel>
          ) : (
            <Panel>
              <p className="muted">No draft available yet.</p>
            </Panel>
          )}

          {!readOnly && (
          <Panel title="Edit instruction">
            <form className="stack-form" onSubmit={handleEdit}>
              <label className="field">
                <span>Instruction</span>
                <textarea
                  rows={4}
                  value={instruction}
                  onChange={(event) => setInstruction(event.target.value)}
                  placeholder="Example: Change tone to analytical and tighten the output contract."
                />
              </label>
              {editError && <ErrorBanner message={editError} />}
              <button
                type="submit"
                className="button secondary"
                disabled={editDraft.isPending || !instruction.trim()}
              >
                {editDraft.isPending ? "Applying…" : "Submit change"}
              </button>
            </form>
          </Panel>
          )}

          {(session.semantic_diff || session.change_summary) && (
            <Panel title="Semantic diff">
              {session.change_summary && <p>{session.change_summary}</p>}
              {session.semantic_diff && <pre className="diff-text">{session.semantic_diff}</pre>}
              {session.edit_intent && (
                <p className="muted">
                  Intent: <code>{session.edit_intent}</code>
                </p>
              )}
            </Panel>
          )}

          {unresolved.length > 0 && (
            <WarningBanner message={`Unresolved fields: ${unresolved.join(", ")}`} />
          )}

          {!readOnly && (
          <Panel title="Finalize">
            <p className="muted">
              Finalization freezes the canonical draft and writes registry files under{" "}
              <code>data/registry/</code>.
            </p>
            {finalizeError && <ErrorBanner message={finalizeError} />}
            <button
              type="button"
              className="button primary"
              disabled={finalize.isPending || !draft}
              onClick={() => void finalize.mutateAsync()}
            >
              {finalize.isPending ? "Finalizing…" : "Finalize prompt"}
            </button>
          </Panel>
          )}
        </div>
        <RequirementCardPanel card={session.requirement_card} />
      </div>
    </div>
  );
}
