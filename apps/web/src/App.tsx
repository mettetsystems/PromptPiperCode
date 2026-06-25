import { useQuery } from "@tanstack/react-query";
import { APP_NAME, LOCAL_FIRST_NOTICE, type HealthResponse } from "@prompt-piper/shared";
import { fetchHealth } from "./api/health";
import "./App.css";

function App() {
  const healthQuery = useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: fetchHealth,
  });

  return (
    <div className="app">
      <header className="app-header">
        <p className="eyebrow">Local-first prompt engineering</p>
        <h1>{APP_NAME}</h1>
        <p className="subtitle">
          Design, clarify, edit, finalize, optimize, store, and retrieve prompts — on your machine.
        </p>
      </header>

      <section className="panel">
        <h2>Workbench shell</h2>
        <p className="notice">{LOCAL_FIRST_NOTICE}</p>

        <div className="status-card">
          <h3>API status</h3>
          {healthQuery.isLoading && <p>Checking local API…</p>}
          {healthQuery.isError && (
            <p className="error">
              Local API unavailable. Start it with <code>make dev-api</code>.
            </p>
          )}
          {healthQuery.data && (
            <dl>
              <div>
                <dt>Status</dt>
                <dd>{healthQuery.data.status}</dd>
              </div>
              <div>
                <dt>Version</dt>
                <dd>{healthQuery.data.version}</dd>
              </div>
              <div>
                <dt>Environment</dt>
                <dd>{healthQuery.data.environment}</dd>
              </div>
              <div>
                <dt>Database</dt>
                <dd>{healthQuery.data.database}</dd>
              </div>
            </dl>
          )}
        </div>
      </section>
    </div>
  );
}

export default App;
