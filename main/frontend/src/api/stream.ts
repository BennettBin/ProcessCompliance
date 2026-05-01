import { API_BASE_URL } from "./client";
import type { AgentEvent } from "../types/processCompliance";

export interface StreamHandlers {
  onEvent?: (event: AgentEvent) => void;
  onFinalResult?: (event: AgentEvent) => void;
  onCompleted?: (event: AgentEvent) => void;
  onError?: (error: Event) => void;
}

export function streamRunEvents(runId: string, handlers: StreamHandlers = {}): EventSource {
  let closed = false;
  let reconnectTimer: number | null = null;
  let lastSeq = 0;
  let source: EventSource | null = null;
  let consecutiveErrors = 0;

  const connect = () => {
    const url = `${API_BASE_URL}/api/runs/${runId}/stream?since=${lastSeq}`;
    source = new EventSource(url);
    source.onopen = () => {
      consecutiveErrors = 0;
    };

    source.onmessage = (message) => {
      try {
        const event = JSON.parse(message.data) as AgentEvent;
        consecutiveErrors = 0;
        const seq = Number((event.payload as Record<string, unknown> | undefined)?.event_seq ?? 0);
        if (Number.isFinite(seq) && seq > lastSeq) {
          lastSeq = seq;
        }
        handlers.onEvent?.(event);

        if (event.type === "final_result") {
          handlers.onFinalResult?.(event);
        }
        if (event.type === "run_completed") {
          handlers.onCompleted?.(event);
          close();
        }
        if (event.type === "run_failed") {
          handlers.onError?.(new Event("run_failed"));
          close();
        }
      } catch {
        // ignore malformed messages
      }
    };

    source.onerror = (error) => {
      if (closed) return;
      consecutiveErrors += 1;
      // EventSource may emit transient onerror during normal reconnect.
      // Only escalate after repeated failures.
      if (consecutiveErrors >= 3) {
        handlers.onError?.(error);
      }
      try {
        source?.close();
      } catch {
        // ignore
      }
      if (reconnectTimer !== null) {
        window.clearTimeout(reconnectTimer);
      }
      reconnectTimer = window.setTimeout(connect, 1000);
    };
  };

  const close = () => {
    closed = true;
    if (reconnectTimer !== null) {
      window.clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    try {
      source?.close();
    } catch {
      // ignore
    }
  };

  connect();
  return { close } as unknown as EventSource;
}
