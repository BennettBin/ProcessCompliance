export interface AnalyzeRequest {
  event_log_path: string;
  running_trace_path: string;
  dataset_name?: string;
  config_path?: string;
}

export interface RunCreateResponse {
  run_id: string;
  status: string;
}

export interface TraceEvent {
  case_id?: string | null;
  activity?: string | null;
  resource?: string | null;
  role?: string | null;
  execution_time?: number | null;
  timestamp?: string | null;
  raw?: Record<string, unknown>;
}

export interface PredictionResult {
  next_activity?: string | null;
  next_activity_confidence?: number | null;
  outcome?: string | null;
  outcome_confidence?: number | null;
  remaining_time?: number | null;
  remaining_time_unit?: "seconds" | "minutes" | "hours" | "days";
  debug_raw_text?: string | null;
}

export interface RuleEvidence {
  rule_id?: string | null;
  rule_text?: string | null;
  matched?: boolean | null;
  confidence?: number | null;
  evidence_text?: string | null;
  source?: "rule_vectorstore" | "log_vectorstore" | "agent" | "manual" | "unknown";
}

export interface ComplianceResult {
  current_status: "compliant" | "non_compliant" | "unknown";
  future_risk: "high" | "medium" | "low" | "unknown";
  violated_rules?: RuleEvidence[];
  risk_rules?: RuleEvidence[];
  summary?: string | null;
}

export interface AgentDecision {
  agent_name?: string | null;
  decision: "yes" | "no" | "unknown";
  confidence?: number | null;
  comment?: string | null;
  raw_response: string;
}

export interface AgentReview {
  check_agent?: AgentDecision | null;
  predict_agent?: AgentDecision | null;
  summary_agent?: AgentDecision | null;
  rule_check_agent?: AgentDecision | null;
  second_check_agent?: AgentDecision | null;
  debate_rounds?: number;
  consensus_reached?: boolean;
}

export interface AnalysisResult {
  run_id: string;
  status: "success" | "partial_success" | "failed";
  dataset_name: string;
  event_log_path: string;
  running_trace_path: string;
  current_trace: TraceEvent[];
  prediction: PredictionResult;
  compliance: ComplianceResult;
  agent_review: AgentReview;
  message?: string | null;
  meta?: Record<string, unknown>;
}

export type AgentEventType =
  | "run_started"
  | "run_completed"
  | "run_failed"
  | "step_started"
  | "step_completed"
  | "agent_started"
  | "agent_token"
  | "agent_message_completed"
  | "debate_round_started"
  | "debate_round_completed"
  | "final_result";

export interface AgentEvent {
  run_id: string;
  event_id: string;
  timestamp: string;
  type: AgentEventType;
  agent_name?: string | null;
  round_index?: number | null;
  step_name?: string | null;
  content?: string | null;
  partial_content?: string | null;
  payload?: Record<string, unknown>;
}

export interface RunSummary {
  run_id: string;
  status: string;
  report_path: string;
}

export interface DatasetConfig {
  name: string;
  event_log_path: string;
  raw_xes_path: string;
  running_trace_path: string;
}

export interface PathsConfig {
  artifact_dir: string;
  knowledge_base_dir: string;
  model_dir: string;
  processed_feature_dir: string;
  run_dir: string;
  upload_dir: string;
}

export interface OllamaConfig {
  chat_model: string;
  embedding_model: string;
  base_url: string;
}

export interface AgentConfig {
  debate_threshold: number;
  max_rounds: number;
}

export interface PredictionConfig {
  max_prefix_length: number;
  device: string;
}

export interface LoggingConfig {
  level: string;
}

export interface AppSettings {
  dataset: DatasetConfig;
  paths: PathsConfig;
  ollama: OllamaConfig;
  agent: AgentConfig;
  prediction: PredictionConfig;
  logging: LoggingConfig;
}

export interface SettingsResponse {
  config: AppSettings;
  config_path: string;
}
