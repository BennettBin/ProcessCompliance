import { useEffect, useMemo, useState } from "react";
import { API_BASE_URL } from "../api/client";
import { getSettings, updateSettings } from "../api/settings";
import type { AppSettings } from "../types/processCompliance";

type NumericDrafts = {
  debate_threshold: string;
  max_rounds: string;
  max_prefix_length: string;
};

function parseNumber(v: string): number | null {
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

export default function Settings() {
  const [config, setConfig] = useState<AppSettings | null>(null);
  const [drafts, setDrafts] = useState<NumericDrafts>({
    debate_threshold: "",
    max_rounds: "",
    max_prefix_length: "",
  });
  const [configPath, setConfigPath] = useState<string>("");
  const [status, setStatus] = useState<string>("");
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    (async () => {
      try {
        const res = await getSettings();
        setConfig(res.config);
        setConfigPath(res.config_path);
        setDrafts({
          debate_threshold: String(res.config.agent.debate_threshold),
          max_rounds: String(res.config.agent.max_rounds),
          max_prefix_length: String(res.config.prediction.max_prefix_length),
        });
      } catch (e) {
        setError(e instanceof Error ? e.message : "Load settings failed.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const update = <K extends keyof AppSettings, F extends keyof AppSettings[K]>(
    section: K,
    field: F,
    value: AppSettings[K][F],
  ) => {
    setConfig((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        [section]: {
          ...prev[section],
          [field]: value,
        },
      };
    });
  };

  const validationErrors = useMemo(() => {
    if (!config) return ["Configuration is empty."];
    const errors: string[] = [];

    const debate = parseNumber(drafts.debate_threshold);
    const rounds = parseNumber(drafts.max_rounds);
    const prefixLen = parseNumber(drafts.max_prefix_length);

    if (debate === null || debate < 0 || debate > 1) {
      errors.push("agent.debate_threshold must be a number between 0 and 1.");
    }
    if (rounds === null || !Number.isInteger(rounds) || rounds < 1 || rounds > 10) {
      errors.push("agent.max_rounds must be an integer between 1 and 10.");
    }
    if (prefixLen === null || !Number.isInteger(prefixLen) || prefixLen < 1 || prefixLen > 200) {
      errors.push("prediction.max_prefix_length must be an integer between 1 and 200.");
    }

    if (!config.dataset.name.trim()) errors.push("dataset.name is required.");
    if (!config.dataset.event_log_path.trim()) errors.push("dataset.event_log_path is required.");
    if (!config.dataset.raw_xes_path.trim()) errors.push("dataset.raw_xes_path is required.");
    if (!config.dataset.running_trace_path.trim()) errors.push("dataset.running_trace_path is required.");
    if (!config.ollama.base_url.trim()) errors.push("ollama.base_url is required.");
    if (!config.ollama.chat_model.trim()) errors.push("ollama.chat_model is required.");
    if (!config.ollama.embedding_model.trim()) errors.push("ollama.embedding_model is required.");
    if (!config.paths.knowledge_base_dir.trim()) errors.push("paths.knowledge_base_dir is required.");
    if (!config.paths.model_dir.trim()) errors.push("paths.model_dir is required.");
    if (!config.paths.run_dir.trim()) errors.push("paths.run_dir is required.");

    return errors;
  }, [config, drafts]);

  const save = async () => {
    if (!config) return;
    setSaving(true);
    setError("");
    setStatus("");

    try {
      if (validationErrors.length > 0) {
        setError(validationErrors[0]);
        return;
      }

      const debate = Number(drafts.debate_threshold);
      const rounds = Number(drafts.max_rounds);
      const prefixLen = Number(drafts.max_prefix_length);

      const nextConfig: AppSettings = {
        ...config,
        agent: {
          ...config.agent,
          debate_threshold: debate,
          max_rounds: rounds,
        },
        prediction: {
          ...config.prediction,
          max_prefix_length: prefixLen,
        },
      };

      const res = await updateSettings(nextConfig);
      setConfig(res.config);
      setConfigPath(res.config_path);
      setDrafts({
        debate_threshold: String(res.config.agent.debate_threshold),
        max_rounds: String(res.config.agent.max_rounds),
        max_prefix_length: String(res.config.prediction.max_prefix_length),
      });
      setStatus("Saved. New parameters will be used for subsequent runs.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save settings failed.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="page">
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle">Loading...</p>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="page">
        <h1 className="page-title">Settings</h1>
        <div className="error">{error || "Settings unavailable."}</div>
      </div>
    );
  }

  return (
    <div className="page">
      <h1 className="page-title">Settings</h1>
      <p className="page-subtitle">Edit runtime parameters and persist to YAML config.</p>

      <div className="card" style={{ marginTop: 12 }}>
        <div className="kv" style={{ marginBottom: 8 }}>
          <strong>Backend URL:</strong> {API_BASE_URL}
        </div>
        <div className="kv">
          <strong>Config File:</strong> {configPath}
        </div>
      </div>

      <div className="grid-2" style={{ marginTop: 12 }}>
        <div className="card">
          <h3 className="section-title">Dataset</h3>
          <label className="label">name
            <input className="input" title="Dataset identifier, e.g. BPIC20_D." value={config.dataset.name} onChange={(e) => update("dataset", "name", e.target.value)} />
          </label>
          <label className="label">event_log_path
            <input className="input" title="CSV event log path. Example: data/BPIC20_D.csv" value={config.dataset.event_log_path} onChange={(e) => update("dataset", "event_log_path", e.target.value)} />
          </label>
          <label className="label">raw_xes_path
            <input className="input" title="Raw XES file path. Example: data/BPIC20_D.xes" value={config.dataset.raw_xes_path} onChange={(e) => update("dataset", "raw_xes_path", e.target.value)} />
          </label>
          <label className="label">running_trace_path
            <input className="input" title="Running trace CSV path. Example: data/running_trace/BPIC20_D_trace.csv" value={config.dataset.running_trace_path} onChange={(e) => update("dataset", "running_trace_path", e.target.value)} />
          </label>
        </div>

        <div className="card">
          <h3 className="section-title">Paths</h3>
          <label className="label">artifact_dir<input className="input" title="Root artifacts directory." value={config.paths.artifact_dir} onChange={(e) => update("paths", "artifact_dir", e.target.value)} /></label>
          <label className="label">knowledge_base_dir<input className="input" title="Knowledge files/vectorstore directory." value={config.paths.knowledge_base_dir} onChange={(e) => update("paths", "knowledge_base_dir", e.target.value)} /></label>
          <label className="label">model_dir<input className="input" title="Model artifact directory." value={config.paths.model_dir} onChange={(e) => update("paths", "model_dir", e.target.value)} /></label>
          <label className="label">processed_feature_dir<input className="input" title="Processed feature directory." value={config.paths.processed_feature_dir} onChange={(e) => update("paths", "processed_feature_dir", e.target.value)} /></label>
          <label className="label">run_dir<input className="input" title="Per-run output directory." value={config.paths.run_dir} onChange={(e) => update("paths", "run_dir", e.target.value)} /></label>
          <label className="label">upload_dir<input className="input" title="Uploaded file directory." value={config.paths.upload_dir} onChange={(e) => update("paths", "upload_dir", e.target.value)} /></label>
        </div>

        <div className="card">
          <h3 className="section-title">Ollama</h3>
          <label className="label">chat_model<input className="input" title="LLM model name. Example: qwen3:8b" value={config.ollama.chat_model} onChange={(e) => update("ollama", "chat_model", e.target.value)} /></label>
          <label className="label">embedding_model<input className="input" title="Embedding model name. Example: qwen3-embedding:8b" value={config.ollama.embedding_model} onChange={(e) => update("ollama", "embedding_model", e.target.value)} /></label>
          <label className="label">base_url<input className="input" title="Ollama server URL. Example: http://localhost:11434" value={config.ollama.base_url} onChange={(e) => update("ollama", "base_url", e.target.value)} /></label>
        </div>

        <div className="card">
          <h3 className="section-title">Agent & Prediction</h3>
          <label className="label">
            debate_threshold
            <input
              className="input"
              type="number"
              min={0}
              max={1}
              step={0.01}
              title="Number between 0 and 1. Higher means stricter consensus requirement."
              value={drafts.debate_threshold}
              onChange={(e) => setDrafts((d) => ({ ...d, debate_threshold: e.target.value }))}
            />
          </label>
          <label className="label">
            max_rounds
            <input
              className="input"
              type="number"
              min={1}
              max={10}
              step={1}
              title="Integer 1-10. Maximum debate rounds per trace step."
              value={drafts.max_rounds}
              onChange={(e) => setDrafts((d) => ({ ...d, max_rounds: e.target.value }))}
            />
          </label>
          <label className="label">
            max_prefix_length
            <input
              className="input"
              type="number"
              min={1}
              max={200}
              step={1}
              title="Integer 1-200. Upper bound for prediction prefix length."
              value={drafts.max_prefix_length}
              onChange={(e) => setDrafts((d) => ({ ...d, max_prefix_length: e.target.value }))}
            />
          </label>

          <label className="label">prediction.device
            <select className="input" title="Prediction runtime device preference." value={config.prediction.device} onChange={(e) => update("prediction", "device", e.target.value)}>
              <option value="auto">auto</option>
              <option value="cpu">cpu</option>
              <option value="cuda">cuda</option>
            </select>
          </label>

          <label className="label">logging.level
            <select className="input" title="Application logging level." value={config.logging.level} onChange={(e) => update("logging", "level", e.target.value)}>
              <option value="DEBUG">DEBUG</option>
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          </label>
        </div>
      </div>

      {validationErrors.length > 0 && (
        <div className="card" style={{ marginTop: 12 }}>
          <strong>Validation</strong>
          <div className="stack" style={{ marginTop: 8 }}>
            {validationErrors.map((e) => (
              <div key={e} className="error">
                {e}
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ marginTop: 12 }}>
        <button className="btn" onClick={save} disabled={saving || validationErrors.length > 0}>
          {saving ? "Saving..." : "Save Settings"}
        </button>
      </div>

      {status && <div className="card" style={{ marginTop: 12 }}>{status}</div>}
      {error && <div className="error" style={{ marginTop: 12 }}>{error}</div>}
    </div>
  );
}

