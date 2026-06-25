import { useNavigate } from "react-router-dom";
import { formatApiError } from "../api/http";
import { useCreateSessionFromTemplate } from "../api/hooks";
import { sessionPath } from "../lib/sessionRouting";
import { ErrorBanner } from "./ui";

interface SessionTemplateButtonProps {
  sessionId: string;
  className?: string;
}

export function SessionTemplateButton({
  sessionId,
  className = "button primary",
}: SessionTemplateButtonProps) {
  const navigate = useNavigate();
  const createTemplate = useCreateSessionFromTemplate(sessionId);

  const error =
    createTemplate.error != null
      ? formatApiError(createTemplate.error, "Could not create a session from this template.")
      : null;

  return (
    <div className="session-template-action">
      {error && <ErrorBanner message={error} />}
      <button
        type="button"
        className={className}
        disabled={createTemplate.isPending}
        onClick={() =>
          void createTemplate.mutateAsync(undefined).then((data) => {
            navigate(sessionPath(data.session.id, "edit"));
          })
        }
      >
        {createTemplate.isPending ? "Creating session…" : "Use as template"}
      </button>
    </div>
  );
}
