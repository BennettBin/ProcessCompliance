from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

import pandas as pd
from pydantic import BaseModel, Field

from backend.process_compliance.config.loader import load_config
from backend.process_compliance.utils import mkdir, trans_case_to_text

APP_CONFIG = load_config()


def mine_declare_rules_from_xes(
    xes_path: str,
    case_id_key: str = "case:concept:name",
    min_support: float = 0.3,
    item_sets_support: float = 0.6,
    max_declare_cardinality: int = 2,
    consider_vacuity: bool = False,
    top_k: Optional[int] = None,
) -> List[str]:
    """Compatibility miner; returns discovered rules when Declare4Py is available."""
    try:
        from Declare4Py.D4PyEventLog import D4PyEventLog
        from Declare4Py.ProcessMiningTasks.Discovery.DeclareMiner import DeclareMiner
    except Exception:
        return []

    event_log = D4PyEventLog(case_name=case_id_key)
    event_log.parse_xes_log(xes_path)
    miner = DeclareMiner(
        log=event_log,
        consider_vacuity=consider_vacuity,
        min_support=min_support,
        itemsets_support=item_sets_support,
        max_declare_cardinality=max_declare_cardinality,
    )
    discovered_model = miner.run()
    rules = list(discovered_model.serialized_constraints)
    return rules[:top_k] if top_k is not None else rules


class EventLog:
    def __init__(self, log_add: str, activity_att: str = "concept:name"):
        self.log_add = log_add
        self.activity_att = activity_att
        self.log_df = pd.read_csv(log_add, encoding="utf-8-sig")

    def get_running_trace_feature(self) -> str:
        rows = self.log_df.to_dict(orient="records")
        return trans_case_to_text(rows) if rows else ""

    def get_case_feature(self) -> str:
        if "case" not in self.log_df.columns:
            return "case feature unavailable: missing 'case' column."
        case_lengths = self.log_df.groupby("case").size()
        if case_lengths.empty:
            return "case feature unavailable: no case data."
        return (
            f"case length min={int(case_lengths.min())}, "
            f"max={int(case_lengths.max())}, mean={float(case_lengths.mean()):.2f}"
        )

    def get_event_feature(self) -> str:
        if self.activity_att not in self.log_df.columns:
            return f"event feature unavailable: missing '{self.activity_att}' column."
        counts = self.log_df[self.activity_att].value_counts()
        head = ", ".join([f"{k}:{int(v)}" for k, v in counts.head(10).items()])
        return f"activity frequency(top): {head}"


def learn_log_features(log_add: str, out_txt_path: str, activity_attribute: str = "concept:name"):
    log = EventLog(log_add, activity_attribute)
    dfg_features = "dfg feature extraction is not enabled in compatibility mode."
    case_features = log.get_case_feature()
    event_features = log.get_event_feature()
    with open(out_txt_path, "w", encoding="utf-8") as f:
        f.write(dfg_features + "\n\n")
        f.write(case_features + "\n\n")
        f.write(event_features + "\n")
    return dfg_features, case_features, event_features


def learn_running_trace_features(running_trace_add: str, activity_attribute: str = "concept:name"):
    return EventLog(running_trace_add, activity_attribute).get_running_trace_feature()


class RuleDebateSession:
    def ask(self, question: str) -> str:
        # Compatibility behavior: passthrough.
        return question


class SecondCheckPrompt(BaseModel):
    conflict: bool = Field(title="conflict", description="Whether a conflict exists.", examples=[True, False])
    comment: str = Field(title="comment", description="Conflict analysis details.")


class SecondCheckAgent:
    def __init__(
        self,
        nl_rule: str,
        all_nl_rules: List[str],
        second_check_log_path: str = "second_check_log.json",
        user_id: str = "user_001",
    ):
        self.nl_rule = nl_rule
        self.all_nl_rules = all_nl_rules
        self.second_check_log_path = second_check_log_path
        self.user_id = user_id

    def ask(self):
        nl_rule = (self.nl_rule or "").strip()
        if nl_rule and nl_rule not in self.all_nl_rules:
            self.all_nl_rules.append(nl_rule)
        return False, self.all_nl_rules


def translate(declare_rule: str) -> str:
    return RuleDebateSession().ask(declare_rule).strip()


def main(
    data_name: Optional[str] = None,
    knowledge_base_dir: Optional[str] = None,
):
    data_name = data_name or APP_CONFIG.dataset.name
    knowledge_base_dir = knowledge_base_dir or APP_CONFIG.paths.knowledge_base_dir

    xes_log_file = APP_CONFIG.dataset.raw_xes_path
    csv_log_file = APP_CONFIG.dataset.event_log_path
    running_trace_file = APP_CONFIG.dataset.running_trace_path

    if not Path(xes_log_file).exists():
        xes_log_file = f"./data/{data_name}.xes"
    if not Path(csv_log_file).exists():
        csv_log_file = f"./data/{data_name}.csv"
    if not Path(running_trace_file).exists():
        running_trace_file = f"./data/running_trace/{data_name}_trace.csv"

    mkdir(knowledge_base_dir)
    out_rule_json_path = f"{knowledge_base_dir}/declare_rules_{data_name}.json"
    out_rule_txt_path = f"{knowledge_base_dir}/declare_rules_{data_name}.txt"
    out_log_info_txt_path = f"{knowledge_base_dir}/log_info_{data_name}.txt"

    declares = mine_declare_rules_from_xes(xes_log_file, top_k=50)
    with open(out_rule_json_path, "w", encoding="utf-8") as f:
        json.dump({"rules": declares}, f, ensure_ascii=False, indent=2)
    with open(out_rule_txt_path, "w", encoding="utf-8") as f:
        for d in declares:
            f.write(translate(d) + "\n")

    log_feature = learn_log_features(csv_log_file, out_txt_path=out_log_info_txt_path)
    running_trace_feature = learn_running_trace_features(running_trace_file, activity_attribute="concept:name")
    return log_feature, running_trace_feature


if __name__ == "__main__":
    _ = main()
