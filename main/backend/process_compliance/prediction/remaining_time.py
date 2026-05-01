from __future__ import annotations

from typing import Any, Dict, List, Optional


def t_predict(running_trace: List[Dict[str, Any]]) -> Optional[float]:
    """
    Package-native remaining-time predictor entry.
    Current MVP returns unknown when no packaged model runtime is available.
    """
    return None
