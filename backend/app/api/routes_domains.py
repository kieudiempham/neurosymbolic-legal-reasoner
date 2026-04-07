"""Domain registry, summary, and multi-domain endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter

from app.config import settings
from app.path_setup import ensure_src_paths

ensure_src_paths()

from rulebase.domain_artifacts_loader import DomainArtifactsLoader, SharedLayerArtifacts

router = APIRouter(tags=["domains"])
logger = logging.getLogger(__name__)


@router.get("/domains")
def list_domains() -> dict[str, Any]:
    """List all available domains and their artifact status."""
    loader = DomainArtifactsLoader(settings.repo_root)
    available_domains = loader.discover_domains()
    
    return {
        "available_domains": available_domains,
        "domain_count": len(available_domains),
        "metadata": loader.get_all_domains_metadata(),
    }


@router.get("/domain/{domain}/summary")
def domain_summary(domain: str) -> dict[str, Any]:
    """Get summary of artifacts for a specific domain."""
    loader = DomainArtifactsLoader(settings.repo_root)
    artifacts = loader.get_domain_artifacts(domain)
    
    if artifacts is None:
        return {
            "domain": domain,
            "status": "not_found",
            "message": f"Domain '{domain}' not configured or artifacts missing",
        }
    
    return artifacts.load_metadata()


@router.get("/shared")
def shared_layer_info() -> dict[str, Any]:
    """Get shared semantic motif layer status."""
    loader = SharedLayerArtifacts(settings.repo_root)
    
    return {
        "layer": "shared",
        **loader.get_metadata(),
    }


@router.get("/status")
def backend_status() -> dict[str, Any]:
    """Complete backend status: domains + shared layer + config."""
    domain_loader = DomainArtifactsLoader(settings.repo_root)
    shared_loader = SharedLayerArtifacts(settings.repo_root)
    
    domains_metadata = domain_loader.get_all_domains_metadata()
    
    return {
        "backend": "multi-domain",
        "domains": {
            "available": list(domains_metadata.keys()),
            "count": len(domains_metadata),
            "metadata": domains_metadata,
        },
        "shared_layer": shared_loader.get_metadata(),
        "config": {
            "repo_root": str(settings.repo_root),
            "nly_enabled": settings.nli_enabled,
            "nesy_nli_mock": settings.nesy_nli_mock,
            "debug": settings.debug,
        },
    }
