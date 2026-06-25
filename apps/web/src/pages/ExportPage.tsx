import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { formatApiError } from "../api/http";
import type { SendToInferenceResponse, SessionDetailResponse } from "../api/types";
import { queryKeys, useGenerateArtifacts, useSendToInference } from "../api/hooks";
import { fetchInferenceSettings, fetchLlmHealth } from "../api/sessions";
import { buildExportFolderPreview } from "../lib/exportFolder";
import { sessionPath, sessionStepForState } from "../lib/sessionRouting";
import { DraftBlock, ErrorBanner, PageHeader, Panel, WarningBanner } from "../components/ui";
import { SessionTemplateButton } from "../components/SessionTemplateButton";

interface ExportPageProps {
  sessionId: string;
  session: SessionDetailResponse;
  readOnly?: boolean;
}

export function ExportPage({ sessionId, session, readOnly = false }: ExportPageProps) {
  const navigate = useNavigate();
  const generate = useGenerateArtifacts(sessionId);
  const defaultFolderLabel = session.session.title;
  const [folderLabel, setFolderLabel] = useState(defaultFolderLabel);
  const folderPreview = useMemo(
    () => buildExportFolderPreview(folderLabel || defaultFolderLabel),
    [defaultFolderLabel, folderLabel],
  );

  const errorMessage =
    generate.error != null
      ? formatApiError(generate.error, "Artifact generation failed.")
      : null;

  return (
    <div className="page">
      <PageHeader
        title="Export artifacts"
        subtitle="Generate stable local artifacts from the approved canonical and optimized prompts."
      />

      {session.registry_warning && <WarningBanner message={session.registry_warning} />}

      <Panel>
        <p>
          Prompt ID: <code>{session.prompt_id ?? session.session.prompt_id}</code>
        </p>
        <p className="muted">
          Artifacts are written under the configured export root (native dev:{" "}
          <code>./data/artifacts/</code> in the repo).
        </p>
        {!readOnly && (
          <>
            <label className="field">
              <span>Export folder label</span>
              <input
                type="text"
                value={folderLabel}
                onChange={(event) => setFolderLabel(event.target.value)}
                placeholder={defaultFolderLabel}
              />
            </label>
            <p className="muted">
              Folder name preview: <code>{folderPreview}</code>
            </p>
            <p className="muted">
              Uses your session title by default (from the new-session screen). Edit the label
              above for a shorter name, or leave it unchanged.
            </p>
          </>
        )}
        {errorMessage && <ErrorBanner message={errorMessage} />}
        {session.artifact_warning && <WarningBanner message={session.artifact_warning} />}
        {!readOnly && (
        <button
          type="button"
          className="button primary"
          disabled={generate.isPending}
          onClick={() =>
            void generate
              .mutateAsync({
                exportFolderLabel: folderLabel.trim() || undefined,
              })
              .then((data) => {
              navigate(sessionPath(sessionId, sessionStepForState(data.session.state)));
            })
          }
        >
          {generate.isPending ? "Generating…" : "Generate artifacts"}
        </button>
        )}
      </Panel>
    </div>
  );
}

export function CompletePage({
  sessionId,
  session,
}: {
  sessionId: string;
  session: SessionDetailResponse;
}) {
  const promptId = session.prompt_id ?? session.session.prompt_id;
  const inferenceSettings = useQuery({
    queryKey: queryKeys.inferenceSettings,
    queryFn: fetchInferenceSettings,
  });
  const llmHealth = useQuery({
    queryKey: ["health", "llm"],
    queryFn: fetchLlmHealth,
    staleTime: 15_000,
  });
  const sendToModel = useSendToInference(sessionId);
  const [approvedSend, setApprovedSend] = useState(false);
  const [oneTimeEndpointId, setOneTimeEndpointId] = useState("");
  const [latestResponse, setLatestResponse] = useState<SendToInferenceResponse | null>(null);

  const inferenceResult = latestResponse ?? session.inference_result;
  const settings = inferenceSettings.data;
  const configuredEndpoints = useMemo(
    () => settings?.api_endpoints.filter((endpoint) => endpoint.configured) ?? [],
    [settings],
  );
  const localModelReady =
    llmHealth.data?.llm_enabled === true && llmHealth.data.status === "ok";
  const hasEndpointSlots = configuredEndpoints.length > 0;
  const canSend =
    settings?.send_to_inference_available === true &&
    (hasEndpointSlots ||
      (settings.external_inference_enabled
        ? settings.external_provider_api_key_configured
        : localModelReady));
  const sendError =
    sendToModel.error != null
      ? formatApiError(sendToModel.error, "Could not send prompt to the model.")
      : null;

  return (
    <div className="page narrow">
      <PageHeader
        title="Export complete"
        subtitle="This session is closed and preserved for audit. Start a new session from this template to iterate."
      />
      <Panel>
        {promptId && (
          <p>
            Registry entry: <code>{promptId}</code>
          </p>
        )}
        {session.expected_host_export_path && (
          <p className="muted">
            {session.generated_files.length} files written to{" "}
            <code>{session.expected_host_export_path}</code>
          </p>
        )}
        {!session.expected_host_export_path && session.artifact_manifest && (
          <p className="muted">
            {session.artifact_manifest.files.length} files written to{" "}
            <code>{session.artifact_manifest.expected_host_export_path}</code>
          </p>
        )}
        {session.artifact_warning && <WarningBanner message={session.artifact_warning} />}
        <div className="form-actions">
          <SessionTemplateButton sessionId={sessionId} />
          {promptId && (
            <Link to={`/registry/${promptId}`} className="button secondary">
              Open in registry
            </Link>
          )}
        </div>
      </Panel>

      <Panel title="Send to model">
        {inferenceSettings.isLoading ? (
          <p className="muted">Checking model API settings…</p>
        ) : !settings?.send_to_inference_available ? (
          <p className="muted">
            No external model API is configured. Add endpoints in{" "}
            <Link to="/settings">Settings</Link>, enable the setup local model, or use the .env
            external provider to run the optimized prompt.
          </p>
        ) : hasEndpointSlots ? (
          <p className="muted">
            Sends the approved optimized prompt to the selected API endpoint. The response is
            saved as <code>inference_response.txt</code> in the artifact folder.
          </p>
        ) : settings.external_inference_enabled ? (
          <p className="muted">
            Sends the approved optimized prompt to{" "}
            <code>{settings.external_provider_model}</code> via the configured external provider.
            The response is saved as <code>inference_response.txt</code> in the artifact folder.
          </p>
        ) : (
          <p className="muted">
            Sends the approved optimized prompt to your local model (
            <code>{settings.local_chat_model}</code>
            ). The response is saved as <code>inference_response.txt</code> in the artifact
            folder.
          </p>
        )}

        {settings?.send_to_inference_available && !canSend && (
          <WarningBanner
            message={
              hasEndpointSlots
                ? "Selected endpoint is not available."
                : settings.external_inference_enabled
                ? "External inference is enabled but no API key is configured."
                : "Local model API is not reachable. Start the LLM server (make ensure-llm) and retry."
            }
          />
        )}

        {canSend && configuredEndpoints.length > 0 && (
          <p className="muted">
            Choose a one-time API override next to Send, or leave the default from the dashboard.
          </p>
        )}

        {inferenceResult && (
          <div className="inference-result">
            <p className="muted">
              Last run: {inferenceResult.model} · saved to{" "}
              <code>{inferenceResult.inference_response_artifact_path}</code>
            </p>
            <DraftBlock body={inferenceResult.response_text} label="Model response" />
          </div>
        )}

        {canSend && (
          <>
            <label className="field checkbox-field">
              <input
                type="checkbox"
                checked={approvedSend}
                disabled={sendToModel.isPending}
                onChange={(event) => setApprovedSend(event.target.checked)}
              />
              <span>I approve sending the optimized prompt to the model API</span>
            </label>
            {sendError && <ErrorBanner message={sendError} />}
            <div className="split-button-row">
              <button
                type="button"
                className="button primary"
                disabled={!approvedSend || sendToModel.isPending}
                onClick={() =>
                  void sendToModel
                    .mutateAsync(oneTimeEndpointId || null)
                    .then((data) => {
                      setLatestResponse(data);
                      setApprovedSend(false);
                    })
                }
              >
                {sendToModel.isPending ? "Sending…" : "Send to model"}
              </button>
              {configuredEndpoints.length > 0 && (
                <label className="field split-button-select">
                  <span className="sr-only">API for this send</span>
                  <select
                    className="select-input"
                    value={oneTimeEndpointId}
                    disabled={sendToModel.isPending}
                    onChange={(event) => setOneTimeEndpointId(event.target.value)}
                    aria-label="API endpoint for this send"
                  >
                    <option value="">
                      Default
                      {settings?.default_api_endpoint_id
                        ? ` (${configuredEndpoints.find((item) => item.id === settings.default_api_endpoint_id)?.label || "configured"})`
                        : ""}
                    </option>
                    {configuredEndpoints.map((endpoint) => (
                      <option key={endpoint.id} value={endpoint.id}>
                        {endpoint.label || endpoint.chat_model}
                      </option>
                    ))}
                  </select>
                </label>
              )}
            </div>
          </>
        )}
      </Panel>
    </div>
  );
}
