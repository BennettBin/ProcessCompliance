from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from backend.process_compliance.config.settings import AppConfig
from backend.process_compliance.knowledge.builder import KnowledgeBuilder
from backend.process_compliance.knowledge.retriever import retrieve_texts
from backend.process_compliance.knowledge.vectorstore import resolve_paths
from backend.process_compliance.online.result_schema import RuleEvidence


class KnowledgeService:
    def __init__(self, config: AppConfig):
        self.config = config
        self._builder = KnowledgeBuilder(config)
        self._last_warning: Optional[str] = None

    def _load_vectorstore(self, target_dir: str):
        try:
            from langchain_ollama import OllamaEmbeddings
            from langchain_community.vectorstores import FAISS
        except Exception as e:
            self._last_warning = f"Vectorstore dependencies are missing: {e}"
            return None

        if not Path(target_dir).exists():
            self._last_warning = f"Vectorstore directory does not exist: {target_dir}"
            return None

        embeddings = OllamaEmbeddings(
            model=self.config.ollama.embedding_model,
            base_url=self.config.ollama.base_url,
        )
        try:
            return FAISS.load_local(target_dir, embeddings, allow_dangerous_deserialization=True)
        except Exception as e:
            self._last_warning = f"Failed to load vectorstore at {target_dir}: {e}"
            return None

    def build_if_missing(self, dataset_name: str) -> None:
        paths = resolve_paths(self.config, dataset_name=dataset_name)
        rule_dir = Path(paths.rule_vectorstore_dir)
        log_dir = Path(paths.log_info_vectorstore_dir)
        if rule_dir.exists() and log_dir.exists():
            return
        try:
            self._builder.build(dataset_name=dataset_name)
        except Exception as e:
            # controlled warning; callers can continue with empty results
            self._last_warning = f"Knowledge build skipped: {e}"

    def search_rules(self, query: str, top_k: int = 5) -> List[RuleEvidence]:
        dataset_name = self.config.dataset.name
        self.build_if_missing(dataset_name)
        paths = resolve_paths(self.config, dataset_name=dataset_name)
        store = self._load_vectorstore(paths.rule_vectorstore_dir)
        if store is None:
            return []

        try:
            texts = retrieve_texts(store, f"Search for compliance rules related to {query}", top_k=top_k)
        except Exception as e:
            self._last_warning = f"Rule retrieval failed: {e}"
            return []

        out: List[RuleEvidence] = []
        for i, txt in enumerate(texts):
            out.append(
                RuleEvidence(
                    rule_id=f"rule_{i + 1}",
                    rule_text=txt,
                    matched=None,
                    confidence=None,
                    evidence_text=txt,
                    source="rule_vectorstore",
                )
            )
        return out

    def search_log_info(self, query: str, top_k: int = 5) -> List[str]:
        dataset_name = self.config.dataset.name
        self.build_if_missing(dataset_name)
        paths = resolve_paths(self.config, dataset_name=dataset_name)
        store = self._load_vectorstore(paths.log_info_vectorstore_dir)
        if store is None:
            return []
        try:
            return retrieve_texts(store, f"Search for historical event log information related to {query}", top_k=top_k)
        except Exception as e:
            self._last_warning = f"Log-info retrieval failed: {e}"
            return []


