import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useRegistryPrompts } from "../api/hooks";
import { formatApiError } from "../api/http";
import { filterRegistryPrompts } from "../lib/registrySearch";
import { formatDate } from "../lib/sessionRouting";
import { ErrorBanner, LoadingState, PageHeader, Panel } from "../components/ui";

export function RegistryPage() {
  const registry = useRegistryPrompts();
  const [searchParams] = useSearchParams();
  const [registrySearch, setRegistrySearch] = useState(() => searchParams.get("q") ?? "");

  const filteredPrompts = useMemo(
    () => filterRegistryPrompts(registry.data ?? [], registrySearch),
    [registry.data, registrySearch],
  );
  const searchActive = registrySearch.trim().length > 0;
  const totalCount = registry.data?.length ?? 0;

  return (
    <div className="page">
      <PageHeader
        title="Registry"
        subtitle="Browse finalized prompts stored under data/registry on this machine."
      />
      <Panel>
        {registry.isLoading && <LoadingState label="Loading registry…" />}
        {registry.isError && (
          <ErrorBanner message={formatApiError(registry.error, "Could not load registry.")} />
        )}
        {registry.data && totalCount === 0 && (
          <p className="muted">No finalized prompts yet.</p>
        )}
        {totalCount > 0 && (
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
        {searchActive && totalCount > 0 && (
          <p className="muted panel-search-meta">
            Showing {filteredPrompts.length} of {totalCount} prompts
          </p>
        )}
        {totalCount > 0 && filteredPrompts.length === 0 && (
          <p className="muted">No finalized prompts match your search.</p>
        )}
        {filteredPrompts.length > 0 && (
          <table className="data-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Prompt ID</th>
                <th>Version</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {filteredPrompts.map((prompt) => (
                <tr key={prompt.prompt_id}>
                  <td>
                    <Link to={`/registry/${prompt.prompt_id}`} className="text-link">
                      {prompt.title}
                    </Link>
                  </td>
                  <td>
                    <code>{prompt.prompt_id}</code>
                  </td>
                  <td>{prompt.version}</td>
                  <td>{formatDate(prompt.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>
    </div>
  );
}
