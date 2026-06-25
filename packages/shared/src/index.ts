/**
 * Shared types for Prompt Piper.
 * OpenAPI-generated types can be added here as the API surface grows.
 */

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  timestamp: string;
  database: "sqlite" | "postgresql" | string;
}

export interface LlmHealthResponse {
  llm_enabled: boolean;
  status: "ok" | "disabled" | "unreachable" | string;
  endpoint: string | null;
  model_name: string | null;
  message: string;
  checked_at: string;
}

export const APP_NAME = "Prompt Piper";

export const APP_TAGLINE =
  "Design, refine, and store prompts locally. Send to a model only when you choose.";
