import { apiRequest } from "./client";
import type { AppSettings, SettingsResponse } from "../types/processCompliance";

export async function getSettings(): Promise<SettingsResponse> {
  return apiRequest<SettingsResponse>("/api/settings", { method: "GET" });
}

export async function updateSettings(config: AppSettings): Promise<SettingsResponse> {
  return apiRequest<SettingsResponse>("/api/settings", {
    method: "PUT",
    body: JSON.stringify(config),
  });
}

