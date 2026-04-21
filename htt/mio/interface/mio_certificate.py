"""mio.interface.mio_certificate — MioCertificate generator API.

INDEPENDENT_TRACKS_PLAN v1.2 §12.4 (MIO-HJ-06a, Week 6 Day 2).
Parent: BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md v3 §4.5.3.5.

Role: convenience builder for the `workspace.contracts.MioCertificate`
dataclass. Each HJ module passes its own computed fields here and
receives a fully-populated, immutable certificate. Provenance
(`git_commit`, `config_hash`) is auto-populated so call sites need
not wire them by hand.

G19 hard separation (v3 §4.5.4 / §10.2bis):
  * Any caller-supplied keyword whose name contains 'posterior' raises
    `ValueError` — MIO does not produce posteriors under any
    circumstance. See `test_build_rejects_posterior_keyword`.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from common.contracts import ArtifactManifest, TscAdequacyOverlay
from mio.interface.manifest import (
    MioReadiness,
    build_mio_manifest,
    merge_domain_caveats,
)
from tsc.adapters.mio_certificate import overlay_to_mio_fields
from workspace.contracts.mio_certificate import MioCertificate


def _resolve_git_commit() -> str:
    """Resolve the current HEAD sha. Returns 'unknown' outside a git tree."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parent,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


def _hash_config(*parts: Any) -> str:
    """Stable sha256 digest of a series of JSON-serializable payloads.

    Used to derive `config_hash` from the caller's diagnostic payload
    (departure variables + indicators + metrics) so that two certificates
    with identical content share a hash even across sessions.
    """
    payload = json.dumps(
        [parts],
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _reject_posterior_keywords(raw_kwargs: Dict[str, Any]) -> None:
    """G19 hard separation — any key containing 'posterior' is forbidden."""
    offenders = [k for k in raw_kwargs if "posterior" in k.lower()]
    if offenders:
        raise ValueError(
            "MIO cannot generate posteriors. Forbidden keyword(s): "
            f"{offenders}. See v3 §10.2bis G19 hard-separation rule."
        )


def _merge_tsc_overlay_fields(
    *,
    adequacy_indicators: Dict[str, bool],
    domain_caveats: Sequence[str],
    channel_caveats: Sequence[str] | None,
    tsc_overlay: TscAdequacyOverlay | None,
    tsc_overlay_ref: str | None,
) -> tuple[Dict[str, bool], List[str], List[str], str | None]:
    """Attach advisory TSC context without changing MIO ownership semantics."""
    resolved_adequacy = dict(adequacy_indicators)
    resolved_domain = list(domain_caveats)
    resolved_channel = list(channel_caveats) if channel_caveats is not None else []
    resolved_ref = tsc_overlay_ref

    if resolved_ref is not None:
        resolved_adequacy.setdefault("tsc_overlay_attached", True)

    if tsc_overlay is None:
        return resolved_adequacy, resolved_domain, resolved_channel, resolved_ref

    fields = overlay_to_mio_fields(tsc_overlay)
    if resolved_ref is None:
        resolved_ref = tsc_overlay.manifest.artifact_id

    resolved_adequacy["tsc_overlay_attached"] = True
    resolved_adequacy["tsc_overlay_diagnostic_only"] = bool(fields.diagnostic_only)

    resolved_domain.extend(fields.source_caveats)
    resolved_domain.append(f"tsc_domain_status={fields.tsc_domain_status}")
    resolved_domain.append(f"tsc_trace_source_adequacy={fields.trace_source_adequacy}")
    if fields.tsc_upgrade_hint is not None:
        resolved_domain.append(f"tsc_upgrade_hint={fields.tsc_upgrade_hint}")
    if fields.diagnostic_only:
        resolved_domain.append("tsc_overlay_diagnostic_only")
    for blocker in fields.publication_blockers:
        resolved_domain.append(f"tsc_publication_blocker={blocker}")

    for channel in fields.propagation_status_required:
        resolved_channel.append(f"tsc_propagation_pending:{channel}")
    for channel, claim_ceiling in sorted(fields.channel_claim_ceiling.items()):
        resolved_channel.append(f"tsc_claim_ceiling:{channel}={claim_ceiling}")
    for channel, responsibility in sorted(fields.channel_responsibility.items()):
        resolved_channel.append(
            f"tsc_channel_responsibility:{channel}={responsibility}"
        )

    return (
        resolved_adequacy,
        list(dict.fromkeys(resolved_domain)),
        list(dict.fromkeys(resolved_channel)),
        resolved_ref,
    )


def build_mio_certificate(
    report_type: str,
    probe_name: str,
    channel: str,
    departure_variables: Dict[str, float],
    adequacy_indicators: Dict[str, bool],
    consistency_metrics: Dict[str, float],
    *,
    domain_caveats: List[str],
    reduction_status: str,
    generated_by: str,
    input_data_hashes: List[str],
    channel_caveats: Optional[List[str]] = None,
    htt_cross_check_suggested: Optional[Dict[str, str]] = None,
    git_commit: Optional[str] = None,
    config_hash: Optional[str] = None,
    manifest: ArtifactManifest | None = None,
    tsc_overlay: TscAdequacyOverlay | None = None,
    tsc_overlay_ref: str | None = None,
    readiness: MioReadiness | None = None,
    artifact_id: str | None = None,
    artifact_path: str | None = None,
    code_version: str = "ver2-sk07m",
    schema_version: str = "ver2-v7",
    statistics_definitions: Optional[Dict[str, Any]] = None,
    **extra: Any,
) -> MioCertificate:
    """Build an immutable MioCertificate with auto-populated provenance.

    Parameters
    ----------
    report_type, probe_name, channel
        Identification triple (e.g. 'directional_coherence' / 'CMB' / 'dipole').
    departure_variables, adequacy_indicators, consistency_metrics
        Diagnostic dictionaries produced by the caller's HJ module.
    domain_caveats
        Human-readable caveats that scope the report (e.g. 'masked_sky_partial').
    reduction_status
        One of 'theory-direct' | 'theory-approximate' | 'diagnostic-only'.
    generated_by
        Module string, e.g. 'mio.coherence.directional v0.1'.
    input_data_hashes
        Input dataset digests. Empty list permitted for bootstrap tests.
    channel_caveats
        Optional additional channel-scoped caveats (defaults to []).
    htt_cross_check_suggested
        Optional HTT cross-check hint dict — NOT a posterior, just a pointer.
    git_commit, config_hash
        Optional overrides; otherwise auto-populated via git rev-parse +
        sha256 of the diagnostic payload.

    Raises
    ------
    ValueError
        If any `extra` keyword contains the substring 'posterior' — MIO
        does not produce posteriors (v3 §10.2bis G19).
    """
    _reject_posterior_keywords(extra)
    if extra:
        unknown = sorted(extra.keys())
        raise TypeError(
            f"build_mio_certificate() got unexpected keyword arguments: {unknown}"
        )
    if readiness is not None and manifest is not None:
        raise ValueError("pass either manifest or readiness, not both")

    resolved_commit = git_commit if git_commit is not None else _resolve_git_commit()
    resolved_hash = (
        config_hash
        if config_hash is not None
        else _hash_config(
            report_type,
            probe_name,
            channel,
            departure_variables,
            adequacy_indicators,
            consistency_metrics,
        )
    )
    resolved_manifest = manifest
    resolved_domain_caveats = list(domain_caveats)
    if readiness is not None:
        if not artifact_id or not artifact_path:
            raise ValueError(
                "artifact_id and artifact_path are required when readiness is provided"
            )
        resolved_manifest = build_mio_manifest(
            artifact_id=artifact_id,
            artifact_path=artifact_path,
            created_by=generated_by,
            git_commit=resolved_commit,
            config_hash=resolved_hash,
            input_hashes=input_data_hashes,
            readiness=readiness,
            code_version=code_version,
            schema_version=schema_version,
            statistics_definitions=statistics_definitions,
        )
        resolved_domain_caveats = merge_domain_caveats(domain_caveats, readiness)

    (
        resolved_adequacy_indicators,
        resolved_domain_caveats,
        resolved_channel_caveats,
        resolved_overlay_ref,
    ) = _merge_tsc_overlay_fields(
        adequacy_indicators=adequacy_indicators,
        domain_caveats=resolved_domain_caveats,
        channel_caveats=channel_caveats,
        tsc_overlay=tsc_overlay,
        tsc_overlay_ref=tsc_overlay_ref,
    )

    return MioCertificate(
        report_type=report_type,
        probe_name=probe_name,
        channel=channel,
        departure_variables=dict(departure_variables),
        adequacy_indicators=resolved_adequacy_indicators,
        consistency_metrics=dict(consistency_metrics),
        domain_caveats=resolved_domain_caveats,
        channel_caveats=resolved_channel_caveats,
        reduction_status=reduction_status,
        generated_by=generated_by,
        git_commit=resolved_commit,
        config_hash=resolved_hash,
        input_data_hashes=list(input_data_hashes),
        manifest=resolved_manifest,
        tsc_overlay_ref=resolved_overlay_ref,
        htt_cross_check_suggested=(
            dict(htt_cross_check_suggested) if htt_cross_check_suggested is not None else None
        ),
    )


def certificate_to_payload(cert: MioCertificate) -> Dict[str, Any]:
    """Return a stable JSON-ready payload for ``MioCertificate``."""
    return {
        "report_type": cert.report_type,
        "probe_name": cert.probe_name,
        "channel": cert.channel,
        "departure_variables": cert.departure_variables,
        "adequacy_indicators": cert.adequacy_indicators,
        "consistency_metrics": cert.consistency_metrics,
        "domain_caveats": cert.domain_caveats,
        "channel_caveats": cert.channel_caveats,
        "reduction_status": cert.reduction_status,
        "generated_by": cert.generated_by,
        "git_commit": cert.git_commit,
        "config_hash": cert.config_hash,
        "input_data_hashes": cert.input_data_hashes,
        "manifest": asdict(cert.manifest) if cert.manifest is not None else None,
        "tsc_overlay_ref": cert.tsc_overlay_ref,
        "htt_cross_check_suggested": cert.htt_cross_check_suggested,
    }


__all__ = ["build_mio_certificate", "certificate_to_payload"]
