import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getRun } from "../api/processCompliance";
import type { AnalysisResult } from "../types/processCompliance";
import PredictionSummaryCard from "../components/results/PredictionSummaryCard";
import ComplianceResultCard from "../components/results/ComplianceResultCard";
import TracePreview from "../components/results/TracePreview";
import RelevantRulesTable from "../components/results/RelevantRulesTable";

export default function RunDetail() {
  const { runId } = useParams<{ runId: string }>();
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!runId) return;
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const data = await getRun(runId);
        if (!cancelled) setResult(data);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load run detail.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [runId]);

  return (
    <div className="page">
      <div style={{ marginBottom: 12 }}>
        <Link to="/">Back to Dashboard</Link>
      </div>
      <h1 className="page-title">Run Detail</h1>
      <p className="page-subtitle">
        <strong>Run ID:</strong> {runId ?? "N/A"}
      </p>

      {loading && <p className="muted" style={{ marginTop: 12 }}>Loading...</p>}
      {error && <div className="error" style={{ marginTop: 12 }}>{error}</div>}

      {!loading && !error && result && (
        <div className="stack" style={{ marginTop: 12 }}>
          <PredictionSummaryCard prediction={result.prediction} />
          <ComplianceResultCard compliance={result.compliance} />
          <RelevantRulesTable
            relevant_rules={result.compliance.risk_rules ?? []}
            violated_rules={result.compliance.violated_rules ?? []}
          />
          <TracePreview trace={result.current_trace} />
        </div>
      )}
    </div>
  );
}
