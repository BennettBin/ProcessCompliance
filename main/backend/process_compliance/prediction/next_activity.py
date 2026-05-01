from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def nap_predict(running_trace: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[float]]:
    """
    Package-native next-activity predictor entry.
    Current MVP returns unknown when no packaged model runtime is available.
    """
    # Future: wire packaged model registry here.
    return None, None
