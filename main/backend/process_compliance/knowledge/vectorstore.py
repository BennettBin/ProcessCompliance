from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from backend.process_compliance.config.settings import AppConfig
from backend.process_compliance.config.loader import load_config


@dataclass
class VectorstorePaths:
    dataset_name: str
    knowledge_base_dir: str

    @property
    def rules_txt_path(self) -> str:
        return str(Path(self.knowledge_base_dir) / f"declare_rules_{self.dataset_name}.txt")

    @property
    def log_info_txt_path(self) -> str:
        return str(Path(self.knowledge_base_dir) / f"log_info_{self.dataset_name}.txt")

    @property
    def rule_vectorstore_dir(self) -> str:
        return str(Path(self.knowledge_base_dir) / f"rule_vectorstore_{self.dataset_name}")

    @property
    def log_info_vectorstore_dir(self) -> str:
        return str(Path(self.knowledge_base_dir) / f"log_info_vectorstore_{self.dataset_name}")


def resolve_paths(config: AppConfig, dataset_name: Optional[str] = None) -> VectorstorePaths:
    ds = dataset_name or config.dataset.name
    return VectorstorePaths(
        dataset_name=ds,
        knowledge_base_dir=config.paths.knowledge_base_dir,
    )


class VectorstoreBuild:
    """
    Backward-compatible adapter for legacy VectorstoreBuild usage.
    """

    def __init__(self, config: Optional[AppConfig] = None, dataset_name: Optional[str] = None):
        self.config = config or load_config()
        self.paths = resolve_paths(self.config, dataset_name=dataset_name)
        self.rules_txt_path = self.paths.rules_txt_path
        self.log_info_path = self.paths.log_info_txt_path
        self.rule_vectorstore_dir = self.paths.rule_vectorstore_dir
        self.log_info_vectorstore_dir = self.paths.log_info_vectorstore_dir

    def build_vectorstores(self) -> None:
        from backend.process_compliance.knowledge.builder import KnowledgeBuilder
        KnowledgeBuilder(self.config).build(dataset_name=self.paths.dataset_name)

    def get_vectorstores(self, target_dir: str):
        from backend.process_compliance.knowledge.service import KnowledgeService
        return KnowledgeService(self.config)._load_vectorstore(target_dir)  # noqa: SLF001

