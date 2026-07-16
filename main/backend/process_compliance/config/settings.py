from pydantic import BaseModel, Field


class DatasetConfig(BaseModel):
    name: str = "BPIC20_D"
    event_log_path: str = "dataset/new_data/BPIC20_D.csv"
    raw_xes_path: str = "dataset/raw_data/BPIC20_D.xes"
    running_trace_path: str = "dataset/running_trace/BPIC20_D_trace.csv"


class PathsConfig(BaseModel):
    artifact_dir: str = "artifacts"
    knowledge_base_dir: str = "knowledge_base"
    model_dir: str = "model"
    processed_feature_dir: str = "artifacts/processed_features"
    run_dir: str = "artifacts/runs"
    upload_dir: str = "dataset/uploads"


class OllamaConfig(BaseModel):
    chat_model: str = "qwen3:8b"
    embedding_model: str = "qwen3-embedding:8b"
    base_url: str = "http://localhost:11434"


class AgentConfig(BaseModel):
    debate_threshold: float = 0.7
    max_rounds: int = 3


class PredictionConfig(BaseModel):
    max_prefix_length: int = 20
    device: str = "auto"


class LoggingConfig(BaseModel):
    level: str = "INFO"


class AppConfig(BaseModel):
    dataset: DatasetConfig = Field(default_factory=DatasetConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    prediction: PredictionConfig = Field(default_factory=PredictionConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
