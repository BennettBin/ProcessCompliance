from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.process_compliance.config.settings import AppConfig
from backend.process_compliance.prediction.legacy_runtime import predict_remaining_time

def t_predict(
    running_trace: List[Dict[str, Any]],
    config: AppConfig,
) -> Optional[float]:
    return predict_remaining_time(running_trace, config)
