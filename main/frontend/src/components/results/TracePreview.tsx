import type { TraceEvent } from "../../types/processCompliance";

type Props = {
  trace?: TraceEvent[] | null;
};

export default function TracePreview({ trace }: Props) {
  if (!trace || trace.length === 0) {
    return <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12 }}>No trace events.</div>;
  }

  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12, overflowX: "auto" }}>
      <h3 style={{ marginTop: 0 }}>Trace Preview</h3>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th align="left">Case</th>
            <th align="left">Activity</th>
            <th align="left">Resource</th>
            <th align="left">Role</th>
            <th align="left">Execution Time</th>
            <th align="left">Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {trace.map((e, idx) => (
            <tr key={`${e.case_id ?? "case"}-${idx}`}>
              <td>{e.case_id ?? "N/A"}</td>
              <td>{e.activity ?? "N/A"}</td>
              <td>{e.resource ?? "N/A"}</td>
              <td>{e.role ?? "N/A"}</td>
              <td>{e.execution_time ?? "N/A"}</td>
              <td>{e.timestamp ?? "N/A"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

