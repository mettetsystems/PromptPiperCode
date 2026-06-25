import { useEffect, useMemo, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { formatApiError } from "../api/http";
import {
  queryKeys,
  useApplyPrecisionReplacement,
  useSession,
  useSuggestPrecisionReplacement,
} from "../api/hooks";
import { fetchPrecisionReview } from "../api/sessions";
import type { VagueLanguageFinding } from "../api/types";
import { formatPercent, sessionPath } from "../lib/sessionRouting";
import {
  DraftBlock,
  ErrorBanner,
  LoadingState,
  PageHeader,
  Panel,
} from "../components/ui";

interface PrecisionPageProps {
  sessionId: string;
}

export function PrecisionPage({ sessionId }: PrecisionPageProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const sessionQuery = useSession(sessionId);
  const precisionQuery = useQuery({
    queryKey: queryKeys.precisionReview(sessionId),
    queryFn: () => fetchPrecisionReview(sessionId),
    enabled: Boolean(sessionId) && sessionQuery.data?.session.state === "optimization",
  });

  const suggest = useSuggestPrecisionReplacement(sessionId);
  const apply = useApplyPrecisionReplacement(sessionId);

  const [index, setIndex] = useState(0);
  const [selected, setSelected] = useState<string>("");
  const [custom, setCustom] = useState("");

  const findings = precisionQuery.data?.findings ?? [];
  const current: VagueLanguageFinding | undefined = findings[index];

  useEffect(() => {
    if (!current) {
      return;
    }
    setSelected("");
    setCustom("");
    void suggest.mutateAsync(current.id).then((result) => {
      if (result.suggested_replacements.length > 0) {
        setSelected(result.suggested_replacements[0] ?? "");
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- refetch suggestions when finding changes
  }, [current?.id]);

  const replacement = useMemo(() => {
    if (custom.trim()) {
      return custom.trim();
    }
    return selected.trim();
  }, [custom, selected]);

  if (sessionQuery.isLoading || precisionQuery.isLoading) {
    return <LoadingState label="Loading precision review…" />;
  }

  if (sessionQuery.isError || !sessionQuery.data) {
    return (
      <div className="page narrow">
        <ErrorBanner message={formatApiError(sessionQuery.error, "Session unavailable.")} />
      </div>
    );
  }

  if (sessionQuery.data.session.state !== "optimization") {
    return <Navigate to={sessionPath(sessionId, "optimize")} replace />;
  }

  if (precisionQuery.isError || !precisionQuery.data) {
    return (
      <div className="page narrow">
        <ErrorBanner message={formatApiError(precisionQuery.error, "Precision review failed.")} />
      </div>
    );
  }

  const review = precisionQuery.data;

  if (!review.refinement_available) {
    return <Navigate to={sessionPath(sessionId, "optimize")} replace />;
  }

  const suggestError =
    suggest.error != null
      ? formatApiError(suggest.error, "Could not fetch replacement suggestions.")
      : null;
  const applyError =
    apply.error != null ? formatApiError(apply.error, "Could not apply replacement.") : null;

  const isBusy = suggest.isPending || apply.isPending;

  async function handleApply() {
    if (!current || !replacement) {
      return;
    }
    await apply.mutateAsync({ findingId: current.id, replacement });
    const refreshed = await queryClient.fetchQuery({
      queryKey: queryKeys.precisionReview(sessionId),
      queryFn: () => fetchPrecisionReview(sessionId),
    });
    if (refreshed.findings.length === 0) {
      navigate(sessionPath(sessionId, "optimize"));
      return;
    }
    if (index >= refreshed.findings.length) {
      setIndex(refreshed.findings.length - 1);
    }
  }

  if (findings.length === 0) {
    return (
      <div className="page">
        <PageHeader
          title="Semantic precision"
          subtitle="No vague language remains in the optimized prompt."
        />
        <Panel>
          <p>
            Semantic precision score: {formatPercent(review.score)} (threshold{" "}
            {formatPercent(review.threshold)}).
          </p>
          <Link className="button primary" to={sessionPath(sessionId, "optimize")}>
            Back to optimization
          </Link>
        </Panel>
      </div>
    );
  }

  return (
    <div className="page">
      <PageHeader
        title="Refine semantic precision"
        subtitle={`Finding ${index + 1} of ${findings.length} · score ${formatPercent(review.score)} · ${
          review.llm_available
            ? "model-ranked lexicon"
            : review.vector_index_available
              ? "vector lexicon"
              : "WordNet (CPU-only)"
        }`}
      />

      <Panel title="Line context">
        <DraftBlock body={current?.line ?? ""} label={`Line ${current?.line_number ?? ""}`} />
        <p className="muted">
          Vague {current?.category === "lazy_adjective" ? "adjective" : "noun"}:{" "}
          <strong>{current?.term}</strong>
        </p>
      </Panel>

      <Panel title="Choose a precise replacement">
        {suggestError && <ErrorBanner message={suggestError} />}
        {applyError && <ErrorBanner message={applyError} />}

        {suggest.data?.message && (
          <p className="muted">{suggest.data.message}</p>
        )}

        {suggest.data && suggest.data.suggested_replacements.length > 0 && (
          <div className="quick-replies" role="radiogroup" aria-label="Suggested replacements">
            {suggest.data.suggested_replacements.map((option) => (
              <button
                key={option}
                type="button"
                className={
                  selected === option && !custom.trim()
                    ? "button secondary is-selected"
                    : "button secondary"
                }
                disabled={isBusy}
                aria-pressed={selected === option && !custom.trim()}
                onClick={() => {
                  setSelected(option);
                  setCustom("");
                }}
              >
                {option}
              </button>
            ))}
          </div>
        )}

        <label className="field">
          <span>Or enter your own</span>
          <input
            type="text"
            className="input"
            value={custom}
            disabled={isBusy}
            placeholder="Your precise wording"
            onChange={(event) => {
              setCustom(event.target.value);
              setSelected("");
            }}
          />
        </label>

        <div className="button-row">
          <button
            type="button"
            className="button"
            disabled={isBusy || index === 0}
            onClick={() => setIndex((value) => Math.max(0, value - 1))}
          >
            Previous
          </button>
          <button
            type="button"
            className="button primary"
            disabled={isBusy || !replacement}
            onClick={() => void handleApply()}
          >
            {apply.isPending ? "Applying…" : "Apply and continue"}
          </button>
          <button
            type="button"
            className="button"
            disabled={isBusy || index >= findings.length - 1}
            onClick={() => setIndex((value) => Math.min(findings.length - 1, value + 1))}
          >
            Skip for now
          </button>
        </div>
      </Panel>

      <p className="muted">
        <Link to={sessionPath(sessionId, "optimize")}>Return to optimization</Link>
      </p>
    </div>
  );
}
