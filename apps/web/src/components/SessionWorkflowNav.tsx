import { Link } from "react-router-dom";
import type { SessionState } from "../api/types";
import {
  SESSION_STEP_LABELS,
  SESSION_STEPS,
  canVisitStep,
  sessionPath,
  sessionStepForState,
  type SessionStep,
} from "../lib/sessionRouting";

interface SessionWorkflowNavProps {
  sessionId: string;
  state: SessionState;
  activeStep: SessionStep;
}

export function SessionWorkflowNav({ sessionId, state, activeStep }: SessionWorkflowNavProps) {
  const currentStep = sessionStepForState(state);

  return (
    <nav className="workflow-nav" aria-label="Session workflow">
      <ol className="workflow-steps">
        {SESSION_STEPS.map((step) => {
          const reachable = canVisitStep(step, state);
          const isActive = step === activeStep;
          const isCurrent = step === currentStep;

          return (
            <li
              key={step}
              className={[
                "workflow-step",
                isActive ? "is-active" : "",
                isCurrent ? "is-current" : "",
                reachable ? "is-reachable" : "is-locked",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {reachable ? (
                <Link
                  to={sessionPath(sessionId, step)}
                  aria-current={isActive ? "step" : undefined}
                  className="workflow-step-link"
                >
                  {SESSION_STEP_LABELS[step]}
                </Link>
              ) : (
                <span className="workflow-step-link" aria-disabled="true">
                  {SESSION_STEP_LABELS[step]}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
