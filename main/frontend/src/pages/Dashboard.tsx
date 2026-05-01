import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listRuns } from "../api/processCompliance";
import type { RunSummary } from "../types/processCompliance";

export default function Dashboard() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const data = await listRuns();
        if (!cancelled) setRuns(data);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load runs.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="page">
      <h1 className="page-title">Dashboard</h1>
      <p className="page-subtitle">Monitor recent executions and start a new compliance analysis run.</p>
      <div style={{ marginTop: 12, marginBottom: 8 }}>
        <Link to="/run" className="btn" style={{ display: "inline-flex", alignItems: "center" }}>
          Start New Run
        </Link>
      </div>

      {loading && <p className="muted">Loading runs...</p>}
      {error && <div className="error">{error}</div>}

      {!loading && !error && (
        <div className="card">
          <h3 className="section-title">Recent Runs</h3>
          {runs.length === 0 ? (
            <p className="muted">No runs yet.</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Run ID</th>
                  <th>Status</th>
                  <th>Detail</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr key={r.run_id}>
                    <td>{r.run_id}</td>
                    <td>
                      <span className={`status-badge status-${r.status === "success" ? "completed" : r.status === "failed" ? "failed" : "running"}`}>
                        {r.status}
                      </span>
                    </td>
                    <td>
                      <Link to={`/runs/${r.run_id}`}>Open</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
