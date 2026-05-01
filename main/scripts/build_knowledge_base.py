from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.process_compliance.config.loader import load_config
from backend.process_compliance.feature_learning.pipeline import main as build_main


def parse_args():
    p = argparse.ArgumentParser(description="Build compliance knowledge base.")
    p.add_argument("--dataset-name", default=None)
    p.add_argument("--knowledge-base-dir", default=None)
    p.add_argument("--config", default=None)
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    cfg = load_config(args.config)
    build_main(
        data_name=args.dataset_name or cfg.dataset.name,
        knowledge_base_dir=args.knowledge_base_dir or cfg.paths.knowledge_base_dir,
    )

