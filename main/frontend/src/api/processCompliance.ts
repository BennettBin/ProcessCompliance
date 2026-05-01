import { apiRequest } from "./client";
import type {
  AnalyzeRequest,
  AnalysisResult,
  RunCreateResponse,
  RunSummary,
} from "../types/processCompliance";

export async function createRun(payload: AnalyzeRequest): Promise<RunCreateResponse> {
  return apiRequest<RunCreateResponse>("/api/runs", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function analyzeTrace(payload: AnalyzeRequest): Promise<AnalysisResult> {
  const res = await apiRequest<{ run_id: string; status: string; result: AnalysisResult }>("/api/analyze", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return res.result;
}

export async function listRuns(): Promise<RunSummary[]> {
  const res = await apiRequest<{ runs: RunSummary[] }>("/api/runs", {
    method: "GET",
  });
  return res.runs;
}

export async function getRun(runId: string): Promise<AnalysisResult> {
  const res = await apiRequest<{ run_id: string; status: string; result: AnalysisResult | null }>(
    `/api/runs/${runId}`,
    { method: "GET" },
  );
  if (!res.result) {
    throw new Error(`Run ${runId} is not completed yet.`);
  }
  return res.result;
}

export async function getRunEvents(
  runId: string,
): Promise<{ run_id: string; status?: string; error?: string | null; events: unknown[] }> {
  return apiRequest<{ run_id: string; status?: string; error?: string | null; events: unknown[] }>(
    `/api/runs/${runId}/events`,
    {
    method: "GET",
    },
  );
}

export async function pauseRun(runId: string): Promise<{ run_id: string; status: string }> {
  return apiRequest<{ run_id: string; status: string }>(`/api/runs/${runId}/pause`, {
    method: "POST",
  });
}

export async function resumeRun(runId: string): Promise<{ run_id: string; status: string }> {
  return apiRequest<{ run_id: string; status: string }>(`/api/runs/${runId}/resume`, {
    method: "POST",
  });
}
