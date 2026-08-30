/** Dev-server paths that belong to the React app, not the FastAPI backend. */
export const SESSION_UI_STEP =
  /\/sessions\/[^/]+\/(clarify|edit|similarity|optimize|export|complete|precision)(?:\/?$|\?)/;

/** Session API routes that must never be served as index.html during dev. */
export const SESSION_API_PATH =
  /\/sessions(?:\/[^/]+(?:\/(?:delete|answer|edit|finalize|optimize(?:\/approve)?|artifacts|send-to-inference|template|workflow(?:\/(?:reopen\/edit|rerun\/(?:similarity|optimize)))?|clarify(?:\/(?:suggest|complete|locals))?|precision(?:\/(?:suggest|apply))?))?)?$/;

const SAFE_SPA_METHODS = new Set(["GET", "HEAD"]);

/**
 * Vite's HTML fallback returns 405 for non-GET requests. Mutations must always
 * proxy to the API, even when the browser sends Accept: text/html.
 */
export function isSpaNavigation(url: string, accept: string, method = "GET"): boolean {
  const verb = method.toUpperCase();
  if (!SAFE_SPA_METHODS.has(verb)) {
    return false;
  }
  const path = url.split("?")[0] ?? url;
  if (SESSION_API_PATH.test(path) && !accept.includes("text/html")) {
    return false;
  }
  if (accept.includes("text/html")) {
    return true;
  }
  if (path === "/sessions/new") {
    return true;
  }
  if (SESSION_UI_STEP.test(path)) {
    return true;
  }
  if (path === "/registry") {
    return true;
  }
  // /registry/:promptId — API lives under /registry/prompts/...
  if (/^\/registry\/(?!prompts)/.test(path)) {
    return true;
  }
  return false;
}
