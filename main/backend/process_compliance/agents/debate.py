from __future__ import annotations

import re
from typing import Optional, Tuple

CONSENSUS_RE = re.compile(r"CONSENSUS:\s*(YES|NO)\b", re.IGNORECASE)
CONF_RE = re.compile(r"CONFIDENCE:\s*([01](?:\.\d+)?)", re.IGNORECASE)


def parse_consensus_confidence(raw_text: str) -> Tuple[str, Optional[float]]:
    m = CONSENSUS_RE.search(raw_text or "")
    c = CONF_RE.search(raw_text or "")
    confidence = float(c.group(1)) if c else None
    if not m:
        return "unknown", confidence
    yes_no = m.group(1).upper()
    return ("yes" if yes_no == "YES" else "no"), confidence
