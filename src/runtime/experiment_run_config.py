"""Config-driven runtime profiles for reproducible QA experiments."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from pydantic import BaseModel

from runtime.cross_domain_policy import CrossDomainPolicy
from schemas.domain_routing import DomainRoutingPlan
from utils.io import read_yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRESET_DIR = _REPO_ROOT / "configs" / "experiments" / "run_profiles"


class ExperimentRunConfig(BaseModel):
    profile_name: str = "custom"
    enable_shared_layer: bool = True
    enable_clarification: bool = True
    enable_repair_loop: bool = True
    enable_backward_chaining: bool = True
    enable_nli_verifier: bool = True
    enable_cross_domain_jump: bool = True
    config_source: str | None = None

    def to_trace_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    def apply_repair_limits(
        self,
        *,
        parse: int,
        answer: int,
        rule: int,
        backward: int,
        forward: int,
    ) -> tuple[int, int, int, int, int]:
        if self.enable_repair_loop:
            return parse, answer, rule, backward, forward
        return 0, 0, 0, 0, 0

    def apply_routing_plan(self, routing: DomainRoutingPlan) -> DomainRoutingPlan:
        return routing.model_copy(
            update={
                "include_shared": self.enable_shared_layer,
                "allow_cross_domain_expansion": self.enable_cross_domain_jump,
            }
        )

    def apply_cross_domain_policy(self, policy: CrossDomainPolicy) -> CrossDomainPolicy:
        return CrossDomainPolicy(
            allow_shared_to_domain=self.enable_shared_layer and policy.allow_shared_to_domain,
            allow_primary_to_secondary=self.enable_cross_domain_jump and policy.allow_primary_to_secondary,
            require_bridge_for_secondary_jump=policy.require_bridge_for_secondary_jump,
            max_cross_domain_hops=policy.max_cross_domain_hops if self.enable_cross_domain_jump else 0,
        )


def _load_config_dict_from_path(path: Path) -> dict[str, Any]:
    payload = read_yaml(path)
    if not isinstance(payload, dict):
        raise ValueError(f"run config at {path} must be a mapping")
    return payload


def _preset_path_for_name(name: str, *, preset_dir: Path) -> Path:
    normalized = str(name or "").strip()
    if not normalized:
        raise ValueError("run config preset name must not be empty")
    return preset_dir / f"{normalized.lower()}.yaml"


def _config_from_mapping(mapping: Mapping[str, Any], *, config_source: str | None = None) -> ExperimentRunConfig:
    payload = dict(mapping)
    if config_source and not payload.get("config_source"):
        payload["config_source"] = config_source
    if not payload.get("profile_name"):
        payload["profile_name"] = "custom"
    return ExperimentRunConfig.model_validate(payload)


def load_experiment_run_config(path: str | Path) -> ExperimentRunConfig:
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = (_REPO_ROOT / file_path).resolve()
    payload = _load_config_dict_from_path(file_path)
    if not payload.get("profile_name"):
        payload["profile_name"] = file_path.stem
    return _config_from_mapping(payload, config_source=str(file_path))


def resolve_experiment_run_config(
    run_config: ExperimentRunConfig | Mapping[str, Any] | str | Path | None,
    *,
    preset_dir: Path | None = None,
) -> ExperimentRunConfig:
    directory = preset_dir or DEFAULT_PRESET_DIR
    if run_config is None:
        return ExperimentRunConfig()
    if isinstance(run_config, ExperimentRunConfig):
        return run_config
    if isinstance(run_config, Mapping):
        return _config_from_mapping(run_config)
    if isinstance(run_config, Path):
        return load_experiment_run_config(run_config)
    text = str(run_config).strip()
    if not text:
        return ExperimentRunConfig()
    candidate = Path(text)
    if candidate.suffix.lower() in {".yaml", ".yml"} or candidate.is_absolute() or "/" in text or "\\" in text:
        return load_experiment_run_config(candidate)
    preset_path = _preset_path_for_name(text, preset_dir=directory)
    return load_experiment_run_config(preset_path)