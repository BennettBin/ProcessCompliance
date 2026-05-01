import type { PredictionResult } from "../../types/processCompliance";

type Props = {
  prediction?: PredictionResult | null;
};

export default function PredictionSummaryCard({ prediction }: Props) {
  if (!prediction) {
    return <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12 }}>No prediction result yet.</div>;
  }

  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12 }}>
      <h3 style={{ marginTop: 0 }}>Prediction Summary</h3>
      <div><strong>Next Activity:</strong> {prediction.next_activity ?? "N/A"}</div>
      <div><strong>Next Activity Confidence:</strong> {prediction.next_activity_confidence ?? "N/A"}</div>
      <div><strong>Outcome:</strong> {prediction.outcome ?? "N/A"}</div>
      <div><strong>Outcome Confidence:</strong> {prediction.outcome_confidence ?? "N/A"}</div>
      <div>
        <strong>Remaining Time:</strong> {prediction.remaining_time ?? "N/A"} {prediction.remaining_time_unit ?? ""}
      </div>
    </div>
  );
}

