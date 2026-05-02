# ProcessCompliance（中文文档）

[English](../README.md)

<p align="center">
  <b>在线流程合规监控系统：集成预测、检索与多 Agent 审核。</b>
</p>

---

## 概述

ProcessCompliance 用于分析事件日志与运行中轨迹（running trace），预测流程后续状态，检索相关合规证据，并输出可被 API/前端直接消费的结构化结果。

当前代码采用后端本地包架构：`backend/process_compliance/...`，并提供 CLI 与前后端联调入口。

---

## 核心能力

- 模型准备：自动检查 `main/model`，若缺失则触发训练流程。
- 知识库准备：自动检查 `main/knowledge_base`，若缺失则构建知识文件与向量库。
- 统一编排：通过 `OnlineMonitoringService` 串联验证、预测、检索、Agent 审核与结果落盘。
- 流式事件：支持 SSE 事件（`run_started`、步骤事件、Agent 事件、`final_result`、`run_completed`）。
- 全栈调试：支持 FastAPI 后端、React 前端和 CLI。

---

## 项目结构（当前版本）

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

| 路径 | 说明 |
|---|---|
| `backend/process_compliance/` | 后端核心包（config/data/prediction/knowledge/agents/online） |
| `backend/` | FastAPI 应用、路由、运行与文件服务 |
| `frontend/` | React + TypeScript + Vite 前端 |
| `scripts/run_online_monitoring.py` | 端到端 CLI 入口 |
| `configs/default.yaml` | 默认运行配置（数据集、路径、Ollama、预测参数） |
| `artifacts/runs/` | 每次运行输出（`final_report.json`、`agent_events.jsonl`） |

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/BennettBin/ProcessCompliance
cd ProcessCompliance/main
```

### 2. 创建虚拟环境

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 启动后端

```bash
uvicorn backend.main:app --reload --port 5174
```

### 5. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 6. CLI 运行（可选）

```bash
python scripts/run_online_monitoring.py --event-log data/BPIC20_D.csv --running-trace data/running_trace/BPIC20_D_trace.csv --dataset-name BPIC20_D --config configs/default.yaml
```

---

## 前端使用说明（如何输入日志与 trace）

1. 在 `main/` 目录启动后端：

```bash
uvicorn backend.main:app --reload --port 5174
```

2. 在另一个终端启动前端：

```bash
cd frontend
npm run dev
```

3. 打开 Vite 提示的地址（通常是 `http://localhost:5173`），进入 `/run` 页面。

4. 在表单中输入：
- `event_log_path`：事件日志 CSV 路径
- `running_trace_path`：运行轨迹 CSV 路径
- `dataset_name`：数据集名称（例如 `BPIC20_D`）

5. 点击 `Run Analysis`，页面会实时显示：
- pipeline 步骤状态
- Agent 动态回答（含流式内容）
- 最终预测与合规结果

---

## API 示例

```bash
curl http://localhost:5174/api/health
curl -X POST http://localhost:5174/api/runs -H "Content-Type: application/json" -d "{\"event_log_path\":\"data/BPIC20_D.csv\",\"running_trace_path\":\"data/running_trace/BPIC20_D_trace.csv\",\"dataset_name\":\"BPIC20_D\"}"
```

---

## 常见问题排查

- Ollama 未启动：请先启动 Ollama 并确认模型可用。
- 向量库缺失：运行时会自动尝试构建，也可先手动执行知识库构建脚本。
- 模型文件缺失：运行时会自动进入训练步骤。
- CSV 缺少必要列：后端会返回结构化校验错误。
- 前端无法连接后端：检查前端 API 地址与后端端口是否一致（默认 `5174`）。

