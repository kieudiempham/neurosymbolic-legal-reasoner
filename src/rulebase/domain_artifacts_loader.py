"""Unified loader for multi-domain artifacts (reasoning core, canonical, procedure, statute packs)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger_module_name = __name__


@dataclass
class DomainArtifacts:
    """Collected artifacts for a single domain."""
    domain: str
    runtime_core_path: Path
    canonical_path: Path | None = None
    procedure_traceability_path: Path | None = None
    statute_packs_dir: Path | None = None
    
    # Loaded metadata
    runtime_rule_count: int = 0
    canonical_rule_count: int = 0
    procedure_traceability_count: int = 0
    statute_pack_count: int = 0
    
    @property
    def is_complete(self) -> bool:
        """Check if domain has minimum required artifacts."""
        return self.runtime_core_path.exists()
    
    def load_metadata(self) -> dict[str, Any]:
        """Load rule counts from files without full parse."""
        metadata = {
            "domain": self.domain,
            "runtime_core_path": str(self.runtime_core_path),
            "runtime_rule_count": 0,
            "canonical_rule_count": 0,
            "procedure_traceability_count": 0,
            "statute_pack_count": 0,
            "status": "missing" if not self.is_complete else "loaded",
        }
        
        # Count runtime rules
        if self.runtime_core_path.exists():
            try:
                with open(self.runtime_core_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    rules = data.get('rules', [])
                    metadata["runtime_rule_count"] = len(rules)
            except Exception:
                pass
        
        # Count canonical rules
        if self.canonical_path and self.canonical_path.exists():
            try:
                with open(self.canonical_path, 'r', encoding='utf-8') as f:
                    count = sum(1 for line in f if line.strip())
                    metadata["canonical_rule_count"] = count
            except Exception:
                pass
        
        # Count procedure traceability
        if self.procedure_traceability_path and self.procedure_traceability_path.exists():
            try:
                with open(self.procedure_traceability_path, 'r', encoding='utf-8') as f:
                    count = sum(1 for line in f if line.strip())
                    metadata["procedure_traceability_count"] = count
            except Exception:
                pass
        
        # Count statute packs
        if self.statute_packs_dir and self.statute_packs_dir.exists():
            try:
                statute_files = list(self.statute_packs_dir.glob("*.jsonl"))
                metadata["statute_pack_count"] = len(statute_files)
            except Exception:
                pass
        
        return metadata


class DomainArtifactsLoader:
    """Load and manage artifacts for enterprise, tax, labor domains."""
    
    def __init__(self, repo_root: Path | str):
        self.repo_root = Path(repo_root)
        self._artifacts: dict[str, DomainArtifacts] = {}
    
    def discover_domains(self) -> list[str]:
        """Discover available domains from standard paths."""
        domains = []
        for domain in ["enterprise", "tax", "labor"]:
            artifacts = self._build_artifacts_for_domain(domain)
            if artifacts.is_complete:
                domains.append(domain)
                self._artifacts[domain] = artifacts
        return domains
    
    def get_domain_artifacts(self, domain: str) -> DomainArtifacts | None:
        """Get artifacts for a specific domain."""
        if domain not in self._artifacts:
            artifacts = self._build_artifacts_for_domain(domain)
            if artifacts.is_complete:
                self._artifacts[domain] = artifacts
                return artifacts
            return None
        return self._artifacts[domain]
    
    def get_all_domains_metadata(self) -> dict[str, dict[str, Any]]:
        """Get metadata summary for all available domains."""
        self.discover_domains()
        return {
            domain: artifacts.load_metadata()
            for domain, artifacts in self._artifacts.items()
        }
    
    def _build_artifacts_for_domain(self, domain: str) -> DomainArtifacts:
        """Build artifact paths for a domain."""
        domain_root = self.repo_root / "data" / "processed" / "rulebase" / domain
        
        runtime_core = domain_root / "runtime" / "rulebase_reasoning_core.json"
        canonical = domain_root / "canonical" / f"{domain}_core.jsonl"
        procedure_traceability = domain_root / "runtime" / "procedure_step_traceability.jsonl"
        statute_packs = domain_root / "statute_packs"
        
        return DomainArtifacts(
            domain=domain,
            runtime_core_path=runtime_core,
            canonical_path=canonical if canonical.exists() else None,
            procedure_traceability_path=procedure_traceability if procedure_traceability.exists() else None,
            statute_packs_dir=statute_packs if statute_packs.exists() else None,
        )


class SharedLayerArtifacts:
    """Shared semantic motif layer artifacts."""
    
    def __init__(self, repo_root: Path | str):
        self.repo_root = Path(repo_root)
        # Try v2.5 first, fall back to v2
        self.v2_5_path = self.repo_root / "data" / "processed" / "shared_rule_pack_v2_5_refined.jsonl"
        self.v2_path = self.repo_root / "data" / "processed" / "shared_rule_pack_v2_semantic_motifs.jsonl"
        self.active_path = self.v2_5_path if self.v2_5_path.exists() else self.v2_path
    
    @property
    def exists(self) -> bool:
        """Check if shared layer exists."""
        return self.active_path.exists()
    
    @property
    def motif_count(self) -> int:
        """Count motifs in shared layer."""
        if not self.exists:
            return 0
        try:
            with open(self.active_path, 'r', encoding='utf-8') as f:
                return sum(1 for line in f if line.strip())
        except Exception:
            return 0
    
    def get_metadata(self) -> dict[str, Any]:
        """Get shared layer metadata."""
        return {
            "layer": "shared",
            "path": str(self.active_path),
            "version": "v2.5" if self.v2_5_path.exists() else "v2",
            "motif_count": self.motif_count,
            "status": "loaded" if self.exists else "missing",
        }
