# ProcessCompliance锛堜腑鏂囩増锛?
[English](./README.md)

<p align="center">
  <b>鍦ㄧ嚎娴佺▼鍚堣鐩戞帶绯荤粺锛氶泦鎴愰娴嬨€佺煡璇嗘绱笌澶氭櫤鑳戒綋瀹℃煡銆?/b>
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

ProcessCompliance 鐢ㄤ簬鍒嗘瀽浜嬩欢鏃ュ織涓庤繍琛屼腑杞ㄨ抗锛岄娴嬫祦绋嬪悗缁姸鎬侊紝妫€绱㈠悎瑙勭浉鍏宠瘉鎹紝骞惰緭鍑哄彲渚?API/鍓嶇鐩存帴娑堣垂鐨勭粨鏋勫寲缁撴灉銆?
褰撳墠椤圭洰閲囩敤鍚庣鏈湴鍖呮灦鏋勶細`backend/process_compliance/...`銆?
---

## Features

- 妯″瀷鍑嗗姝ラ锛氳嚜鍔ㄦ鏌?`main/model`锛岀己澶辨椂瑙﹀彂璁粌銆?- 鐭ヨ瘑搴撳噯澶囨楠わ細鑷姩妫€鏌?`main/knowledge_base`锛岀己澶辨椂鑷姩鏋勫缓鐭ヨ瘑鏂囦欢涓庡悜閲忓簱銆?- 瀹炴椂杩愯缂栨帓锛氭牎楠岃緭鍏ャ€佹墽琛岄娴?妫€绱?Agent锛屽苟杩斿洖缁撴瀯鍖?`AnalysisResult`銆?- 娴佸紡浜嬩欢锛氭敮鎸?SSE 浜嬩欢锛坄run_started`銆佹楠や簨浠躲€丄gent 浜嬩欢銆乣final_result`銆乣run_completed`锛夈€?- 鍏ㄦ爤鑱旇皟锛欶astAPI 鍚庣銆丷eact 鍓嶇銆丆LI 璋冭瘯鍏ュ彛銆?
---

## Architecture

```text
ProcessCompliance
鈹溾攢鈹€ Data Layer
鈹?  鈹溾攢鈹€ event log / running trace loading
鈹?  鈹斺攢鈹€ validation + trace conversion
鈹溾攢鈹€ Service Layer
鈹?  鈹溾攢鈹€ PredictionService
鈹?  鈹溾攢鈹€ KnowledgeService
鈹?  鈹斺攢鈹€ AgentService
鈹溾攢鈹€ Orchestration Layer
鈹?  鈹斺攢鈹€ OnlineMonitoringService (single pipeline entry)
鈹斺攢鈹€ Delivery Layer
    鈹溾攢鈹€ FastAPI (/api/*)
    鈹溾攢鈹€ SSE stream (/api/runs/{run_id}/stream)
    鈹斺攢鈹€ React frontend + CLI
```

---

## Project Structure

```text
main/
鈹溾攢鈹€ configs/
鈹溾攢鈹€ data/
鈹溾攢鈹€ artifacts/
鈹溾攢鈹€ backend/process_compliance/
鈹溾攢鈹€ backend/
鈹溾攢鈹€ frontend/
鈹溾攢鈹€ scripts/
鈹斺攢鈹€ tests/
```

| 璺緞 | 璇存槑 |
|---|---|
| `backend/process_compliance/` | 鍚庣鏍稿績鍖咃紙config/data/prediction/knowledge/agents/online锛?|
| `backend/` | FastAPI 搴旂敤銆佽矾鐢变笌杩愯鏈嶅姟 |
| `frontend/` | React + TypeScript + Vite 鍓嶇 |
| `scripts/run_online_monitoring.py` | 绔埌绔?CLI 璋冭瘯鍏ュ彛 |
| `configs/default.yaml` | 榛樿杩愯閰嶇疆锛堟暟鎹泦銆佽矾寰勩€乷llama銆侀娴嬪弬鏁帮級 |
| `artifacts/runs/` | 姣忔杩愯杈撳嚭锛坄final_report.json`銆乣agent_events.jsonl`锛?|

---

## Quick Start

### 1. 鍏嬮殕浠撳簱

```bash
git clone <repository-url>
cd ProcessCompliance/main
```

### 2. 鍒涘缓铏氭嫙鐜

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. 瀹夎渚濊禆

```bash
pip install -r requirements.txt
pip install fastapi uvicorn python-multipart pydantic pyyaml pandas pytest httpx
```

鍙€夛紙鍚敤鐪熷疄 LLM/Embedding锛夛細

```bash
pip install langchain langchain-community langgraph langchain-ollama faiss-cpu
```

### 4. 鍑嗗鏁版嵁涓庨厤缃?
榛樿閰嶇疆鏂囦欢锛?
```text
configs/default.yaml
```

榛樿鏁版嵁璺緞锛?
```text
data/BPIC20_D.csv
data/running_trace/BPIC20_D_trace.csv
```

### 5. 鍚姩椤圭洰

鍚庣锛?
```bash
uvicorn backend.main:app --reload --port 5174
```

鍓嶇锛?
```bash
cd frontend
npm install
npm run dev
```

CLI锛?
```bash
python scripts/run_online_monitoring.py --event-log data/BPIC20_D.csv --running-trace data/running_trace/BPIC20_D_trace.csv --dataset-name BPIC20_D --config configs/default.yaml
```

### 6. 鍓嶇鎵嬪姩杩愯锛堟棩蹇椾笌 trace 杈撳叆锛?
1. 鍦?`main/` 鍚姩鍚庣锛?
```bash
uvicorn backend.main:app --reload --port 5174
```

2. 鍦ㄥ彟涓€涓粓绔惎鍔ㄥ墠绔細

```bash
cd frontend
npm install
npm run dev
```

3. 鎵撳紑 Vite 鏄剧ず鍦板潃锛堥€氬父 `http://localhost:5173`锛夛紝璁块棶 `/run`銆?
4. 濉啓锛?- `event_log_path`: `data/BPIC20_D.csv`
- `running_trace_path`: `data/running_trace/BPIC20_D_trace.csv`
- `dataset_name`: `BPIC20_D`

5. 鐐瑰嚮 `Run Analysis`銆?
6. 瑙傚療锛?- pipeline 姝ラ鐘舵€佹洿鏂帮紙鍚ā鍨嬪噯澶囥€佺煡璇嗗簱鍑嗗锛?- Agent 瀹炴椂杈撳嚭锛坄check_agent`銆乣predict_agent`銆乣summary_agent`锛?- `final_result` / `run_completed` 鍚庢樉绀烘渶缁堢粨鏋?
---

## Usage

### 鍩虹 API 鐢ㄦ硶

```bash
curl http://localhost:5174/api/health
curl -X POST http://localhost:5174/api/runs -H "Content-Type: application/json" -d "{\"event_log_path\":\"data/BPIC20_D.csv\",\"running_trace_path\":\"data/running_trace/BPIC20_D_trace.csv\",\"dataset_name\":\"BPIC20_D\"}"
```

### Python API 鐢ㄦ硶

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

| 鍑芥暟 / 绫?| 璇存槑 |
|---|---|
| `OnlineMonitoringService` | 缁熶竴缂栨帓鍏ュ彛锛氭ā鍨嬪噯澶囥€佺煡璇嗗簱鍑嗗銆佹牎楠屻€侀娴嬨€佹绱€丄gent 瀹℃煡銆佺粨鏋滀繚瀛?|
| `analyze(...)` | 鎵ц瀹屾暣 pipeline 骞跺彂鍑虹粨鏋勫寲浜嬩欢 |

### `backend/services/run_service.py`

| 鍑芥暟 / 绫?| 璇存槑 |
|---|---|
| `RunService` | 绠＄悊寮傛 run 鐘舵€併€佷簨浠堕槦鍒椼€佺粨鏋滃瓨鍌ㄤ笌 SSE 鍒嗗彂 |
| `stream_events(run_id)` | 浠?`text/event-stream` 鏂瑰紡鎺ㄩ€佸疄鏃朵簨浠?|

### `backend/process_compliance/agents/service.py`

| 鍑芥暟 / 绫?| 璇存槑 |
|---|---|
| `AgentService` | 鎵ц褰撳墠鍚堣銆佹湭鏉ラ闄┿€佹渶缁堟€荤粨 |
| `check_current_compliance(...)` | 褰撳墠鍚堣鍒ゅ畾 |
| `analyze_future_risk(...)` | 鏈潵椋庨櫓鍒ゅ畾 |
| `summarize(...)` | 姹囨€荤粨璁?|

---

## Workflow

```text
杈撳叆璺緞锛坋vent log + running trace锛?   -> Model preparation (load/train)
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

涓婚厤缃枃浠讹細

```text
configs/default.yaml
```

| 鍙傛暟 | 榛樿鍊?| 璇存槑 |
|---|---|---|
| `dataset.name` | `BPIC20_D` | 鏁版嵁闆嗘爣璇?|
| `dataset.event_log_path` | `data/BPIC20_D.csv` | 浜嬩欢鏃ュ織璺緞 |
| `dataset.running_trace_path` | `data/running_trace/BPIC20_D_trace.csv` | 杩愯杞ㄨ抗璺緞 |
| `paths.run_dir` | `artifacts/runs` | 杩愯杈撳嚭鐩綍 |
| `paths.knowledge_base_dir` | `artifacts/knowledge_base` | 鐭ヨ瘑搴撶洰褰?|
| `ollama.chat_model` | `qwen3:8b` | Agent 瀵硅瘽妯″瀷 |
| `ollama.embedding_model` | `qwen3-embedding:8b` | 鍚戦噺妯″瀷 |

---

## Data Preparation

CSV 鏈€浣庡繀闇€鍒楋細

| 鍒楀悕 | 璇存槑 |
|---|---|
| `case` | case 鏍囪瘑 |
| `concept:name` | 娲诲姩鍚嶇О |

鍙€夊垪锛堢己澶辨椂鍙檷绾у鐞嗭級锛?
| 鍒楀悕 | 璇存槑 |
|---|---|
| `org:resource` | 璧勬簮 |
| `org:role` | 瑙掕壊 |

---

## Training

濡傞渶鎵嬪姩璁粌鏃х増棰勬祴妯″瀷锛?
```bash
python scripts/train_models.py
```

妯″瀷浜х墿鐩綍锛?
```text
artifacts/models/
```

---

## Inference / Prediction

`PredictionService` 鍦?pipeline 涓緭鍑猴細

```text
next_activity
outcome
remaining_time
```

鑻ユā鍨嬭繍琛屼笉鍙敤锛屾湇鍔′細杩斿洖鍙楁帶 unknown/None锛宲ipeline 涓嶄細鏁翠綋宕╂簝銆?
---

## API Reference

| 鏂规硶 | 璺緞 | 璇存槑 |
|---|---|---|
| `GET` | `/api/health` | 鍋ュ悍妫€鏌?|
| `POST` | `/api/analyze` | 鐩存帴鍒嗘瀽锛堥潪 run 鐢熷懡鍛ㄦ湡锛?|
| `POST` | `/api/runs` | 鍒涘缓鍚庡彴 run |
| `GET` | `/api/runs` | run 鍒楄〃 |
| `GET` | `/api/runs/{run_id}` | 鑾峰彇 run 鏈€缁堢粨鏋?|
| `GET` | `/api/runs/{run_id}/stream` | SSE 瀹炴椂浜嬩欢娴?|
| `POST` | `/api/files/upload` | 涓婁紶 CSV 鏂囦欢 |

绀轰緥锛?
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

| 鍙傛暟 | 璇存槑 |
|---|---|
| `--event-log` | 浜嬩欢鏃ュ織 CSV 璺緞 |
| `--running-trace` | 杩愯杞ㄨ抗 CSV 璺緞 |
| `--dataset-name` | 鏁版嵁闆嗗悕绉拌鐩?|
| `--config` | YAML 閰嶇疆璺緞 |

---

## Outputs

```text
artifacts/runs/{run_id}/
鈹溾攢鈹€ final_report.json
鈹斺攢鈹€ agent_events.jsonl
```

| 杈撳嚭 | 璇存槑 |
|---|---|
| `final_report.json` | 缁撴瀯鍖栨渶缁堢粨鏋?|
| `agent_events.jsonl` | 鍏ㄩ噺浜嬩欢鏃ュ織锛堝洖鏀?鎺掗殰锛?|

---

## Dependencies

涓讳緷璧栨枃浠讹細

```text
requirements.txt
```

褰撳墠鍚庣/鍓嶇鑱旇皟甯哥敤渚濊禆锛?
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

| 鏈嶅姟 | 鐢ㄩ€?|
|---|---|
| Ollama | 鏈湴 LLM 涓?Embedding 鏈嶅姟 |

---

## Known Issues

- 鑻?`langchain_ollama` 鎴?Ollama 涓嶅彲鐢紝Agent 姝ラ浼氳繑鍥炲彈鎺ч檷绾ф秷鎭€?- 鑻ュ悜閲忓簱浜х墿缂哄け锛屾绱㈢粨鏋滃彲鑳戒负绌恒€?- 鑻ユā鍨嬩骇鐗╃己澶憋紝棰勬祴瀛楁鍙兘鏄?unknown/None銆?- 缃戠粶鎴栦唬鐞嗕笉绋冲畾鏃?SSE 鍙兘閲嶈繛锛屽墠绔細鑷姩鍚敤 polling fallback 淇濇寔杩涘害鏇存柊銆?- 鏈畨瑁?Node.js + npm 鏃讹紝鍓嶇鏃犳硶鍚姩銆?
---

## Development Notes

- 当前代码库已不再使用根目录的旧兼容入口脚本。
- 新代码导入路径建议使用 backend.process_compliance...。
- 联调建议使用 /api/runs + SSE，并检查 artifacts/runs/{run_id}/agent_events.jsonl。

---

## Roadmap

- [ ] 澧炲姞涓€閿幆澧冨垵濮嬪寲鑴氭湰锛圥ython + Node + 鍙€?Ollama 妫€鏌ワ級
- [ ] 澧炲姞鏇村 SSE 鐩稿叧闆嗘垚娴嬭瘯
- [ ] 澧炲姞澶氭暟鎹泦/澶氭棩蹇?schema 绀轰緥
- [ ] 澧炲姞 backend + frontend + Ollama 鐨?Docker Compose 鏂规

---

## Contributing

娆㈣繋璐＄尞銆傝浣跨敤鍔熻兘鍒嗘敮骞舵彁浜?PR锛?
```bash
git checkout -b feature/your-change
git commit -m "Describe your change"
git push origin feature/your-change
```

---

## License

褰撳墠浠撳簱鏈彂鐜版槑纭?License 鏂囦欢銆傚彂甯冨墠寤鸿琛ュ厖 `LICENSE`銆?
---

## Acknowledgements

- BPIC 娴佺▼鏁版嵁鐢熸€?- FastAPI 涓?React 鐢熸€?- LangChain / Ollama / FAISS 鐩稿叧寮€婧愮粍浠?
