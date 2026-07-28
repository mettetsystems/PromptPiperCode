/**
 * Shared types for PromptPiperCode.
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

export const APP_NAME = "PromptPiperCode";

export const APP_TAGLINE =
  "Design coding prompts locally across six dimensions. Export a structured spec and a ready-to-paste prompt.";
