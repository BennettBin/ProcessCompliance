from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from backend.process_compliance.config.settings import AppConfig


@dataclass
class ModelPrepareResult:
    ready: bool
    trained: bool
    model_dir: str
    missing_files: List[str]
    warnings: List[str]


class ModelService:
    def __init__(self, config: AppConfig):
        self.config = config

    @staticmethod
    def _expected_model_files(dataset_name: str) -> List[str]:
        return [
            f"{dataset_name}_NAP.pth",
            f"{dataset_name}_PO.pth",
            f"{dataset_name}_T.pth",
        ]

    def _resolve_model_dir(self) -> Path:
        return Path(self.config.paths.model_dir)

    def _resolve_base_dir(self) -> Path:
        model_dir = self._resolve_model_dir().resolve()
        return model_dir.parent

    def _missing_files(self, dataset_name: str) -> Tuple[Path, List[str]]:
        model_dir = self._resolve_model_dir()
        expected = self._expected_model_files(dataset_name)
        missing = [name for name in expected if not (model_dir / name).exists()]
        return model_dir, missing

    def ensure_models_ready(self, dataset_name: str) -> ModelPrepareResult:
        warnings: List[str] = []
        model_dir, missing = self._missing_files(dataset_name)
        model_dir.mkdir(parents=True, exist_ok=True)
        if not missing:
            return ModelPrepareResult(
                ready=True,
                trained=False,
                model_dir=str(model_dir),
                missing_files=[],
                warnings=[],
            )

        trained = False
        try:
            from backend.process_compliance.models import trainer as legacy_trainer
        except Exception as e:
            warnings.append(f"Model trainer import failed: {e}")
            return ModelPrepareResult(
                ready=False,
                trained=False,
                model_dir=str(model_dir),
                missing_files=missing,
                warnings=warnings,
            )

        if dataset_name != "BPIC20_D":
            warnings.append(
                f"Legacy trainer is hardcoded for BPIC20_D; got dataset={dataset_name}. "
                "Skipping auto training."
            )
            return ModelPrepareResult(
                ready=False,
                trained=False,
                model_dir=str(model_dir),
                missing_files=missing,
                warnings=warnings,
            )

        try:
            legacy_trainer.DATASET = dataset_name
            legacy_trainer.configure_paths(
                dataset_name=dataset_name,
                dataset_csv=self.config.dataset.event_log_path,
                model_dir=self.config.paths.model_dir,
                pro_data_dir=self.config.paths.processed_feature_dir,
                base_dir=self._resolve_base_dir(),
            )
            for mode in ("NAP", "PO", "T"):
                legacy_trainer.PREDICTION_MODE = mode
                legacy_trainer.data_pro()
                legacy_trainer.main()
            trained = True
        except Exception as e:
            warnings.append(f"Model training failed: {e}")

        _, missing_after = self._missing_files(dataset_name)
        return ModelPrepareResult(
            ready=len(missing_after) == 0,
            trained=trained,
            model_dir=str(model_dir),
            missing_files=missing_after,
            warnings=warnings,
        )
