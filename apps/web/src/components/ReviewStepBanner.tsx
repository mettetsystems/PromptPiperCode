import { Link } from "react-router-dom";
import type { SessionState } from "../api/types";
import {
  SESSION_STEP_LABELS,
  sessionPath,
  sessionStepForState,
  type SessionStep,
} from "../lib/sessionRouting";

interface ReviewStepBannerProps {
  sessionId: string;
  state: SessionState;
}

export function ReviewStepBanner({ sessionId, state }: ReviewStepBannerProps) {
  const currentStep = sessionStepForState(state);

  return (
    <div className="callout callout-warn review-step-banner" role="status">
      <strong>Review mode</strong>
      <p>
        You are viewing a completed step. Use the action below to re-open this step, or continue
        from the current step.
      </p>
      <Link to={sessionPath(sessionId, currentStep)} className="button secondary">
        Continue at {SESSION_STEP_LABELS[currentStep]}
      </Link>
    </div>
  );
}

export type { SessionStep };
