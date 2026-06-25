import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { artifactFileUrl } from "../api/http";
import { useRegistryPrompt } from "../api/hooks";
import { RequirementCardPanel } from "../components/RequirementCardPanel";
import { DraftBlock, LoadingState, PageHeader, Panel } from "../components/ui";

export function RegistryDetailPage() {
  const { promptId = "" } = useParams();
  const detail = useRegistryPrompt(promptId);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>("");
  const [fileLoading, setFileLoading] = useState(false);

  async function openArtifact(filename: string) {
    setSelectedFile(filename);
    setFileLoading(true);
    try {
      const response = await fetch(artifactFileUrl(promptId, filename));
      if (!response.ok) {
        setFileContent(`Failed to load ${filename} (${response.status}).`);
        return;
      }
      const text = await response.text();
      setFileContent(text);
    } catch {
      setFileContent(`Failed to load ${filename}.`);
    } finally {
      setFileLoading(false);
    }
  }

  if (detail.isLoading) {
    return <LoadingState label="Loading prompt…" />;
  }

  if (detail.isError || !detail.data) {
    return (
      <div className="page">
        <PageHeader title="Prompt not found" />
        <Link to="/registry" className="text-link">
          Back to registry
        </Link>
      </div>
    );
  }

  const data = detail.data;
  const metadata = data.metadata;
  const manifestFiles = data.artifact_manifest?.files ?? [];
  const artifactPaths = Object.entries(metadata.artifact_paths);

  return (
    <div className="page">
      <PageHeader
        title={metadata.title}
        subtitle={metadata.abstract || "Finalized prompt registry entry"}
        actions={
          <Link to="/registry" className="button secondary">
            Back
          </Link>
        }
      />

      <div className="grid-workflow">
        <div className="workflow-main stack-form">
          <Panel title="Metadata">
            <dl className="field-list">
              <div className="field-block">
                <dt>Prompt ID</dt>
                <dd>
                  <code>{metadata.prompt_id}</code>
                </dd>
              </div>
              <div className="field-block">
                <dt>Version</dt>
                <dd>{metadata.version}</dd>
              </div>
              <div className="field-block">
                <dt>Output form</dt>
                <dd>{metadata.output_form || "—"}</dd>
              </div>
              {metadata.tags.length > 0 && (
                <div className="field-block">
                  <dt>Tags</dt>
                  <dd>{metadata.tags.join(", ")}</dd>
                </div>
              )}
              {Object.keys(metadata.evaluation_scores).length > 0 && (
                <div className="field-block">
                  <dt>Evaluation scores</dt>
                  <dd>
                    <ul className="compact-list">
                      {Object.entries(metadata.evaluation_scores).map(([key, value]) => (
                        <li key={key}>
                          {key}: {value}
                        </li>
                      ))}
                    </ul>
                  </dd>
                </div>
              )}
            </dl>
          </Panel>

          <Panel title="Canonical prompt">
            <DraftBlock body={data.canonical_prompt} label="Registry canonical" />
          </Panel>

          <Panel title="Artifacts">
            {manifestFiles.length === 0 && artifactPaths.length === 0 ? (
              <p className="muted">No export artifacts linked yet.</p>
            ) : (
              <ul className="artifact-list">
                {manifestFiles.map((file) => (
                  <li key={file.name}>
                    <button
                      type="button"
                      className="text-link button-link"
                      onClick={() => void openArtifact(file.name)}
                    >
                      {file.name}
                    </button>
                    <span className="muted">
                      {" "}
                      ({file.format}, {file.size_bytes} bytes)
                    </span>
                    <a
                      href={artifactFileUrl(promptId, file.name)}
                      className="text-link"
                      target="_blank"
                      rel="noreferrer"
                    >
                      Open
                    </a>
                  </li>
                ))}
                {manifestFiles.length === 0 &&
                  artifactPaths.map(([key, path]) => (
                    <li key={key}>
                      <code>{key}</code>: <code>{path}</code>
                    </li>
                  ))}
              </ul>
            )}
            {selectedFile && (
              <div className="artifact-preview">
                <h3>{selectedFile}</h3>
                {fileLoading ? (
                  <LoadingState />
                ) : (
                  <pre className="draft-text">{fileContent}</pre>
                )}
              </div>
            )}
          </Panel>
        </div>
        <RequirementCardPanel card={data.requirement_card} title="Requirement card" />
      </div>
    </div>
  );
}
