"""Load and manage domain-specific configurations for pipeline.

Purpose: Externalize enterprise-specific patterns from code into config.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from utils.io import read_yaml
from utils.logger import get_logger

logger = get_logger(__name__)


class DomainConfig:
    """Loaded domain configuration."""
    
    def __init__(self, config_dict: dict[str, Any]) -> None:
        self._config = config_dict
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by dot notation (e.g., 'doc_metadata.defaults')."""
        keys = key.split(".")
        val = self._config
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default
        return val if val is not None else default
    
    def get_dict(self, key: str, default: dict[str, Any] | None = None) -> dict[str, Any]:
        """Get config dictionary."""
        return self.get(key, default or {})
    
    def get_list(self, key: str, default: list[Any] | None = None) -> list[Any]:
        """Get config list."""
        return self.get(key, default or [])
    
    def __getitem__(self, key: str) -> Any:
        """Direct access to config dict."""
        return self._config[key]


class DomainConfigLoader:
    """Load domain configurations from YAML files."""
    
    def __init__(self, domains_dir: Path | None = None) -> None:
        """Initialize loader.
        
        Args:
            domains_dir: Path to domains config directory. 
                        If None, defaults to {repo_root}/configs/domains
        """
        if domains_dir is None:
            from pipelines._paths import legal_qa_nesy_root
            domains_dir = legal_qa_nesy_root() / "configs" / "domains"
        
        self._domains_dir = domains_dir
        self._cache: dict[str, DomainConfig] = {}
    
    def load(self, domain: str) -> DomainConfig:
        """Load domain config from YAML file.
        
        Args:
            domain: Domain name (e.g., 'enterprise', 'labor', 'tax')
        
        Returns:
            DomainConfig object
            
        Raises:
            FileNotFoundError: If domain config file doesn't exist
            ValueError: If config file is invalid
        """
        if domain in self._cache:
            return self._cache[domain]
        
        config_path = self._domains_dir / f"{domain}.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"Domain config not found: {config_path}\n"
                f"Available domains should be in {self._domains_dir}"
            )
        
        try:
            config_dict = read_yaml(config_path)
        except Exception as e:
            raise ValueError(f"Failed to load domain config from {config_path}: {e}")
        
        domain_config = DomainConfig(config_dict)
        self._cache[domain] = domain_config
        logger.info(f"Loaded domain config: {domain}")
        
        return domain_config
    
    def available_domains(self) -> list[str]:
        """List available domain configs (by filename)."""
        if not self._domains_dir.exists():
            logger.warning(f"Domains directory does not exist: {self._domains_dir}")
            return []
        
        return [
            p.stem
            for p in self._domains_dir.glob("*.yaml")
            if p.is_file() and not p.name.startswith("_")
        ]


# Global loader instance
_loader: DomainConfigLoader | None = None


def get_domain_loader() -> DomainConfigLoader:
    """Get or create global domain config loader (singleton)."""
    global _loader
    if _loader is None:
        _loader = DomainConfigLoader()
    return _loader


def load_domain_config(domain: str) -> DomainConfig:
    """Load domain config by name (convenience function)."""
    return get_domain_loader().load(domain)


def list_available_domains() -> list[str]:
    """List all available domains (convenience function)."""
    return get_domain_loader().available_domains()
