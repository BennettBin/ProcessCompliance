import type { AgentEvent } from "../../types/processCompliance";

type Props = {
  events: AgentEvent[];
  limit?: number;
};

function shortText(s: string, max = 220): string {
  if (s.length <= max) return s;
  return `${s.slice(0, max)}...`;
}

export default function AgentEventLog({ events, limit = 100 }: Props) {
  const visible = events.slice(Math.max(0, events.length - limit));
  return (
    <div
      style={{
        border: "1px solid rgba(148,163,184,0.25)",
        borderRadius: 8,
        padding: 10,
        maxHeight: 320,
        overflow: "auto",
        fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
        fontSize: 12,
      }}
    >
      {visible.map((e) => {
        const payload = (e.payload ?? {}) as Record<string, unknown>;
        const prompt = typeof payload.prompt === "string" ? payload.prompt : "";
        const traceText = typeof payload.running_trace_text === "string" ? payload.running_trace_text : "";
        return (
          <div key={e.event_id} style={{ marginBottom: 10, borderBottom: "1px solid rgba(148,163,184,0.2)", paddingBottom: 8 }}>
            <div>
              [{e.timestamp}] {e.type} step={e.step_name ?? "-"} agent={e.agent_name ?? "-"} round={e.round_index ?? "-"}
            </div>
            {prompt ? <div>prompt: {shortText(prompt)}</div> : null}
            {e.partial_content ? <div>delta: {shortText(e.partial_content, 160)}</div> : null}
            {e.content ? <div>content: {shortText(e.content)}</div> : null}
            {traceText ? <div>running_trace: {shortText(traceText, 260)}</div> : null}
          </div>
        );
      })}
    </div>
  );
}
