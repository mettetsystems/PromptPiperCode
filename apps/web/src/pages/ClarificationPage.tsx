import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { formatApiError } from "../api/http";
import type {
  AskTheLocalsResponse,
  ClarificationSuggestionsResponse,
  ClarificationVersionText,
  ClarificationVersionsSettings,
  QuickReplyGuide,
  SessionDetailResponse,
} from "../api/types";
import {
  useAnswerClarification,
  useAskTheLocals,
  useCompleteClarification,
  useSuggestClarification,
  useUserSettings,
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

const DEFAULT_VERSIONS: ClarificationVersionsSettings = {
  beginner: true,
  standard: true,
  advanced: true,
};

function isVersionEnabled(
  level: ClarificationVersionText["level"],
  availability: ClarificationVersionsSettings,
): boolean {
  const enabled = availability[level];
  if (availability.beginner || availability.standard || availability.advanced) {
    return enabled;
  }
  return level === "standard";
}

function BeginnerOptionGuides({ guides }: { guides: QuickReplyGuide[] }) {
  if (guides.length === 0) {
    return null;
  }
  return (
    <div className="option-guides">
      <p className="option-guides-title">What each default option means</p>
      <ul className="option-guide-list">
        {guides.map((guide) => (
          <li key={guide.option} className="option-guide-item">
            <p className="option-guide-option">{guide.option}</p>
            <p className="option-guide-explanation">{guide.explanation}</p>
            <p className="option-guide-when">
              <span className="clarification-rationale-label">Best when: </span>
              {guide.when_to_use}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}

function ClarificationVersionAccordions({
  versions,
  availability,
  questionNumber,
  totalQuestions,
  questionKey,
  optionGuides,
}: {
  versions: ClarificationVersionText[];
  availability: ClarificationVersionsSettings;
  questionNumber: number;
  totalQuestions: number;
  questionKey: string;
  optionGuides: QuickReplyGuide[];
}) {
  const visible = versions.filter((version) => isVersionEnabled(version.level, availability));
  const [openLevels, setOpenLevels] = useState<Record<string, boolean>>({
    beginner: false,
    standard: true,
    advanced: false,
  });

  useEffect(() => {
    setOpenLevels({ beginner: false, standard: true, advanced: false });
  }, [questionKey]);

  return (
    <div className="clarification-versions" role="group" aria-label="Question wording versions">
      <p className="muted clarification-versions-meta">
        Quick question {questionNumber} of {totalQuestions}
      </p>
      {visible.map((version) => (
        <details
          key={version.level}
          className="clarification-version"
          open={openLevels[version.level] ?? false}
          onToggle={(event) => {
            const isOpen = event.currentTarget.open;
            setOpenLevels((current) => ({ ...current, [version.level]: isOpen }));
          }}
        >
          <summary>
            <span className="clarification-version-label">{version.label}</span>
          </summary>
          <div className="clarification-version-body">
            <p className="question-text">{version.prompt}</p>
            {version.rationale && (
              <p className="clarification-rationale">
                <span className="clarification-rationale-label">Why this matters: </span>
                {version.rationale}
              </p>
            )}
            {version.level === "beginner" && <BeginnerOptionGuides guides={optionGuides} />}
          </div>
        </details>
      ))}
    </div>
  );
}

export function ClarificationPage({ sessionId, session, readOnly = false }: ClarificationPageProps) {
  const answer = useAnswerClarification(sessionId);
  const complete = useCompleteClarification(sessionId);
  const suggest = useSuggestClarification(sessionId);
  const locals = useAskTheLocals(sessionId);
  const userSettings = useUserSettings();
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
  const [localsInsight, setLocalsInsight] = useState<AskTheLocalsResponse | null>(null);
  const [localsCopied, setLocalsCopied] = useState(false);

  const questionKey = `${session.clarification_question_number ?? 0}:${session.clarification_field ?? ""}`;

  useEffect(() => {
    setSelectedOptions([]);
    setCustomAnswer("");
    setModelSuggestions(null);
    setLocalsInsight(null);
    setLocalsCopied(false);
  }, [questionKey]);

  const questionNumber = session.clarification_question_number ?? 1;
  const totalQuestions = session.clarification_total_questions ?? 15;
  const canFinish = session.clarification_can_finish ?? false;
  const isBusy =
    answer.isPending || complete.isPending || suggest.isPending || locals.isPending;
  const combinedAnswer = buildClarificationAnswer(selectedOptions, customAnswer);
  const canSubmit = combinedAnswer !== null;
  const modelEnabled = llmHealth.data?.llm_enabled === true && llmHealth.data.status === "ok";
  const localsOverrideActive = userSettings.data?.ask_the_locals_override_active === true;
  // Keep Ask The Locals clickable whenever AI assistance is on. The API returns a
  // guide-based recommendation when the model is down, and the dedicated Ask The
  // Locals override works even if the setup-wizard local model is offline.
  const localsEnabled = userSettings.data?.llm_enabled !== false;
  const availability = userSettings.data?.clarification_versions ?? DEFAULT_VERSIONS;
  const versions = useMemo(
    () => session.clarification_versions ?? [],
    [session.clarification_versions],
  );
  const optionGuides = useMemo(
    () => session.clarification_quick_reply_guides ?? [],
    [session.clarification_quick_reply_guides],
  );
  const hasVersions = versions.length > 0;

  async function submitAnswer(value: string) {
    if (!value.trim()) {
      return;
    }
    setSelectedOptions([]);
    setCustomAnswer("");
    setModelSuggestions(null);
    setLocalsInsight(null);
    await answer.mutateAsync(value.trim());
  }

  async function requestModelSuggestions() {
    const result = await suggest.mutateAsync();
    setModelSuggestions(result);
  }

  async function requestLocalsInsight() {
    const result = await locals.mutateAsync();
    setLocalsInsight(result);
    setLocalsCopied(false);
  }

  async function copyLocalsRecommendation(text: string) {
    if (!text.trim()) {
      return;
    }
    try {
      await navigator.clipboard.writeText(text);
      setLocalsCopied(true);
      window.setTimeout(() => setLocalsCopied(false), 2000);
    } catch {
      setLocalsCopied(false);
    }
  }

  const localsCopyText =
    localsInsight?.recommended_answer?.trim() || localsInsight?.insight?.trim() || "";
  const localsHasInsight =
    Boolean(localsInsight?.insight?.trim()) &&
    localsInsight?.insight?.trim() !== localsCopyText;

  const errorMessage =
    locals.error != null
      ? formatApiError(locals.error, "Ask The Locals failed.")
      : suggest.error != null
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
            {!readOnly && hasVersions && (
              <ClarificationVersionAccordions
                versions={versions}
                availability={availability}
                questionNumber={questionNumber}
                totalQuestions={totalQuestions}
                questionKey={questionKey}
                optionGuides={optionGuides}
              />
            )}
            {!readOnly && !hasVersions && session.clarification_question && (
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
                : "Pick quick replies and/or add custom text, then submit. Expand Beginner for option guides, or Ask The Locals for a contextual recommendation under your custom answer."}
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
                    disabled={isBusy || !localsEnabled}
                    title={
                      localsEnabled
                        ? localsOverrideActive
                          ? "Ask your configured Ask The Locals model for a contextual recommendation based on prior answers"
                          : modelEnabled
                            ? "Ask the current AI tooling model for a contextual recommendation based on prior answers"
                            : "Ask for a recommendation (uses the model when available, otherwise guide-based defaults)"
                        : "Turn on Enable AI assistance in Settings to use Ask The Locals"
                    }
                    onClick={() => void requestLocalsInsight()}
                  >
                    {locals.isPending ? "Asking locals…" : "Ask The Locals"}
                  </button>
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
                {localsInsight && (
                  <div className="locals-insight locals-copy-window" aria-live="polite">
                    <div className="locals-copy-header">
                      <div>
                        <p className="locals-copy-title">Ask The Locals recommendation</p>
                        <p className="muted locals-copy-meta">
                          {localsInsight.message ??
                            (localsInsight.model_available
                              ? "Contextual recommendation"
                              : "Ask The Locals unavailable.")}
                          {localsInsight.model_source ? ` · ${localsInsight.model_source}` : ""}
                          {localsInsight.previous_answers_used.length > 0
                            ? ` · grounded in ${localsInsight.previous_answers_used.length} prior answer${
                                localsInsight.previous_answers_used.length === 1 ? "" : "s"
                              }`
                            : ""}
                        </p>
                      </div>
                      <div className="button-row locals-copy-actions">
                        <button
                          type="button"
                          className="button secondary"
                          disabled={!localsCopyText}
                          onClick={() => void copyLocalsRecommendation(localsCopyText)}
                        >
                          {localsCopied ? "Copied" : "Copy"}
                        </button>
                        <button
                          type="button"
                          className="button secondary"
                          disabled={!localsCopyText || selectedOptions.includes("unspecified")}
                          onClick={() => setCustomAnswer(localsCopyText)}
                        >
                          Use in custom answer
                        </button>
                      </div>
                    </div>
                    {localsCopyText ? (
                      <textarea
                        className="locals-copy-text"
                        rows={4}
                        readOnly
                        value={localsCopyText}
                        aria-label="Ask The Locals copyable recommendation"
                      />
                    ) : (
                      <p className="muted">No recommendation text was returned.</p>
                    )}
                    {localsHasInsight && (
                      <p className="locals-insight-body">{localsInsight.insight}</p>
                    )}
                  </div>
                )}
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
