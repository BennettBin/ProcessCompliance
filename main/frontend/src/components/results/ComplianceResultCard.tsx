import type { ComplianceResult } from "../../types/processCompliance";

type Props = {
  compliance?: ComplianceResult | null;
};

function riskStyle(risk: ComplianceResult["future_risk"]) {
  if (risk === "high") return { background: "#ffe9e9", color: "#b42318" };
  if (risk === "medium") return { background: "#fff6e5", color: "#b54708" };
  if (risk === "low") return { background: "#ecfdf3", color: "#067647" };
  return { background: "#f2f4f7", color: "#344054" };
}

export default function ComplianceResultCard({ compliance }: Props) {
  if (!compliance) {
    return <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12 }}>No compliance result yet.</div>;
  }

  const style = riskStyle(compliance.future_risk);
  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12 }}>
      <h3 style={{ marginTop: 0 }}>Compliance Result</h3>
      <div><strong>Current Status:</strong> {compliance.current_status}</div>
      <div style={{ marginTop: 8 }}>
        <span style={{ ...style, borderRadius: 999, padding: "3px 10px", display: "inline-block" }}>
          Future Risk: {compliance.future_risk}
        </span>
      </div>
    </div>
  );
}

