import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { formatApiError } from "../api/http";
import { useCreateSession } from "../api/hooks";
import { sessionPath, sessionStepForState } from "../lib/sessionRouting";
import { ErrorBanner, PageHeader, Panel } from "../components/ui";

export function NewSessionPage() {
  const navigate = useNavigate();
  const createSession = useCreateSession();
  const [request, setRequest] = useState("");
  const [title, setTitle] = useState("");

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!request.trim()) {
      return;
    }
    try {
      const data = await createSession.mutateAsync({
        initial_request: request.trim(),
        title: title.trim() || undefined,
      });
      navigate(sessionPath(data.session.id, sessionStepForState(data.session.state)));
    } catch {
      // surfaced below
    }
  }

  const errorMessage =
    createSession.error != null
      ? formatApiError(createSession.error, "Failed to create session.")
      : null;

  return (
    <div className="page narrow">
      <PageHeader
        title="New session"
        subtitle="Describe the coding prompt you want to design. PromptPiperCode will extract six coding dimensions and ask clarifying questions."
      />
      <Panel>
        <form className="stack-form" onSubmit={handleSubmit}>
          <label className="field">
            <span>Initial request</span>
            <textarea
              rows={8}
              value={request}
              onChange={(event) => setRequest(event.target.value)}
              placeholder="Example: Write a prompt for implementing a FastAPI endpoint with Pydantic v2 models, matching existing service patterns, returning typed JSON, with pytest coverage."
              required
            />
          </label>
          <label className="field">
            <span>Title (optional)</span>
            <input
              type="text"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="FastAPI feature coding prompt"
            />
          </label>
          {errorMessage && <ErrorBanner message={errorMessage} />}
          <div className="form-actions">
            <button type="submit" className="button primary" disabled={createSession.isPending}>
              {createSession.isPending ? "Creating…" : "Create session"}
            </button>
          </div>
        </form>
      </Panel>
    </div>
  );
}
