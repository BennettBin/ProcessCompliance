import asyncio

from backend.process_compliance.config.loader import load_config
from backend.process_compliance.online.runner import OnlineMonitoringService


def test_online_monitoring_service_controlled_error_on_missing_files():
    async def _run():
        cfg = load_config()
        svc = OnlineMonitoringService(cfg)
        result = await svc.analyze(
            event_log_path="dataset/new_data/not_exists.csv",
            running_trace_path="dataset/running_trace/not_exists.csv",
            dataset_name=cfg.dataset.name,
        )
        return result

    result = asyncio.run(_run())
    assert result.status == "failed"
    assert result.message


