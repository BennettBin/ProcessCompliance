from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.process_compliance.config.loader import load_config
from backend.process_compliance.online.runner import OnlineMonitoringService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run online process compliance monitoring.")
    parser.add_argument("--event-log", required=True, help="Path to event log CSV.")
    parser.add_argument("--running-trace", required=True, help="Path to running trace CSV.")
    parser.add_argument("--dataset-name", default=None, help="Dataset name override.")
    parser.add_argument("--config", default=None, help="Path to YAML config file.")
    parser.add_argument(
        "--print-events",
        action="store_true",
        help="Print agent/pipeline events as they are emitted.",
    )
    return parser


async def _main() -> int:
    args = build_parser().parse_args()
    cfg = load_config(args.config)
    service = OnlineMonitoringService(cfg)

    async def emit_event(event):
        if args.print_events:
            print(f"EVENT {event.type} step={event.step_name} agent={event.agent_name}")

    result = await service.analyze(
        event_log_path=args.event_log,
        running_trace_path=args.running_trace,
        dataset_name=args.dataset_name,
        emit_event=emit_event,
    )

    print("\n=== Online Monitoring Summary ===")
    print(f"run_id: {result.run_id}")
    print(f"status: {result.status}")
    print(f"current_status: {result.compliance.current_status}")
    print(f"future_risk: {result.compliance.future_risk}")
    print(f"next_activity: {result.prediction.next_activity}")
    print(f"outcome: {result.prediction.outcome}")
    print(f"remaining_time: {result.prediction.remaining_time} {result.prediction.remaining_time_unit}")

    report_path = Path(cfg.paths.run_dir) / result.run_id / "final_report.json"
    print(f"final_report: {report_path}")
    return 0 if result.status != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))

