import { useMemo } from "react";
import type { AgentEvent } from "../../types/processCompliance";

type Props = {
  events: AgentEvent[];
};

type AgentRoundItem = {
  agent: string;
  stepName: string;
  prompt: string;
  response: string;
  responseTimestamp?: string;
};

type RoundCard = {
  round: number;
  started: boolean;
  completed: boolean;
  items: AgentRoundItem[];
};

function shorten(text: string, limit = 600): string {
  const t = (text || "").trim();
  if (t.length <= limit) return t;
  return `${t.slice(0, limit)}...`;
}

export default function AgentDebateTimeline({ events }: Props) {
  const rounds = useMemo(() => {
    const map = new Map<number, RoundCard>();

    const ensureRound = (round: number): RoundCard => {
      if (!map.has(round)) {
        map.set(round, { round, started: false, completed: false, items: [] });
      }
      return map.get(round)!;
    };

    const upsertAgentItem = (roundCard: RoundCard, agent: string, stepName: string): AgentRoundItem => {
      let item = roundCard.items.find((x) => x.agent === agent && x.stepName === stepName);
      if (!item) {
        item = { agent, stepName, prompt: "", response: "" };
        roundCard.items.push(item);
      }
      return item;
    };

    for (const e of events) {
      const roundIndex = e.round_index ?? 0;
      if (roundIndex <= 0) continue;
      const card = ensureRound(roundIndex);

      if (e.type === "debate_round_started") {
        card.started = true;
      }
      if (e.type === "debate_round_completed") {
        card.completed = true;
      }

      if (e.type === "agent_started" && e.agent_name) {
        const payload = (e.payload ?? {}) as Record<string, unknown>;
        const prompt = typeof payload.prompt === "string" ? payload.prompt : "";
        const item = upsertAgentItem(card, e.agent_name, e.step_name ?? "-");
        if (prompt) item.prompt = prompt;
      }

      if (e.type === "agent_message_completed" && e.agent_name) {
        const item = upsertAgentItem(card, e.agent_name, e.step_name ?? "-");
        item.response = e.content ?? "";
        item.responseTimestamp = e.timestamp;
      }
    }

    return Array.from(map.values()).sort((a, b) => a.round - b.round);
  }, [events]);

  if (rounds.length === 0) {
    return <p className="muted">No debate rounds yet.</p>;
  }

  return (
    <div className="stack">
      {rounds.map((round) => (
        <div key={round.round} className="card">
          <div className="kv" style={{ marginBottom: 8 }}>
            <strong>Round {round.round}</strong>
            <span className={`status-badge ${round.completed ? "status-completed" : "status-running"}`}>
              {round.completed ? "completed" : "running"}
            </span>
          </div>

          {round.items.length === 0 ? (
            <p className="muted">No agent prompt/response captured for this round.</p>
          ) : (
            <div className="stack">
              {round.items.map((item, idx) => (
                <div key={`${round.round}-${item.agent}-${idx}`} className="card">
                  <div className="kv" style={{ marginBottom: 6 }}>
                    <strong>{item.agent}</strong>
                    <span className="muted">{item.stepName}</span>
                    {item.responseTimestamp ? <span className="muted">{item.responseTimestamp}</span> : null}
                  </div>

                  <div style={{ marginBottom: 6 }}>
                    <strong>Prompt</strong>
                    <div className="code-block">{item.prompt ? shorten(item.prompt) : "(none)"}</div>
                  </div>

                  <div>
                    <strong>Response</strong>
                    <div className="code-block">{item.response ? shorten(item.response) : "(waiting)"}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
