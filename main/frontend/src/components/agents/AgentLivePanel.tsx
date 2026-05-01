import { useMemo } from "react";
import type { AgentEvent } from "../../types/processCompliance";
import AgentDebateTimeline from "./AgentDebateTimeline";
import AgentEventLog from "./AgentEventLog";
import AgentMessageCard from "./AgentMessageCard";

type Props = {
  events: AgentEvent[];
};

type AgentStatus = "waiting" | "running" | "completed" | "failed";

type AgentView = {
  agentName: string;
  status: AgentStatus;
  content: string;
  decision?: string | null;
  confidence?: string | null;
};

function extractSignal(content: string, key: "CONSENSUS" | "CONFIDENCE"): string | null {
  const regex = new RegExp(`${key}:\\s*([^\\n\\r]+)`, "i");
  const match = content.match(regex);
  return match?.[1]?.trim() ?? null;
}

function statusClass(status: AgentStatus): string {
  if (status === "running") return "status-badge status-running";
  if (status === "completed") return "status-badge status-completed";
  if (status === "failed") return "status-badge status-failed";
  return "status-badge status-pending";
}

export default function AgentLivePanel({ events }: Props) {
  const agents = useMemo(() => {
    const map = new Map<string, AgentView>();

    for (const e of events) {
      if (!e.agent_name) continue;
      const name = e.agent_name;
      if (!map.has(name)) {
        map.set(name, { agentName: name, status: "waiting", content: "" });
      }
      const current = map.get(name)!;

      if (e.type === "agent_started") {
        current.status = "running";
      } else if (e.type === "agent_token") {
        current.status = current.status === "waiting" ? "running" : current.status;
        current.content = (current.content ?? "") + (e.partial_content ?? "");
      } else if (e.type === "agent_message_completed") {
        current.status = "completed";
        current.content = e.content ?? current.content;
      }

      if (e.type === "run_failed" && current.status !== "completed") {
        current.status = "failed";
      }

      const decision = extractSignal(current.content, "CONSENSUS");
      const confidence = extractSignal(current.content, "CONFIDENCE");
      current.decision = decision;
      current.confidence = confidence;
      map.set(name, current);
    }

    return Array.from(map.values()).sort((a, b) => a.agentName.localeCompare(b.agentName));
  }, [events]);

  return (
    <div className="stack">
      <div>
        <h3 className="section-title">Agent Live Panel</h3>
        {agents.length === 0 ? (
          <p className="muted">No agent events yet.</p>
        ) : (
          <div className="stack">
            {agents.map((a) => (
              <div key={a.agentName}>
                <div className="kv" style={{ marginBottom: 6 }}>
                  <strong>{a.agentName}</strong>
                  <span className={statusClass(a.status)}>{a.status}</span>
                  {a.decision ? <span>decision={a.decision}</span> : null}
                  {a.confidence ? <span>confidence={a.confidence}</span> : null}
                </div>
                <AgentMessageCard title={a.agentName} content={a.content} status={a.status} />
              </div>
            ))}
          </div>
        )}
      </div>

      <div>
        <h4 className="section-title">Debate Timeline</h4>
        <AgentDebateTimeline events={events} />
      </div>

      <div>
        <h4 className="section-title">Event Log</h4>
        <AgentEventLog events={events} />
      </div>
    </div>
  );
}
