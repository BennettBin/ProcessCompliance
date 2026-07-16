from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from backend.process_compliance.config.settings import AppConfig
from backend.process_compliance.prediction.legacy_runtime import predict_next_activity


def nap_predict(
    running_trace: List[Dict[str, Any]],
    config: AppConfig,
) -> Tuple[Optional[str], Optional[float]]:
    return predict_next_activity(running_trace, config)
