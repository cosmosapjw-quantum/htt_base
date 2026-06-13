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
_POSTERIOR_PUSHFORWARD_EXPORTS = {
    "PiSource",
    "PosteriorPushforwardPrerequisites",
    "PosteriorPushforwardReport",
    "PosteriorPushforwardSample",
    "build_posterior_pushforward_report",
    "reject_mio_pushforward_inputs",
}


def __getattr__(name: str):
    if name in _LOCAL_GLOBAL_EXPORTS:
        from . import local_global_mixture

        return getattr(local_global_mixture, name)
    if name in _POSTERIOR_PUSHFORWARD_EXPORTS:
        from . import posterior_pushforward

        return getattr(posterior_pushforward, name)
    raise AttributeError(name)

__all__ = [
    "LocalGlobalMixtureBlock",
    "LocalGlobalMixtureReport",
    "LocalGlobalMixtureSpec",
    "PiSource",
    "PosteriorPushforwardPrerequisites",
    "PosteriorPushforwardReport",
    "PosteriorPushforwardSample",
    "ResponseOverlapAudit",
    "build_response_overlap_audit",
    "build_local_global_mixture_report",
    "build_posterior_pushforward_report",
    "reject_mio_pushforward_inputs",
    "require_rank_audit_for_model_run",
]
