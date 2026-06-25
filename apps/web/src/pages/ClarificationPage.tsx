import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { formatApiError } from "../api/http";
import type { ClarificationSuggestionsResponse, SessionDetailResponse } from "../api/types";
import {
  useAnswerClarification,
  useCompleteClarification,
  useSuggestClarification,
} from "../api/hooks";
import { fetchLlmHealth } from "../api/sessions";
import {
  buildClarificationAnswer,
  toggleClarificationOption,
} from "../lib/clarificationAnswer";
import { RequirementCardPanel } from "../components/RequirementCardPanel";
import { DraftBlock, ErrorBanner, PageHeader, Panel } from "../components/ui";

interface ClarificationPageProps {
  sessionId: string;
  session: SessionDetailResponse;
  readOnly?: boolean;
}

export function ClarificationPage({ sessionId, session, readOnly = false }: ClarificationPageProps) {
  const answer = useAnswerClarification(sessionId);
  const complete = useCompleteClarification(sessionId);
  const suggest = useSuggestClarification(sessionId);
  const llmHealth = useQuery({
    queryKey: ["health", "llm"],
    queryFn: fetchLlmHealth,
    staleTime: 15_000,
  });
  const [selectedOptions, setSelectedOptions] = useState<string[]>([]);
  const [customAnswer, setCustomAnswer] = useState("");
  const [modelSuggestions, setModelSuggestions] = useState<ClarificationSuggestionsResponse | null>(
    null,
  );

  const questionKey = `${session.clarification_question_number ?? 0}:${session.clarification_field ?? ""}`;

  useEffect(() => {
    setSelectedOptions([]);
    setCustomAnswer("");
    setModelSuggestions(null);
  }, [questionKey]);

  const questionNumber = session.clarification_question_number ?? 1;
  const totalQuestions = session.clarification_total_questions ?? 15;
  const canFinish = session.clarification_can_finish ?? false;
  const isBusy = answer.isPending || complete.isPending || suggest.isPending;
  const combinedAnswer = buildClarificationAnswer(selectedOptions, customAnswer);
  const canSubmit = combinedAnswer !== null;
  const modelEnabled = llmHealth.data?.llm_enabled === true && llmHealth.data.status === "ok";

  async function submitAnswer(value: string) {
    if (!value.trim()) {
      return;
    }
    setSelectedOptions([]);
    setCustomAnswer("");
    setModelSuggestions(null);
    await answer.mutateAsync(value.trim());
  }

  async function requestModelSuggestions() {
    const result = await suggest.mutateAsync();
    setModelSuggestions(result);
  }

  const errorMessage =
    suggest.error != null
      ? formatApiError(suggest.error, "Could not fetch model suggestions.")
      : answer.error != null
        ? formatApiError(answer.error, "Clarification action failed.")
        : complete.error != null
          ? formatApiError(complete.error, "Clarification action failed.")
          : null;

  return (
    <div className="page">
      <PageHeader
        title="Clarification"
        subtitle={
          readOnly
            ? "Captured requirement answers for this session"
            : `Field ${questionNumber} of up to ${totalQuestions} — CPU-fast by default`
        }
      />
      <div className="grid-workflow">
        <div className="workflow-main stack-form">
          <Panel>
            {!readOnly && session.clarification_question && (
              <p className="question-text">{session.clarification_question}</p>
            )}
            {modelSuggestions?.suggested_question && (
              <p className="muted model-suggested-question">
                Model rephrase: {modelSuggestions.suggested_question}
              </p>
            )}
            {session.clarification_field && !readOnly && (
              <p className="muted">
                Field: <code>{session.clarification_field}</code>
              </p>
            )}
            <p className="muted">
              {readOnly
                ? "Review the requirement card for answers captured during clarification."
                : "Pick quick replies and/or add custom text, then submit. Optionally ask the model for tailored suggestions when you want help."}
            </p>
            {!readOnly && (
              <>
                <div className="quick-replies" role="group" aria-label="Quick reply options">
                  {(session.clarification_quick_replies ?? []).map((option) => {
                    const isSelected = selectedOptions.includes(option);
                    return (
                      <button
                        key={option}
                        type="button"
                        className={isSelected ? "button secondary is-selected" : "button secondary"}
                        disabled={isBusy}
                        aria-pressed={isSelected}
                        onClick={() =>
                          setSelectedOptions((current) =>
                            toggleClarificationOption(current, option),
                          )
                        }
                      >
                        {option}
                      </button>
                    );
                  })}
                </div>
                <div className="button-row">
                  <button
                    type="button"
                    className="button secondary"
                    disabled={isBusy || !modelEnabled}
                    title={
                      modelEnabled
                        ? "Ask the local model for contextual answer suggestions"
                        : "Model unavailable — use quick replies or custom text"
                    }
                    onClick={() => void requestModelSuggestions()}
                  >
                    {suggest.isPending ? "Querying model…" : "Get model suggestions"}
                  </button>
                </div>
                {modelSuggestions && (
                  <div className="model-suggestions">
                    <p className="muted">
                      {modelSuggestions.message ??
                        (modelSuggestions.model_available
                          ? "Select any model suggestions below."
                          : "Model suggestions unavailable.")}
                    </p>
                    {modelSuggestions.suggested_answers.length > 0 && (
                      <div className="quick-replies" role="group" aria-label="Model suggestions">
                        {modelSuggestions.suggested_answers.map((option) => {
                          const isSelected = selectedOptions.includes(option);
                          return (
                            <button
                              key={option}
                              type="button"
                              className={
                                isSelected
                                  ? "button secondary is-selected is-model"
                                  : "button secondary is-model"
                              }
                              disabled={isBusy}
                              aria-pressed={isSelected}
                              onClick={() =>
                                setSelectedOptions((current) =>
                                  toggleClarificationOption(current, option),
                                )
                              }
                            >
                              {option}
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}
                <label className="field">
                  <span>Custom answer (optional)</span>
                  <textarea
                    rows={3}
                    value={customAnswer}
                    onChange={(event) => setCustomAnswer(event.target.value)}
                    placeholder="Add details or combine with the options above"
                    disabled={selectedOptions.includes("unspecified")}
                  />
                </label>
                {errorMessage && <ErrorBanner message={errorMessage} />}
                <div className="button-row">
                  <button
                    type="button"
                    className="button primary"
                    disabled={isBusy || !canSubmit}
                    onClick={() => combinedAnswer && void submitAnswer(combinedAnswer)}
                  >
                    {answer.isPending ? "Submitting…" : "Submit answer"}
                  </button>
                  {canFinish && (
                    <button
                      type="button"
                      className="button secondary"
                      disabled={isBusy}
                      onClick={() => void complete.mutateAsync()}
                    >
                      {complete.isPending ? "Generating…" : "Generate draft now"}
                    </button>
                  )}
                </div>
              </>
            )}
          </Panel>
          {session.current_draft && (
            <Panel title="Draft preview">
              <DraftBlock body={session.current_draft.body} />
            </Panel>
          )}
        </div>
        <RequirementCardPanel card={session.requirement_card} />
      </div>
    </div>
  );
}
