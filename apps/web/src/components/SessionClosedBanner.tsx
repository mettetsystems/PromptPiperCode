import { SessionTemplateButton } from "./SessionTemplateButton";

interface SessionClosedBannerProps {
  sessionId: string;
}

export function SessionClosedBanner({ sessionId }: SessionClosedBannerProps) {
  return (
    <div className="callout callout-warn session-closed-banner" role="status">
      <strong>Session closed</strong>
      <p>
        This session is complete and preserved for audit. Previous steps are read-only and cannot
        be re-run.
      </p>
      <SessionTemplateButton sessionId={sessionId} />
    </div>
  );
}
