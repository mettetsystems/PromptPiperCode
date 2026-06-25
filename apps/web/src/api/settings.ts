import { apiFetch } from "./http";
import type { InferenceSettingsResponse, UserSettingsResponse, UserSettingsUpdateRequest } from "./types";

export function fetchUserSettings(): Promise<UserSettingsResponse> {
  return apiFetch<UserSettingsResponse>("/settings/user");
}

export function updateUserSettings(
  payload: UserSettingsUpdateRequest,
): Promise<UserSettingsResponse> {
  return apiFetch<UserSettingsResponse>("/settings/user", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function fetchInferenceSettings(): Promise<InferenceSettingsResponse> {
  return apiFetch<InferenceSettingsResponse>("/settings/inference");
}
