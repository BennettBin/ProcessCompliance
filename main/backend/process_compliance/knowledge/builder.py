from __future__ import annotations

from pathlib import Path
from typing import Optional

from backend.process_compliance.config.settings import AppConfig
from backend.process_compliance.knowledge.vectorstore import resolve_paths
from backend.process_compliance.utils import mkdir, split_document


class KnowledgeBuilder:
    def __init__(self, config: AppConfig):
        self.config = config

    def build(self, dataset_name: Optional[str] = None) -> None:
        paths = resolve_paths(self.config, dataset_name=dataset_name)
        Path(paths.knowledge_base_dir).mkdir(parents=True, exist_ok=True)

        if not Path(paths.rules_txt_path).exists():
            raise FileNotFoundError(
                f"Rules text file not found: {paths.rules_txt_path}. "
                "Please run feature learning first."
            )
        if not Path(paths.log_info_txt_path).exists():
            raise FileNotFoundError(
                f"Log info text file not found: {paths.log_info_txt_path}. "
                "Please run feature learning first."
            )

        try:
            from langchain_ollama import OllamaEmbeddings
            from langchain_community.vectorstores import FAISS
        except Exception as e:
            raise RuntimeError(f"Knowledge builder dependencies are missing: {e}")

        embedding_tool = OllamaEmbeddings(
            model=self.config.ollama.embedding_model,
            base_url=self.config.ollama.base_url,
        )

        mkdir(paths.rule_vectorstore_dir)
        mkdir(paths.log_info_vectorstore_dir)

        rule_vectorstore = FAISS.from_documents(
            split_document(paths.rules_txt_path),
            embedding_tool,
            normalize_L2=True,
        )
        rule_vectorstore.save_local(paths.rule_vectorstore_dir)

        log_info_vectorstore = FAISS.from_documents(
            split_document(paths.log_info_txt_path),
            embedding_tool,
            normalize_L2=True,
        )
        log_info_vectorstore.save_local(paths.log_info_vectorstore_dir)

