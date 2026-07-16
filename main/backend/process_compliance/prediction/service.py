from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from backend.process_compliance.config.settings import AppConfig
from backend.process_compliance.online.result_schema import PredictionResult, parse_prediction_text
from backend.process_compliance.prediction.next_activity import nap_predict
from backend.process_compliance.prediction.outcome import po_predict
from backend.process_compliance.prediction.remaining_time import t_predict


def _to_trace_records(running_trace: Any) -> List[Dict[str, Any]]:
    if isinstance(running_trace, pd.DataFrame):
        return running_trace.to_dict(orient="records")
    if isinstance(running_trace, list):
        return running_trace
    raise TypeError("running_trace must be a pandas.DataFrame or List[dict].")


def _safe_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except Exception:
        return None


def _normalize_pred_tuple(result: Any) -> Tuple[Optional[str], Optional[float]]:
    def _norm_label(v: Any) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip()
        if s.lower() in {"", "none", "null", "unknown"}:
            return None
        return s

    # Expected old format: (label, confidence)
    if isinstance(result, (list, tuple)) and len(result) >= 2:
        return _norm_label(result[0]), _safe_float(result[1])
    # Fallback: label only
    if result is None:
        return None, None
    return _norm_label(result), None


class PredictionService:
    def __init__(self, config: AppConfig):
        self.config = config

    def predict(self, running_trace: pd.DataFrame) -> PredictionResult:
        records = _to_trace_records(running_trace)
        out = PredictionResult(
            remaining_time_unit="hours",
        )

        # 1) Preferred path: package-native predictors.
        nap_fn = nap_predict
        po_fn = po_predict
        t_fn = t_predict

        if nap_fn is not None:
            try:
                nap_pred, nap_conf = _normalize_pred_tuple(nap_fn(running_trace=records, config=self.config))
                out.next_activity = nap_pred
                out.next_activity_confidence = nap_conf
            except Exception as e:
                out.debug_raw_text = (out.debug_raw_text or "") + f"[nap_predict error] {e}\n"

        if po_fn is not None:
            try:
                po_pred, po_conf = _normalize_pred_tuple(po_fn(running_trace=records, config=self.config))
                out.outcome = po_pred
                out.outcome_confidence = po_conf
            except Exception as e:
                out.debug_raw_text = (out.debug_raw_text or "") + f"[po_predict error] {e}\n"

        if t_fn is not None:
            try:
                out.remaining_time = _safe_float(t_fn(running_trace=records, config=self.config))
            except Exception as e:
                out.debug_raw_text = (out.debug_raw_text or "") + f"[t_predict error] {e}\n"

        # 2) Fallback path: parse a synthesized legacy-like text for compatibility.
        need_fallback = (
            out.next_activity is None
            and out.outcome is None
            and out.remaining_time is None
        )
        if need_fallback:
            try:
                raw_text = (
                    "The predicted next activity to be executed is None and the confidence level of the predicted value None. "
                    "The predicted outcome of the current trace execution process is None and the confidence level of the "
                    "predicted value is None. The predicted remaining execution time of the current trace process is None hours."
                )
                parsed = parse_prediction_text(raw_text, remaining_time_unit=out.remaining_time_unit)
                out = parsed
                out.debug_raw_text = raw_text
            except Exception as e:
                out.debug_raw_text = (out.debug_raw_text or "") + f"[fallback parse error] {e}\n"

        return out

