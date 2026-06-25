/** Shared types for Prompt Piper frontend and OpenAPI-generated contracts. */

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
  database: string;
  timestamp: string;
}

export const APP_NAME = "Prompt Piper" as const;

export const LOCAL_FIRST_NOTICE =
  "Prompt Piper runs locally. External models are used only when you explicitly send a finalized prompt.";
