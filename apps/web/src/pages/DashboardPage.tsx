import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import {
  queryKeys,
  useDeleteSession,
  useRegistryPrompts,
  useUpdateUserSettings,
  useUserSettings,
} from "../api/hooks";
import { formatApiError } from "../api/http";
import type { RecentSessionEntry } from "../api/types";
import { filterRegistryPrompts } from "../lib/registrySearch";
import { loadRecentSessions } from "../lib/recentSessions";
import { formatDate, sessionPath, sessionStepForState } from "../lib/sessionRouting";
import { ErrorBanner, LoadingState, PageHeader, Panel, WarningBanner } from "../components/ui";
import { StatusBadge } from "../components/StatusBadge";

export function DashboardPage() {
  const recent = useQuery({
    queryKey: queryKeys.recentSessions,
    queryFn: loadRecentSessions,
    staleTime: 0,
  });
  const registry = useRegistryPrompts();
  const userSettings = useUserSettings();
  const saveSettings = useUpdateUserSettings();
  const deleteSession = useDeleteSession();
  const [registrySearch, setRegistrySearch] = useState("");
  const [deleteError, setDeleteError] = useState<string | null>(null);

  async function handleDeleteSession(session: RecentSessionEntry) {
    const confirmed = window.confirm(
      `Delete “${session.title}”? This removes the session from this machine. Finalized registry prompts are kept.`,
    );
    if (!confirmed) {
      return;
    }
    setDeleteError(null);
    try {
      await deleteSession.mutateAsync(session.id);
    } catch (error) {
      setDeleteError(formatApiError(error, "Could not delete session."));
    }
  }

  const configuredEndpoints = useMemo(
    () => userSettings.data?.api_endpoints.filter((endpoint) => endpoint.configured) ?? [],
    [userSettings.data],
  );

  const sessionsWithWarnings = useMemo(
    () => (recent.data ?? []).filter((item) => item.similarityWarning),
    [recent.data],
  );

  const filteredRegistryPrompts = useMemo(
    () => filterRegistryPrompts(registry.data ?? [], registrySearch),
    [registry.data, registrySearch],
  );

  const visibleRegistryPrompts = filteredRegistryPrompts.slice(0, 8);
  const registrySearchActive = registrySearch.trim().length > 0;

  return (
    <div className="page">
      <PageHeader
        title="Dashboard"
        subtitle="Recent design sessions and finalized prompts on this machine."
        actions={
          <Link to="/sessions/new" className="button primary">
            New session
          </Link>
        }
      />

      {sessionsWithWarnings.length > 0 && (
        <WarningBanner
          message={`${sessionsWithWarnings.length} recent session(s) reported similarity warnings.`}
        />
      )}

      {configuredEndpoints.length > 0 && (
        <Panel title="Default external API">
          <label className="field">
            <span>Used for send-to-model unless overridden on the Complete step</span>
            <select
              className="select-input"
              value={userSettings.data?.default_api_endpoint_id ?? ""}
              disabled={!userSettings.data || saveSettings.isPending}
              onChange={(event) => {
                const value = event.target.value || null;
                if (!userSettings.data) {
                  return;
                }
                void saveSettings.mutateAsync({
                  llm_enabled: userSettings.data.llm_enabled,
                  precision_warning_threshold: userSettings.data.precision_warning_threshold,
                  similarity_time_scope_index: userSettings.data.similarity_time_scope_index,
                  clarification_versions: userSettings.data.clarification_versions,
                  default_api_endpoint_id: value,
                  ai_tooling_api_override: {
                    label: userSettings.data.ai_tooling_api_override.label,
                    base_url: userSettings.data.ai_tooling_api_override.base_url,
                    chat_model: userSettings.data.ai_tooling_api_override.chat_model,
                  },
                  ask_the_locals_api_override: {
                    label: userSettings.data.ask_the_locals_api_override.label,
                    base_url: userSettings.data.ask_the_locals_api_override.base_url,
                    chat_model: userSettings.data.ask_the_locals_api_override.chat_model,
                  },
                  api_endpoints: userSettings.data.api_endpoints.map((endpoint) => ({
                    id: endpoint.id,
                    label: endpoint.label,
                    base_url: endpoint.base_url,
                    chat_model: endpoint.chat_model,
                  })),
                });
              }}
            >
              <option value="">Select an endpoint</option>
              {configuredEndpoints.map((endpoint) => (
                <option key={endpoint.id} value={endpoint.id}>
                  {endpoint.label || endpoint.chat_model || endpoint.base_url}
                </option>
              ))}
            </select>
          </label>
        </Panel>
      )}

      <div className="grid-two">
        <Panel title="Recent sessions">
          {recent.isLoading && <LoadingState label="Loading recent sessions…" />}
          {recent.isError && (
            <ErrorBanner message={formatApiError(recent.error, "Could not load recent sessions.")} />
          )}
          {deleteError && <ErrorBanner message={deleteError} />}
          {!recent.isLoading && !recent.isError && (recent.data ?? []).length === 0 && (
            <p className="muted">No sessions tracked yet. Start a new prompt design session.</p>
          )}
          {!recent.isLoading && !recent.isError && (recent.data ?? []).length > 0 && (
            <ul className="item-list">
              {(recent.data ?? []).map((session) => (
                <li key={session.id}>
                  <div className="item-row">
                    <div>
                      <Link
                        to={sessionPath(session.id, sessionStepForState(session.state))}
                        className="item-title"
                      >
                        {session.title}
                      </Link>
                      <p className="item-meta">
                        Updated {formatDate(session.updatedAt)}
                        {session.promptId && (
                          <>
                            {" · "}
                            <code>{session.promptId}</code>
                          </>
                        )}
                      </p>
                      {session.similarityWarning && (
                        <p className="item-warn">{session.similarityWarning}</p>
                      )}
                    </div>
                    <div className="item-actions">
                      <StatusBadge state={session.state} />
                      <button
                        type="button"
                        className="button compact"
                        disabled={deleteSession.isPending && deleteSession.variables === session.id}
                        aria-label={`Delete session ${session.title}`}
                        onClick={() => {
                          void handleDeleteSession(session);
                        }}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel title="Finalized prompts">
          {registry.isLoading && <LoadingState label="Loading registry…" />}
          {registry.isError && (
            <ErrorBanner message={formatApiError(registry.error, "Registry unavailable.")} />
          )}
          {registry.data && registry.data.length > 0 && (
            <label className="field panel-search">
              <span className="sr-only">Search finalized prompts</span>
              <input
                type="search"
                className="select-input"
                placeholder="Search by title, prompt ID, abstract, or tags…"
                value={registrySearch}
                onChange={(event) => setRegistrySearch(event.target.value)}
                aria-label="Search finalized prompts"
              />
            </label>
          )}
          {registry.data && registry.data.length === 0 && (
            <p className="muted">No finalized prompts in the local registry yet.</p>
          )}
          {registry.data && registry.data.length > 0 && filteredRegistryPrompts.length === 0 && (
            <p className="muted">No finalized prompts match your search.</p>
          )}
          {visibleRegistryPrompts.length > 0 && (
            <ul className="item-list">
              {visibleRegistryPrompts.map((prompt) => (
                <li key={prompt.prompt_id}>
                  <div className="item-row">
                    <div>
                      <Link to={`/registry/${prompt.prompt_id}`} className="item-title">
                        {prompt.title}
                      </Link>
                      <p className="item-meta">
                        <code>{prompt.prompt_id}</code>
                        {prompt.abstract && <> · {prompt.abstract}</>}
                      </p>
                    </div>
                    <span className="muted">v{prompt.version}</span>
                  </div>
                </li>
              ))}
            </ul>
          )}
          {registry.data && registry.data.length > 0 && filteredRegistryPrompts.length > 8 && (
            <Link
              to={`/registry${registrySearchActive ? `?q=${encodeURIComponent(registrySearch.trim())}` : ""}`}
              className="text-link"
            >
              View all {filteredRegistryPrompts.length} matching prompts
            </Link>
          )}
          {registry.data &&
            registry.data.length > 8 &&
            !registrySearchActive &&
            filteredRegistryPrompts.length <= 8 && (
            <Link to="/registry" className="text-link">
              View all {registry.data.length} prompts
            </Link>
          )}
        </Panel>
      </div>
    </div>
  );
}
