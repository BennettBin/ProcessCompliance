from .trainer import DATASET, PREDICTION_MODE


def get_default_registry():
    return {
        "dataset": DATASET,
        "prediction_mode": PREDICTION_MODE,
        "modes": {"next_activity": "NAP", "outcome": "PO", "remaining_time": "T"},
    }


__all__ = ["get_default_registry"]
