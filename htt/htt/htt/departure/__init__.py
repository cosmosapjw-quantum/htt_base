"""HTT pre-inference departure and response-rank diagnostics."""
from __future__ import annotations

from .response_overlap import (
    ResponseOverlapAudit,
    build_response_overlap_audit,
    require_rank_audit_for_model_run,
)

_LOCAL_GLOBAL_EXPORTS = {
    "LocalGlobalMixtureBlock",
    "LocalGlobalMixtureReport",
    "LocalGlobalMixtureSpec",
    "build_local_global_mixture_report",
}


def __getattr__(name: str):
    if name in _LOCAL_GLOBAL_EXPORTS:
        from . import local_global_mixture

        return getattr(local_global_mixture, name)
    raise AttributeError(name)

__all__ = [
    "LocalGlobalMixtureBlock",
    "LocalGlobalMixtureReport",
    "LocalGlobalMixtureSpec",
    "ResponseOverlapAudit",
    "build_response_overlap_audit",
    "build_local_global_mixture_report",
    "require_rank_audit_for_model_run",
]
