import { useEffect, useMemo, useRef, useState } from "react";
import { createRun, getRun, getRunEvents, pauseRun, resumeRun } from "../api/processCompliance";
import { streamRunEvents } from "../api/stream";
import type { AgentEvent, AnalysisResult } from "../types/processCompliance";
import AgentLivePanel from "../components/agents/AgentLivePanel";
import FileUploadInput from "../components/forms/FileUploadInput";

type UiStatus = "idle" | "creating_run" | "running" | "completed" | "failed";
type StepKey =
  | "model_preparation"
  | "knowledge_base_preparation"
  | "data_validation"
  | "prediction"
  | "retrieval"
  | "check_agent"
  | "predict_agent"
  | "summary_agent"
  | "final_result";
type StepState = "pending" | "running" | "completed" | "failed";

type AgentCard = {
  agentName: string;
  content: string;
  completed: boolean;
};

const STEP_ORDER: StepKey[] = [
  "model_preparation",
  "knowledge_base_preparation",
  "data_validation",
  "prediction",
  "retrieval",
  "check_agent",
  "predict_agent",
  "summary_agent",
  "final_result",
];

function initSteps(): Record<StepKey, StepState> {
  return {
    model_preparation: "pending",
    knowledge_base_preparation: "pending",
    data_validation: "pending",
    prediction: "pending",
    retrieval: "pending",
    check_agent: "pending",
    predict_agent: "pending",
    summary_agent: "pending",
    final_result: "pending",
  };
}

function mapAgentToStep(agent?: string | null): StepKey | null {
  if (agent === "check_agent") return "check_agent";
  if (agent === "predict_agent") return "predict_agent";
  if (agent === "summary_agent") return "summary_agent";
  return null;
}

export default function RunPrediction() {
  const [eventLogPath, setEventLogPath] = useState("data/BPIC20_D.csv");
  const [runningTracePath, setRunningTracePath] = useState("data/running_trace/BPIC20_D_trace.csv");
  const [datasetName, setDatasetName] = useState("BPIC20_D");
  const [status, setStatus] = useState<UiStatus>("idle");
  const [runId, setRunId] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [steps, setSteps] = useState<Record<StepKey, StepState>>(initSteps);
  const [agentCards, setAgentCards] = useState<Record<string, AgentCard>>({});
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [tick, setTick] = useState(0);
  const closeStreamRef = useRef<(() => void) | null>(null);
  const [stepStartedAt, setStepStartedAt] = useState<Record<string, number>>({});
  const [isPaused, setIsPaused] = useState(false);
  const seenEventIdsRef = useRef<Set<string>>(new Set());
  const fallbackEventSeqRef = useRef<number>(0);

  const orderedCards = useMemo(
    () => Object.values(agentCards).sort((a, b) => a.agentName.localeCompare(b.agentName)),
    [agentCards],
  );

  const setStep = (key: StepKey, value: StepState) => {
    setSteps((prev) => ({ ...prev, [key]: value }));
  };

  useEffect(() => {
    const timer = setInterval(() => setTick((v) => v + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const normalizeEvent = (raw: unknown): AgentEvent | null => {
    if (!raw || typeof raw !== "object") return null;
    const obj = raw as Record<string, unknown>;
    const eventType = typeof obj.type === "string" ? obj.type : null;
    if (!eventType) return null;
    const run_id = typeof obj.run_id === "string" ? obj.run_id : runId;
    const event_id =
      typeof obj.event_id === "string"
        ? obj.event_id
        : `fallback_${++fallbackEventSeqRef.current}`;
    const timestamp = typeof obj.timestamp === "string" ? obj.timestamp : new Date().toISOString();
    return {
      run_id,
      event_id,
      timestamp,
      type: eventType as AgentEvent["type"],
      agent_name: (obj.agent_name as string | null | undefined) ?? null,
      round_index: (obj.round_index as number | null | undefined) ?? null,
      step_name: (obj.step_name as string | null | undefined) ?? null,
      content: (obj.content as string | null | undefined) ?? null,
      partial_content: (obj.partial_content as string | null | undefined) ?? null,
      payload: (obj.payload as Record<string, unknown> | undefined) ?? {},
    };
  };

  const onEvent = (rawEvent: AgentEvent | unknown) => {
    const event = normalizeEvent(rawEvent);
    if (!event) return;
    if (seenEventIdsRef.current.has(event.event_id)) return;
    seenEventIdsRef.current.add(event.event_id);
    setEvents((prev) => [...prev, event]);
    if (error === "SSE disconnected, fallback polling is active.") {
      setError("");
    }
    const stepDict = initSteps();
    if (event.type === "step_started" && event.step_name && event.step_name in stepDict) {
      setStep(event.step_name as StepKey, "running");
      setStepStartedAt((prev) => ({ ...prev, [event.step_name as string]: Date.now() }));
    }
    if (event.type === "step_completed" && event.step_name && event.step_name in stepDict) {
      setStep(event.step_name as StepKey, "completed");
    }

    if (event.type === "agent_started" && event.agent_name) {
      const step = mapAgentToStep(event.agent_name);
      if (step) {
        setStep(step, "running");
        setStepStartedAt((prev) => ({ ...prev, [step]: Date.now() }));
      }
      setAgentCards((prev) => ({
        ...prev,
        [event.agent_name as string]: {
          agentName: event.agent_name as string,
          content: prev[event.agent_name as string]?.content ?? "",
          completed: false,
        },
      }));
    }

    if (event.type === "agent_token" && event.agent_name) {
      const token = event.partial_content ?? "";
      setAgentCards((prev) => {
        const old = prev[event.agent_name as string] ?? {
          agentName: event.agent_name as string,
          content: "",
          completed: false,
        };
        return {
          ...prev,
          [event.agent_name as string]: {
            ...old,
            content: (old.content ?? "") + token,
          },
        };
      });
    }

    if (event.type === "agent_message_completed" && event.agent_name) {
      const step = mapAgentToStep(event.agent_name);
      if (step) setStep(step, "completed");
      setAgentCards((prev) => ({
        ...prev,
        [event.agent_name as string]: {
          agentName: event.agent_name as string,
          content: event.content ?? prev[event.agent_name as string]?.content ?? "",
          completed: true,
        },
      }));
    }

    if (event.type === "final_result") {
      setStep("final_result", "completed");
      if (event.content) {
        try {
          const parsed = JSON.parse(event.content) as AnalysisResult;
          setResult(parsed);
        } catch {
          // ignore; fallback on completed event via getRun
        }
      }
    }

    if (event.type === "run_started") {
      setStatus("running");
    }
    if (event.type === "run_completed") {
      setStatus("completed");
    }
    if (event.type === "run_failed") {
      setStatus("failed");
      setError(event.content ?? "Run failed.");
      setSteps((prev) => {
        const next = { ...prev };
        for (const k of STEP_ORDER) {
          if (next[k] === "running") next[k] = "failed";
        }
        return next;
      });
    }
    if (event.step_name === "paused" && event.type === "step_started") {
      setIsPaused(true);
    }
    if (event.step_name === "paused" && event.type === "step_completed") {
      setIsPaused(false);
    }
  };

  const runAnalysis = async () => {
    closeStreamRef.current?.();
    closeStreamRef.current = null;
    setStatus("creating_run");
    setRunId("");
    setError("");
    setSteps(initSteps());
    setAgentCards({});
    setEvents([]);
    setResult(null);
    setIsPaused(false);
    seenEventIdsRef.current = new Set();
    fallbackEventSeqRef.current = 0;

    try {
      const created = await createRun({
        event_log_path: eventLogPath,
        running_trace_path: runningTracePath,
        dataset_name: datasetName || undefined,
      });
      setRunId(created.run_id);
      setStatus("running");

      // prime UI quickly in case SSE handshake is slow
      try {
        const initial = await getRunEvents(created.run_id);
        const arr = (initial.events ?? []) as unknown[];
        arr.forEach((evt) => onEvent(evt));
      } catch {
        // ignore
      }

      const close = streamRunEvents(created.run_id, {
        onEvent,
        onFinalResult: onEvent,
        onCompleted: async () => {
          setStatus("completed");
          try {
            const finalResult = await getRun(created.run_id);
            setResult(finalResult);
          } catch {
            // ignore
          }
        },
        onError: () => {
          // Do not mark failed immediately; polling fallback continues.
          setError("SSE disconnected, fallback polling is active.");
        },
      });
      closeStreamRef.current = () => close.close();

      // Polling fallback: in case SSE is delayed/disconnected, keep UI live by pulling events.
      const pollTimer = setInterval(async () => {
        try {
          const payload = await getRunEvents(created.run_id);
          const arr = (payload.events ?? []) as unknown[];
          arr.forEach((evt) => onEvent(evt));
          if (payload.status === "failed") {
            setStatus("failed");
            if (payload.error) {
              setError(`Run failed: ${payload.error}`);
            }
          } else if (payload.status === "running") {
            setStatus((s) => (s === "creating_run" ? "running" : s));
          }
        } catch {
          setError("Polling /api/runs/{run_id}/events failed. Check backend URL and server logs.");
        }
      }, 1000);

      const prevCloser = closeStreamRef.current;
      closeStreamRef.current = () => {
        clearInterval(pollTimer);
        prevCloser?.();
      };
    } catch (e) {
      setStatus("failed");
      setError(e instanceof Error ? e.message : "Failed to create run.");
    }
  };

  const togglePause = async () => {
    if (!runId) return;
    try {
      if (isPaused) {
        await resumeRun(runId);
      } else {
        await pauseRun(runId);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Pause/resume failed.");
    }
  };

  const badgeClass = (state: StepState): string => {
    if (state === "running") return "status-badge status-running";
    if (state === "completed") return "status-badge status-completed";
    if (state === "failed") return "status-badge status-failed";
    return "status-badge status-pending";
  };

  const runtimeHint = useMemo(() => {
    void tick;
    const latest = [...events].reverse().find((e) => e.type === "step_started" || e.type === "agent_started" || e.type === "step_completed" || e.type === "agent_message_completed");
    if (!latest) return "Current Step: waiting to start.";

    const currentRunningStep = STEP_ORDER.find((s) => steps[s] === "running") ?? latest.step_name ?? mapAgentToStep(latest.agent_name) ?? "unknown";
    const payload = (latest.payload ?? {}) as Record<string, unknown>;
    const scriptFile = typeof payload.script_file === "string" ? payload.script_file : "unknown";
    const etaRaw = typeof payload.eta_remaining_seconds === "number" ? payload.eta_remaining_seconds : null;
    const progress = (payload.trace_progress ?? {}) as Record<string, unknown>;
    const currentIdx = typeof progress.current_event_index === "number" ? progress.current_event_index : null;
    const total = typeof progress.total_events === "number" ? progress.total_events : null;
    const progressText = currentIdx !== null && total !== null ? ` | Trace Event: ${currentIdx}/${total}` : "";

    const startedTs = stepStartedAt[currentRunningStep];
    const elapsedSec = startedTs ? Math.max(0, Math.floor((Date.now() - startedTs) / 1000)) : 0;

    const etaText = etaRaw !== null ? `${Math.max(0, Math.round(etaRaw))}s` : "unknown";
    return `Current Step: ${currentRunningStep} | Elapsed: ${elapsedSec}s | ETA Remaining: ${etaText}${progressText} | Script: ${scriptFile}`;
  }, [events, stepStartedAt, steps, tick]);

  const currentRunningTrace = useMemo(() => {
    const latestWithTrace = [...events]
      .reverse()
      .find((e) => typeof (e.payload as Record<string, unknown> | undefined)?.running_trace_text === "string");
    const text = (latestWithTrace?.payload as Record<string, unknown> | undefined)?.running_trace_text;
    return typeof text === "string" && text.trim() ? text : "No running trace snapshot yet.";
  }, [events]);

  return (
    <div className="page">
      <h1 className="page-title">Run Prediction</h1>
      <p className="page-subtitle">
        Submit event log and running trace, then monitor each pipeline and agent step in real time.
      </p>

      <div className="grid-2" style={{ marginTop: 14 }}>
        <div className="card">
          <h3 className="section-title">Input</h3>
          <div className="form-grid">
            <label className="label">
          Event Log Path
          <input
            className="input"
            value={eventLogPath}
            onChange={(e) => setEventLogPath(e.target.value)}
          />
        </label>
        <FileUploadInput
          label="Upload Event Log (.csv/.xes)"
          onUploaded={(filePath) => setEventLogPath(filePath)}
        />
            <label className="label">
          Running Trace Path
          <input
            className="input"
            value={runningTracePath}
            onChange={(e) => setRunningTracePath(e.target.value)}
          />
        </label>
        <FileUploadInput
          label="Upload Running Trace (.csv/.xes)"
          onUploaded={(filePath) => setRunningTracePath(filePath)}
        />
            <label className="label">
          Dataset Name
          <input
            className="input"
            value={datasetName}
            onChange={(e) => setDatasetName(e.target.value)}
          />
        </label>
            <button className="btn" onClick={runAnalysis} disabled={status === "creating_run" || status === "running"}>
          Run Analysis
        </button>
          </div>
        </div>

        <div className="card">
          <h3 className="section-title">Run State</h3>
          <div className="kv">
            <span><strong>Status:</strong> {status}</span>
          </div>
          <div className="code-block" style={{ marginTop: 8 }}>
            {runtimeHint}
          </div>
          {runId && (
            <div className="kv" style={{ marginTop: 8 }}>
              <span><strong>Run ID:</strong> {runId}</span>
              <button
                className="btn"
                style={{ height: 28, padding: "0 10px", fontSize: 12 }}
                onClick={togglePause}
                disabled={!runId || status === "failed" || status === "completed"}
              >
                {isPaused ? "Resume" : "Pause"}
              </button>
            </div>
          )}
          {error && <div className="error" style={{ marginTop: 12 }}>{error}</div>}
          <div className="stack" style={{ marginTop: 12 }}>
            {STEP_ORDER.map((s) => (
              <div key={s} className="kv">
                <strong>{s}</strong>
                <span className={badgeClass(steps[s])}>{steps[s]}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card" style={{ marginTop: 12, borderColor: "rgba(34,211,238,0.55)" }}>
        <h3 className="section-title">Current Running Trace (Current Step Snapshot)</h3>
        <div className="code-block" style={{ minHeight: 90 }}>
          {currentRunningTrace}
        </div>
      </div>

      <div className="card" style={{ marginTop: 12 }}>
      <h3 className="section-title">Agent Responses</h3>
      {orderedCards.length === 0 ? (
        <p className="muted">No agent events yet.</p>
      ) : (
        orderedCards.map((card) => (
          <div
            key={card.agentName}
            className="card"
            style={{ marginBottom: 10 }}
          >
            <div>
              <strong>{card.agentName}</strong> {card.completed ? "(completed)" : "(streaming)"}
            </div>
            <div className="code-block">{card.content || "(empty)"}</div>
          </div>
        ))
      )}
      </div>

      <div className="card" style={{ marginTop: 12 }}>
        <h3 className="section-title">Live Event Stream</h3>
        <AgentLivePanel events={events} />
      </div>

      <div className="card" style={{ marginTop: 12 }}>
      <h3 className="section-title">Final Result</h3>
      {result ? (
        <div className="stack">
          <div className="kv">
            <strong>Result Status:</strong> {result.status}
          </div>
          <div className="kv">
            <strong>Current Status:</strong> {result.compliance.current_status}
          </div>
          <div className="kv">
            <strong>Future Risk:</strong> {result.compliance.future_risk}
          </div>
          <div className="kv">
            <strong>Next Activity:</strong> {result.prediction.next_activity ?? "N/A"}
          </div>
          <div className="kv">
            <strong>Outcome:</strong> {result.prediction.outcome ?? "N/A"}
          </div>
          <div className="kv">
            <strong>Remaining Time:</strong> {result.prediction.remaining_time ?? "N/A"}{" "}
            {result.prediction.remaining_time_unit ?? ""}
          </div>
        </div>
      ) : (
        <p className="muted">Waiting for final result...</p>
      )}
      </div>
    </div>
  );
}
