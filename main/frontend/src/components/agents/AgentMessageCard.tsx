import { useMemo, useState } from "react";

type Props = {
  title: string;
  content: string;
  status: "waiting" | "running" | "completed" | "failed";
};

function extractSignal(content: string, key: "CONSENSUS" | "CONFIDENCE"): string | null {
  const regex = new RegExp(`${key}:\\s*([^\\n\\r]+)`, "i");
  const match = content.match(regex);
  return match?.[1]?.trim() ?? null;
}

export default function AgentMessageCard({ title, content, status }: Props) {
  const [collapsed, setCollapsed] = useState(false);

  const consensus = useMemo(() => extractSignal(content, "CONSENSUS"), [content]);
  const confidence = useMemo(() => extractSignal(content, "CONFIDENCE"), [content]);

  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <strong>{title}</strong> <span>({status})</span>
        </div>
        <button onClick={() => setCollapsed((v) => !v)}>{collapsed ? "Expand" : "Collapse"}</button>
      </div>

      <div style={{ marginTop: 8, display: "flex", gap: 12, flexWrap: "wrap" }}>
        {consensus && (
          <span style={{ padding: "2px 8px", borderRadius: 6, background: "#eef6ff" }}>
            CONSENSUS: <strong>{consensus}</strong>
          </span>
        )}
        {confidence && (
          <span style={{ padding: "2px 8px", borderRadius: 6, background: "#f3f8ed" }}>
            CONFIDENCE: <strong>{confidence}</strong>
          </span>
        )}
      </div>

      {!collapsed && (
        <pre
          style={{
            marginTop: 10,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            background: "#fafafa",
            border: "1px solid #eee",
            borderRadius: 6,
            padding: 10,
          }}
        >
          {content || "(empty)"}
        </pre>
      )}
    </div>
  );
}

