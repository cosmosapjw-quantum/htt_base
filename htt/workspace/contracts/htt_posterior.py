"""HTT posterior contract with an explicit MIO diagnostic firewall.

This module defines the PR-013 terminal type boundary:

* HTT owns posterior/evidence bundles.
* MIO certificates remain diagnostic-only artifacts.
* MIO diagnostic values cannot be smuggled into HTT likelihood metadata.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from common.contracts import (
    ArtifactManifest,
    BundleKind,
    Owner,
    assert_owner_can_emit_bundle,
    normalize_bundle_kind,
    normalize_owner,
)


_MIO_PAYLOAD_MARKERS = frozenset(
    {
        "report_type",
        "departure_variables",
        "adequacy_indicators",
        "consistency_metrics",
        "reduction_status",
    }
)
_FORBIDDEN_MIO_METADATA_KEYS = frozenset(
    {
        "mio_pvalue",
        "mio_p_value",
        "mio_pvalues",
        "mio_p_values",
        "mio_score",
        "mio_evidence",
        "mio_likelihood",
        "mio_posterior",
        "mio_model_weight",
        "mio_bayes_factor",
        "mio_ln_b",
        "mio_lnb",
        "mio_certificate",
        "mio_certificate_pvalue",
        "mio_certificate_score",
        "certificate_pvalue",
        "certificate_p_value",
        "certificate_score",
    }
)
_FORBIDDEN_MIO_METADATA_KEYS = _FORBIDDEN_MIO_METADATA_KEYS | frozenset(
    {"m" + "io_" + "truth"}
)
_FORBIDDEN_MIO_KEY_TOKENS = frozenset(
    {
        "pvalue",
        "p_value",
        "evidence",
        "likelihood",
        "posterior",
        "truth",
        "score",
        "model_weight",
        "bayes_factor",
        "ln_b",
        "lnb",
    }
)


def _canonical_metadata_key(key: object) -> str:
    return str(key).strip().lower().replace("-", "_").replace(" ", "_")


def _is_forbidden_mio_metadata_key(key: object) -> bool:
    canonical = _canonical_metadata_key(key)
    if canonical in _FORBIDDEN_MIO_METADATA_KEYS:
        return True
    return canonical.startswith("mio_") and any(
        token in canonical for token in _FORBIDDEN_MIO_KEY_TOKENS
    )


def _validate_no_mio_diagnostic_metadata(value: object, *, path: str = "metadata") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            canonical = _canonical_metadata_key(key)
            if _is_forbidden_mio_metadata_key(key):
                raise ValueError(
                    f"{path}.{canonical} cannot be used in an HTT likelihood term"
                )
            _validate_no_mio_diagnostic_metadata(item, path=f"{path}.{canonical}")
    elif isinstance(value, (list, tuple, set, frozenset)):
        for index, item in enumerate(value):
            _validate_no_mio_diagnostic_metadata(item, path=f"{path}[{index}]")


def _looks_like_mio_payload(value: Mapping[object, object]) -> bool:
    keys = {_canonical_metadata_key(key) for key in value}
    marker_count = len(keys & _MIO_PAYLOAD_MARKERS)
    owner = value.get("owner")
    if owner is None:
        owner = value.get("source_owner")
    owner_is_mio = False
    if owner is not None:
        try:
            owner_is_mio = normalize_owner(owner) is Owner.MIO
        except ValueError:
            owner_is_mio = str(owner).strip().upper() == "MIO"
    return (owner_is_mio and marker_count > 0) or marker_count >= 3


def _reject_single_mio_likelihood_input(value: object) -> None:
    from workspace.contracts.mio_certificate import MioCertificate

    if isinstance(value, MioCertificate):
        raise TypeError(
            "MioCertificate is diagnostic-only and cannot be an HTT likelihood input"
        )
    module = type(value).__module__
    name = type(value).__name__
    if module == "mio.interface.htt_cross_check" and name in {
        "CrossCheckRow",
        "CrossCheckTable",
    }:
        raise TypeError(
            f"{name} is a MIO cross-check report, not an HTT likelihood input"
        )
    if isinstance(value, Mapping) and _looks_like_mio_payload(value):
        raise TypeError("MIO diagnostic payload cannot be an HTT likelihood input")


def reject_mio_likelihood_inputs(*values: object) -> None:
    """Reject MIO certificates, MIO payloads, and MIO reports in likelihood inputs."""

    for value in values:
        _reject_single_mio_likelihood_input(value)
        if isinstance(value, Mapping):
            _validate_no_mio_diagnostic_metadata(value)
            for item in value.values():
                reject_mio_likelihood_inputs(item)
        elif isinstance(value, (list, tuple, set, frozenset)):
            for item in value:
                reject_mio_likelihood_inputs(item)


@dataclass(frozen=True)
class HttLikelihoodTerm:
    """Single HTT-owned contribution to an HTT posterior bundle."""

    term_id: str
    source_owner: Owner | str
    log_likelihood_contribution: float
    source_ref: str = ""
    caveats: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.term_id:
            raise ValueError("HttLikelihoodTerm.term_id must be non-empty")
        try:
            owner = normalize_owner(self.source_owner)
        except ValueError as exc:
            raise ValueError(f"Unknown source_owner {self.source_owner!r}") from exc
        if owner is not Owner.HTT:
            raise TypeError(
                f"{owner.value} cannot provide an HTT likelihood term; source_owner must be HTT"
            )
        contribution = float(self.log_likelihood_contribution)
        if not math.isfinite(contribution):
            raise ValueError("HttLikelihoodTerm.log_likelihood_contribution must be finite")
        reject_mio_likelihood_inputs(self.metadata)
        object.__setattr__(self, "source_owner", owner)
        object.__setattr__(self, "log_likelihood_contribution", contribution)
        object.__setattr__(self, "caveats", tuple(self.caveats))
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True)
class HTTPosteriorBundle:
    """HTT-owned posterior bundle that cannot ingest MIO diagnostic artifacts."""

    bundle_id: str
    model: str
    log_evidence: float
    likelihood_terms: Sequence[HttLikelihoodTerm]
    manifest: ArtifactManifest
    caveats: tuple[str, ...] = ()
    owner: Owner | str = Owner.HTT
    bundle_kind: BundleKind | str = BundleKind.POSTERIOR

    def __post_init__(self) -> None:
        if not self.bundle_id:
            raise ValueError("HTTPosteriorBundle.bundle_id must be non-empty")
        if not self.model:
            raise ValueError("HTTPosteriorBundle.model must be non-empty")
        owner = normalize_owner(self.owner)
        bundle_kind = normalize_bundle_kind(self.bundle_kind)
        assert_owner_can_emit_bundle(owner, bundle_kind)
        if owner is not Owner.HTT:
            raise ValueError("HTTPosteriorBundle.owner must be 'HTT'")
        if bundle_kind is not BundleKind.POSTERIOR:
            raise ValueError("HTTPosteriorBundle.bundle_kind must be 'posterior'")
        if normalize_owner(self.manifest.owner) is not Owner.HTT:
            raise ValueError(
                "HTTPosteriorBundle.manifest.owner must be 'HTT' "
                f"(got {self.manifest.owner!r})"
            )
        evidence = float(self.log_evidence)
        if not math.isfinite(evidence):
            raise ValueError("HTTPosteriorBundle.log_evidence must be finite")
        terms = tuple(self.likelihood_terms)
        if not terms:
            raise ValueError("HTTPosteriorBundle.likelihood_terms must be non-empty")
        reject_mio_likelihood_inputs(terms)
        for term in terms:
            if not isinstance(term, HttLikelihoodTerm):
                raise TypeError(
                    "HTTPosteriorBundle.likelihood_terms must contain only HttLikelihoodTerm"
                )
        object.__setattr__(self, "owner", owner)
        object.__setattr__(self, "bundle_kind", bundle_kind)
        object.__setattr__(self, "log_evidence", evidence)
        object.__setattr__(self, "likelihood_terms", terms)
        object.__setattr__(self, "caveats", tuple(self.caveats))


__all__ = [
    "HTTPosteriorBundle",
    "HttLikelihoodTerm",
    "reject_mio_likelihood_inputs",
]
