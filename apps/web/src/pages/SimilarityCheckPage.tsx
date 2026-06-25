import { Link } from "react-router-dom";
import type { SessionDetailResponse } from "../api/types";
import { ApiError, formatApiError } from "../api/http";
import { useOptimizeSession } from "../api/hooks";
import { PageHeader, Panel, WarningBanner, DraftBlock, ErrorBanner } from "../components/ui";

interface SimilarityCheckPageProps {
  sessionId: string;
  session: SessionDetailResponse;
  readOnly?: boolean;
}

export function SimilarityCheckPage({
  sessionId,
  session,
  readOnly = false,
}: SimilarityCheckPageProps) {
  const optimize = useOptimizeSession(sessionId);
  const topMatch = session.similarity_matches[0];
  const hasWarning = Boolean(session.similarity_warning);
  const optimizeError =
    optimize.error instanceof ApiError
      ? formatApiError(optimize.error)
      : optimize.error
        ? "Optimization failed."
        : null;

  return (
    <div className="page">
      <PageHeader
        title="Similarity check"
        subtitle="Compare this prompt against indexed patterns in the local registry before optimization."
      />

      {optimizeError && <ErrorBanner message={optimizeError} />}

      {hasWarning && session.similarity_warning && (
        <WarningBanner message={session.similarity_warning} />
      )}

      <div className="grid-two">
        <Panel title="Current canonical draft">
          {session.current_draft ? (
            <DraftBlock body={session.current_draft.body} label="Canonical" />
          ) : (
            <p className="muted">No draft loaded.</p>
          )}
          {session.prompt_id && (
            <p className="muted">
              Registry ID: <code>{session.prompt_id}</code>
            </p>
          )}
        </Panel>

        <Panel title="Similar matches">
          {session.similarity_matches.length === 0 ? (
            <p className="muted">No close matches found in the local index.</p>
          ) : (
            <ul className="item-list">
              {session.similarity_matches.map((match) => (
                <li key={`${match.prompt_id}-${match.document_kind ?? "unknown"}`}>
                  <div className="item-row">
                    <div>
                      <strong>{match.title}</strong>
                      <p className="item-meta">
                        <code>{match.prompt_id}</code> · score{" "}
                        {Math.round(match.similarity_score * 100)}%
                      </p>
                      {match.artifact_paths.canonical_txt && (
                        <p className="item-meta">
                          Artifact: <code>{match.artifact_paths.canonical_txt}</code>
                        </p>
                      )}
                      {match.delta && <p className="muted">{match.delta}</p>}
                    </div>
                    <Link to={`/registry/${match.prompt_id}`} className="button secondary">
                      Review
                    </Link>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>

      {!readOnly && (
      <Panel title="Next step">
        {topMatch && hasWarning ? (
          <p>
            A similar pattern exists for <code>{topMatch.prompt_id}</code>. Review it or continue
            to token optimization.
          </p>
        ) : (
          <p>No blocking similarity issues detected. Continue to optimization.</p>
        )}
        <div className="form-actions">
          {topMatch && (
            <Link to={`/registry/${topMatch.prompt_id}`} className="button secondary">
              Review matched prompt
            </Link>
          )}
          <button
            type="button"
            className="button primary"
            disabled={optimize.isPending}
            onClick={() => void optimize.mutateAsync()}
          >
            {optimize.isPending ? "Starting optimization…" : "Continue to optimization"}
          </button>
        </div>
      </Panel>
      )}
    </div>
  );
}
