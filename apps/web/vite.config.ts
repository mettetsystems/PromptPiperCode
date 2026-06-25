import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

const rootDir = fileURLToPath(new URL(".", import.meta.url));
const repoRoot = path.resolve(rootDir, "../..");

/** Dev-server paths that belong to the React app, not the FastAPI backend. */
const SESSION_UI_STEP =
  /\/sessions\/[^/]+\/(clarify|edit|similarity|optimize|export|complete|precision)(?:\/?$|\?)/;

/** Session API routes that must never be served as index.html during dev. */
const SESSION_API_PATH =
  /\/sessions(?:\/[^/]+(?:\/(?:answer|edit|finalize|optimize(?:\/approve)?|artifacts|send-to-inference|template|workflow(?:\/(?:reopen\/edit|rerun\/(?:similarity|optimize)))?|clarify(?:\/(?:suggest|complete))?|precision(?:\/(?:suggest|apply))?))?)?$/;

function isSpaNavigation(url: string, accept: string): boolean {
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

function apiProxy(target: string) {
  return {
    target,
    bypass(req: { url?: string; headers?: { accept?: string } }) {
      const url = req.url ?? "";
      const accept = req.headers?.accept ?? "";
      if (isSpaNavigation(url, accept)) {
        return "/index.html";
      }
      return undefined;
    },
  };
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, repoRoot, "");
  const apiTarget = `http://${env.API_HOST ?? "127.0.0.1"}:${env.API_PORT ?? "8000"}`;

  return {
    envDir: repoRoot,
    plugins: [react()],
    resolve: {
      alias: {
        "@assets": path.resolve(repoRoot, "assets"),
      },
    },
    server: {
      host: "127.0.0.1",
      port: 5173,
      proxy: {
        "/health": apiProxy(apiTarget),
        "/sessions": apiProxy(apiTarget),
        "/registry": apiProxy(apiTarget),
        "/settings": apiProxy(apiTarget),
      },
    },
    test: {
      environment: "jsdom",
      setupFiles: "./src/test/setup.ts",
      css: true,
    },
  };
});
