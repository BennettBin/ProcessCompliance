import type { RuleEvidence } from "../../types/processCompliance";

type Props = {
  relevant_rules?: RuleEvidence[] | null;
  violated_rules?: RuleEvidence[] | null;
};

function RulesSection({ title, items }: { title: string; items?: RuleEvidence[] | null }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <h4 style={{ margin: "0 0 8px" }}>{title}</h4>
      {!items || items.length === 0 ? (
        <p style={{ margin: 0 }}>No rules.</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th align="left">Rule ID</th>
              <th align="left">Rule Text</th>
              <th align="left">Confidence</th>
              <th align="left">Source</th>
            </tr>
          </thead>
          <tbody>
            {items.map((r, idx) => (
              <tr key={`${r.rule_id ?? "rule"}-${idx}`}>
                <td>{r.rule_id ?? "N/A"}</td>
                <td>{r.rule_text ?? r.evidence_text ?? "N/A"}</td>
                <td>{r.confidence ?? "N/A"}</td>
                <td>{r.source ?? "unknown"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default function RelevantRulesTable({ relevant_rules, violated_rules }: Props) {
  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12 }}>
      <h3 style={{ marginTop: 0 }}>Rules</h3>
      <RulesSection title="Relevant Rules" items={relevant_rules} />
      <RulesSection title="Violated Rules" items={violated_rules} />
    </div>
  );
}

