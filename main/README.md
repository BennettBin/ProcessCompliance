# ProcessCompliance

[中文文档](./README.zh.md)

<p align="center">
  <b>Online process compliance monitoring with prediction, retrieval, and multi-agent review.</b>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-blue">
  <img alt="PyTorch" src="https://img.shields.io/badge/PyTorch-Deep%20Learning-ee4c2c">
  <img alt="LangChain" src="https://img.shields.io/badge/LangChain2.0%2B-Agent-green">
  <img alt="Ollama" src="https://img.shields.io/badge/Ollama-Local%20LLM-black">
  <img alt="FAISS" src="https://img.shields.io/badge/FAISS-Vector%20Search-purple">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-Backend-009688">
  <img alt="React" src="https://img.shields.io/badge/React-Frontend-61dafb">
</p>

---

## Overview

ProcessCompliance analyzes event logs and running traces, predicts next process status, retrieves relevant compliance evidence, and produces structured compliance outputs for API/Frontend consumption.

The project now uses a backend-local package architecture (`backend/process_compliance/...`) plus compatibility service entries.

---

## Features

- Model preparation step: auto-checks `main/model` and triggers training when model files are missing.
- Knowledge base preparation step: auto-checks `main/knowledge_base` and builds knowledge files/vectorstores when missing.
- Real-time run orchestration: validate input files, run prediction/retrieval/agent steps, and return a structured `AnalysisResult`.
- Streaming run events: supports SSE events (`run_started`, step events, agent events, `final_result`, `run_completed`).
- Full-stack integration: FastAPI backend, React frontend, and CLI entry for quick debugging.

---

## Architecture

```text
ProcessCompliance
├── Data Layer
│   ├── event log / running trace loading
│   └── validation + trace conversion
├── Service Layer
│   ├── PredictionService
│   ├── KnowledgeService
│   └── AgentService
├── Orchestration Layer
│   └── OnlineMonitoringService (single pipeline entry)
└── Delivery Layer
    ├── FastAPI (/api/*)
    ├── SSE stream (/api/runs/{run_id}/stream)
    └── React frontend + CLI
```

---

## Project Structure

```text
main/
├── configs/
├── data/
├── artifacts/
├── backend/process_compliance/
├── backend/
├── frontend/
├── scripts/
└── tests/
```

| Path | Description |
|---|---|
| `backend/process_compliance/` | Core backend package (config/data/prediction/knowledge/agents/online) |
| `backend/` | FastAPI app, routers, and run/file services |
| `frontend/` | React + TypeScript + Vite UI |
| `scripts/run_online_monitoring.py` | CLI entry to run end-to-end analysis |
| `configs/default.yaml` | Default runtime config (dataset, paths, ollama, prediction) |
| `artifacts/runs/` | Per-run outputs (`final_report.json`, `agent_events.jsonl`) |

---

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ProcessCompliance/main
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install fastapi uvicorn python-multipart pydantic pyyaml pandas pytest httpx
```

Optional (for real LLM/embedding execution instead of fallback messages):

```bash
pip install langchain langchain-community langgraph langchain-ollama faiss-cpu
```

### 4. Prepare Data and Config

Default config file:

```text
configs/default.yaml
```

Default data paths in config:

```text
data/BPIC20_D.csv
data/running_trace/BPIC20_D_trace.csv
```

### 5. Run the Project

Backend:

```bash
uvicorn backend.main:app --reload --port 5174
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

CLI:

```bash
python scripts/run_online_monitoring.py --event-log data/BPIC20_D.csv --running-trace data/running_trace/BPIC20_D_trace.csv --dataset-name BPIC20_D --config configs/default.yaml
```

### 6. Frontend Manual Run (How to input event log and trace)

1. Start backend in `main/`:

```bash
uvicorn backend.main:app --reload --port 5174
```

2. Start frontend in another terminal:

```bash
cd frontend
npm install
npm run dev
```

3. Open the frontend URL shown by Vite (commonly `http://localhost:5173`) and go to `/run`.

4. Fill the form fields:
- `event_log_path`: `data/BPIC20_D.csv`
- `running_trace_path`: `data/running_trace/BPIC20_D_trace.csv`
- `dataset_name`: `BPIC20_D`

5. Click `Run Analysis`.

6. Observe:
- pipeline step status updates
- live agent messages (`check_agent`, `predict_agent`, `summary_agent`)
- final prediction/compliance result after `final_result` / `run_completed`

---

## Usage

### Basic Usage (API)

```bash
curl http://localhost:5174/api/health
curl -X POST http://localhost:5174/api/runs -H "Content-Type: application/json" -d "{\"event_log_path\":\"data/BPIC20_D.csv\",\"running_trace_path\":\"data/running_trace/BPIC20_D_trace.csv\",\"dataset_name\":\"BPIC20_D\"}"
```

### Python API Usage

```python
import asyncio
from backend.process_compliance.config.loader import load_config
from backend.process_compliance.online.runner import OnlineMonitoringService

async def main():
    cfg = load_config()
    svc = OnlineMonitoringService(cfg)
    result = await svc.analyze(
        event_log_path=cfg.dataset.event_log_path,
        running_trace_path=cfg.dataset.running_trace_path,
        dataset_name=cfg.dataset.name,
    )
    print(result.status, result.run_id)

asyncio.run(main())
```

---

## Core Modules

### `backend/process_compliance/online/runner.py`

| Function / Class | Description |
|---|---|
| `OnlineMonitoringService` | Unified orchestration entry for validation, prediction, retrieval, agent review, and output save |
| `analyze(...)` | Executes full pipeline and emits structured events |

### `backend/services/run_service.py`

| Function / Class | Description |
|---|---|
| `RunService` | Manages async run state, queue, result storage, and SSE event delivery |
| `stream_events(run_id)` | Streams run events as `text/event-stream` |

### `backend/process_compliance/agents/service.py`

| Function / Class | Description |
|---|---|
| `AgentService` | Agent check/future-risk/summary execution |
| `check_current_compliance(...)` | Current compliance decision |
| `analyze_future_risk(...)` | Future risk decision |
| `summarize(...)` | Consolidated summary decision |

---

## Workflow

```text
Input paths (event log + running trace)
   -> Model preparation (load/train)
   -> Knowledge base preparation (load/build)
   -> Validation
   -> Running trace load + conversion
   -> PredictionService
   -> KnowledgeService retrieval
   -> AgentService (check/predict/summary)
   -> AnalysisResult + SSE events
   -> Save final_report.json and agent_events.jsonl
```

---

## Configuration

Main config file:

```text
configs/default.yaml
```

| Parameter | Default | Description |
|---|---|---|
| `dataset.name` | `BPIC20_D` | Dataset identifier |
| `dataset.event_log_path` | `data/BPIC20_D.csv` | Event log path |
| `dataset.running_trace_path` | `data/running_trace/BPIC20_D_trace.csv` | Running trace path |
| `paths.run_dir` | `artifacts/runs` | Run output directory |
| `paths.knowledge_base_dir` | `artifacts/knowledge_base` | Vectorstore / knowledge artifact directory |
| `ollama.chat_model` | `qwen3:8b` | Agent chat model |
| `ollama.embedding_model` | `qwen3-embedding:8b` | Embedding model |

---

## Data Preparation

Minimum expected CSV columns:

| Column | Description |
|---|---|
| `case` | Case identifier |
| `concept:name` | Activity name |

Optional columns (gracefully handled if missing):

| Column | Description |
|---|---|
| `org:resource` | Resource |
| `org:role` | Role |

---

## Training

If you need to train legacy prediction models:

```bash
python scripts/train_models.py
```

Expected artifacts location (by current conventions/config):

```text
artifacts/models/
```

---

## Inference / Prediction

Prediction is invoked inside pipeline via `PredictionService`:

```text
next_activity
outcome
remaining_time
```

If model runtime is unavailable, service returns controlled unknown values and keeps pipeline alive.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/analyze` | Direct analyze (non-run lifecycle) |
| `POST` | `/api/runs` | Create background run |
| `GET` | `/api/runs` | List runs |
| `GET` | `/api/runs/{run_id}` | Get final run result |
| `GET` | `/api/runs/{run_id}/stream` | SSE stream for live events |
| `POST` | `/api/files/upload` | Upload CSV file |

Example:

```bash
curl -X POST http://localhost:5174/api/runs \
  -H "Content-Type: application/json" \
  -d "{\"event_log_path\":\"data/BPIC20_D.csv\",\"running_trace_path\":\"data/running_trace/BPIC20_D_trace.csv\",\"dataset_name\":\"BPIC20_D\"}"
```

---

## CLI Reference

```bash
python scripts/run_online_monitoring.py --event-log data/BPIC20_D.csv --running-trace data/running_trace/BPIC20_D_trace.csv --dataset-name BPIC20_D --config configs/default.yaml
```

| Argument | Description |
|---|---|
| `--event-log` | Event log CSV path |
| `--running-trace` | Running trace CSV path |
| `--dataset-name` | Dataset name override |
| `--config` | YAML config path |

---

## Outputs

```text
artifacts/runs/{run_id}/
├── final_report.json
└── agent_events.jsonl
```

| Output | Description |
|---|---|
| `final_report.json` | Structured final analysis result |
| `agent_events.jsonl` | Full event stream record for replay/debug |

---

## Dependencies

Primary dependency file:

```text
requirements.txt
```

Additional runtime dependencies used in current backend/frontend integration:

```text
fastapi
uvicorn
python-multipart
pydantic
pyyaml
pandas
pytest
httpx
```

---

## External Services

| Service | Purpose |
|---|---|
| Ollama | Local LLM + embedding backend for agent/retrieval features |

---

## Known Issues

- If `langchain_ollama` or Ollama service is unavailable, agent steps return controlled fallback messages.
- If vectorstore artifacts are missing, retrieval may return empty evidence.
- If prediction model artifacts are missing, prediction fields can be unknown/None.
- During unstable network/proxy conditions, SSE can reconnect; frontend polling fallback continues to keep progress updates.
- Frontend build/dev cannot run without Node.js + npm installed locally.

---

## Development Notes

- Legacy root compatibility entry scripts are no longer used in the current codebase.
- New imports should prefer `backend.process_compliance...` instead of root-level legacy modules.
- For integration debug, use `/api/runs` + SSE and inspect `artifacts/runs/{run_id}/agent_events.jsonl`.

---

## Roadmap

- [ ] Add full environment bootstrap script (Python + Node + optional Ollama checks)
- [ ] Add more API integration tests for SSE behavior
- [ ] Add dataset/schema examples for multiple logs
- [ ] Add Docker Compose for backend + frontend + Ollama local stack

---

## Contributing

Contributions are welcome. Use a feature branch and open a pull request.

```bash
git checkout -b feature/your-change
git commit -m "Describe your change"
git push origin feature/your-change
```

---

## License

No explicit license file was found in the current project. Consider adding a `LICENSE` file before publishing.

---

## Acknowledgements

- BPIC process data ecosystem
- FastAPI and React tooling ecosystem
- LangChain/Ollama/FAISS related open-source components used by the project

