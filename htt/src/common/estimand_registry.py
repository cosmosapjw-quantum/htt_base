"""PR-134 estimand / population / dependency / selection / nuisance
registry.

Each analysis carries a TYPED contract with every field explicit and
fail-closed — target population, observation unit, dependence cluster,
selection/mask/window, preprocessing, estimand, nuisance family,
prior/null/multiplicity, allowed transformations, and generative
branch. A missing or defaulted field is rejected, so no hidden
sample/window/depth convention survives. The deterministic
TEMPLATE-mean generative branch and the stochastic COVARIANCE data
factor are separate typed branches and are never mixed.

Each contract carries a content-addressed estimand fingerprint (any
field edit mints a new fingerprint), dependence is recorded as a NAMED
cluster (never silent independent rows), and the registry is immutable:
a post-hoc nuisance/depth/window edit requires a NEW analysis_id and
multiplicity. Active inference naming an unregistered analysis is
blocked.

Estimand/analysis specification mechanics only (C1) — no measurement,
no family/geometry claim, and the five representative contracts are
specification records built from documented metadata, NOT PR4 data
runs. roadmap_rescue_v1:C1.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Mapping

SCHEMA_VERSION = "pr134.estimand_registry.v1"

REQUIRED_FIELDS = (
    "analysis_id", "target_population", "observation_unit",
    "dependence_cluster", "selection_window", "preprocessing",
    "estimand", "nuisance_family", "prior_null_multiplicity",
    "allowed_transformations", "generative_branch",
)

# The named dependence structures. The flat/independent label is
# admissible ONLY with an explicit justification and is never a default.
# Matched against tokens AND substrings after normalizing every
# separator (hyphen/space/etc) to "_" so "assumed-independent",
# "iid gaussian", "independent-rows" cannot evade the guard.
_FLAT_TOKENS = ("independent", "iid", "flat", "uncorrelated")
_FLAT_SUBSTRINGS = ("independent", "uncorrelated", "iid")


def _names_independence(dependence_cluster: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "_", dependence_cluster.lower())
    tokens = set(normalized.split("_"))
    if tokens & set(_FLAT_TOKENS):
        return True
    joined = normalized.replace("_", "")
    return any(sub in joined for sub in _FLAT_SUBSTRINGS)


class GenerativeBranch(str, Enum):
    DETERMINISTIC_TEMPLATE_MEAN = "deterministic_template_mean"
    STOCHASTIC_COVARIANCE_FACTOR = "stochastic_covariance_factor"


class EstimandRegistryError(ValueError):
    """Raised on any contract / branch / immutability / gate violation."""


@dataclass(frozen=True)
class AnalysisContract:
    """One typed analysis contract. Every field is required and
    non-empty; the generative branch is a typed enum; the dependence
    cluster may not silently default to an independent label."""

    analysis_id: str
    target_population: str
    observation_unit: str
    dependence_cluster: str
    selection_window: str
    preprocessing: str
    estimand: str
    nuisance_family: str
    prior_null_multiplicity: str
    allowed_transformations: str
    generative_branch: GenerativeBranch
    dependence_justification: str = ""
    supersedes: str = ""

    def __post_init__(self) -> None:
        for name in REQUIRED_FIELDS:
            if name == "generative_branch":
                continue
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise EstimandRegistryError(
                    f"contract field {name!r} must be a non-empty string "
                    "(no hidden/defaulted conventions)")
            object.__setattr__(self, name, value.strip())
        for name in ("dependence_justification", "supersedes"):
            value = getattr(self, name)
            if not isinstance(value, str):
                raise EstimandRegistryError(
                    f"contract field {name!r} must be a string"
                )
            object.__setattr__(self, name, value.strip())
        if not isinstance(self.generative_branch, GenerativeBranch):
            raise EstimandRegistryError(
                "generative_branch must be a GenerativeBranch enum")
        if _names_independence(self.dependence_cluster) and \
                not self.dependence_justification.strip():
            raise EstimandRegistryError(
                f"dependence_cluster {self.dependence_cluster!r} names "
                "a flat/independent structure without a justification "
                "— independent-rows is never the silent default")

    @classmethod
    def from_payload(cls, payload: Mapping) -> "AnalysisContract":
        # preprocessing/allowed_transformations may be supplied with
        # defaults in the spec's representative rows; require them here
        # so an omission is a hard error, not a silent fill.
        missing = [f for f in REQUIRED_FIELDS if f not in payload]
        if missing:
            raise EstimandRegistryError(
                f"contract registration missing fields: {missing}")
        try:
            branch = GenerativeBranch(payload["generative_branch"])
        except ValueError as exc:
            raise EstimandRegistryError(
                f"invalid generative_branch: {exc}") from exc
        return cls(
            analysis_id=payload["analysis_id"],
            target_population=payload["target_population"],
            observation_unit=payload["observation_unit"],
            dependence_cluster=payload["dependence_cluster"],
            selection_window=payload["selection_window"],
            preprocessing=payload["preprocessing"],
            estimand=payload["estimand"],
            nuisance_family=payload["nuisance_family"],
            prior_null_multiplicity=payload["prior_null_multiplicity"],
            allowed_transformations=payload["allowed_transformations"],
            generative_branch=branch,
            dependence_justification=payload.get(
                "dependence_justification", ""),
            supersedes=payload.get("supersedes", ""),
        )

    def canonical_payload(self) -> dict:
        return {
            "analysis_id": self.analysis_id,
            "target_population": self.target_population,
            "observation_unit": self.observation_unit,
            "dependence_cluster": self.dependence_cluster,
            "selection_window": self.selection_window,
            "preprocessing": self.preprocessing,
            "estimand": self.estimand,
            "nuisance_family": self.nuisance_family,
            "prior_null_multiplicity": self.prior_null_multiplicity,
            "allowed_transformations": self.allowed_transformations,
            "generative_branch": self.generative_branch.value,
            "dependence_justification": self.dependence_justification,
            "supersedes": self.supersedes,
        }

    def estimand_fingerprint(self) -> str:
        """Content-addressed fingerprint over ALL fields — any edit
        mints a new fingerprint (immutability + multiplicity anchor)."""
        canonical = json.dumps(self.canonical_payload(), sort_keys=True)
        return "estid-" + hashlib.sha256(
            canonical.encode()).hexdigest()[:16]

    def channel_fingerprint(self) -> str:
        """Content-addressed fingerprint over the SPECIFICATION fields
        EXCLUDING analysis_id and lineage — two distinct analyses that
        share this are the SAME channel (flattening one onto the other
        is the defect the registry rejects)."""
        payload = self.canonical_payload()
        for key in ("analysis_id", "supersedes"):
            payload.pop(key, None)
        canonical = json.dumps(payload, sort_keys=True)
        return "chan-" + hashlib.sha256(canonical.encode()).hexdigest()[:16]


class EstimandRegistry:
    """Immutable typed registry. Re-registering an analysis_id with a
    different fingerprint, or editing a field in place, is refused — a
    change is a NEW analysis with a NEW id and multiplicity."""

    def __init__(self) -> None:
        self._contracts: dict[str, AnalysisContract] = {}
        self._fingerprints: dict[str, str] = {}
        self._channels: dict[str, str] = {}
        self._multiplicity: dict[str, int] = {}

    def register(self, contract: AnalysisContract) -> str:
        fp = contract.estimand_fingerprint()
        existing = self._contracts.get(contract.analysis_id)
        if existing is not None:
            if existing.estimand_fingerprint() != fp:
                raise EstimandRegistryError(
                    f"analysis {contract.analysis_id} already registered "
                    "with a different fingerprint — a field edit needs a "
                    "NEW analysis_id and multiplicity, not an in-place "
                    "change")
            return fp
        # flattening guard: two DISTINCT analyses that share the same
        # channel fingerprint (identical specification content up to the
        # id) are the same channel — flattening is refused.
        chan = contract.channel_fingerprint()
        chan_owner = self._channels.get(chan)
        if chan_owner is not None and chan_owner != contract.analysis_id:
            raise EstimandRegistryError(
                f"channel fingerprint {chan} already used by {chan_owner}"
                f" — flattening two distinct surveys ({contract.analysis_id}"
                " and the former) under one channel is refused")
        # estimand-fingerprint collision guard (defence in depth).
        clash = self._fingerprints.get(fp)
        if clash is not None and clash != contract.analysis_id:
            raise EstimandRegistryError(
                f"estimand fingerprint {fp} already used by {clash} — "
                "flattening two distinct surveys under one channel is "
                "refused")
        # multiplicity: a revision must NAME its predecessor and declare
        # a distinct prior_null_multiplicity (the added look-elsewhere
        # penalty), and the predecessor must already be registered.
        if contract.supersedes:
            predecessor = self._contracts.get(contract.supersedes)
            if predecessor is None:
                raise EstimandRegistryError(
                    f"revision {contract.analysis_id} supersedes "
                    f"{contract.supersedes!r} which is not registered")
            if contract.prior_null_multiplicity == \
                    predecessor.prior_null_multiplicity:
                raise EstimandRegistryError(
                    f"revision {contract.analysis_id} supersedes "
                    f"{contract.supersedes} but leaves "
                    "prior_null_multiplicity unchanged — a post-hoc edit "
                    "must carry the added look-elsewhere multiplicity")
            self._multiplicity[contract.analysis_id] = \
                self._multiplicity.get(contract.supersedes, 1) + 1
        else:
            self._multiplicity[contract.analysis_id] = 1
        self._contracts[contract.analysis_id] = contract
        self._fingerprints[fp] = contract.analysis_id
        self._channels[chan] = contract.analysis_id
        return fp

    def multiplicity(self, analysis_id: str) -> int:
        """The look-elsewhere multiplicity count for a lineage (1 for an
        original analysis, +1 per revision)."""
        self.get(analysis_id)
        return self._multiplicity.get(analysis_id, 1)

    def get(self, analysis_id: str) -> AnalysisContract:
        contract = self._contracts.get(analysis_id)
        if contract is None:
            raise EstimandRegistryError(
                f"analysis {analysis_id!r} is not registered")
        return contract

    def require_registered_for_inference(self, analysis_id: str) -> None:
        """Active inference may only run against a registered contract."""
        self.get(analysis_id)

    def ids(self) -> list[str]:
        return sorted(self._contracts)

    def dependency_graph(self) -> dict:
        """Group analyses by their named dependence cluster — the graph
        makes the cluster structure explicit (never independent rows)."""
        clusters: dict[str, list[str]] = {}
        for cid, contract in self._contracts.items():
            clusters.setdefault(contract.dependence_cluster, []).append(cid)
        return {cluster: sorted(members)
                for cluster, members in sorted(clusters.items())}


# ---------------------------------------------------------------------------
# Generative-branch separation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BranchComponent:
    """A generative-model component tagged with its branch role and its
    owning analysis. The composer refuses to mix a template mean with a
    covariance factor, or components from different analyses."""

    analysis_id: str
    branch: GenerativeBranch
    descriptor: str


def compose_generative_model(mean: BranchComponent,
                             covariance: BranchComponent) -> dict:
    """Compose a template MEAN with a stochastic COVARIANCE factor — the
    two must be the two DISTINCT branches, and must belong to the SAME
    analysis. Mixing branches or cross-analysis parts is blocked."""
    if mean.branch is not GenerativeBranch.DETERMINISTIC_TEMPLATE_MEAN:
        raise EstimandRegistryError(
            "the mean component must be the deterministic_template_mean "
            "branch — branch mixing is refused")
    if covariance.branch is not \
            GenerativeBranch.STOCHASTIC_COVARIANCE_FACTOR:
        raise EstimandRegistryError(
            "the covariance component must be the "
            "stochastic_covariance_factor branch — branch mixing is "
            "refused")
    if mean.analysis_id != covariance.analysis_id:
        raise EstimandRegistryError(
            f"cannot mix a template mean from {mean.analysis_id} with a "
            f"covariance factor from {covariance.analysis_id} — "
            "cross-analysis branch composition is refused")
    return {
        "analysis_id": mean.analysis_id,
        "template_mean": mean.descriptor,
        "covariance_factor": covariance.descriptor,
        "branches_kept_separate": True,
    }


# ---------------------------------------------------------------------------
# Caption gate
# ---------------------------------------------------------------------------

_FORBIDDEN_PHRASES = tuple(
    a + b for a, b in (
        ("all surveys share", " one channel"),
        ("dependency assumed", " independent"),
        ("template and covariance", " merged"),
        ("measured the", " dipole"),
        ("family identified", " from estimand"),
        # generic over-claim phrases (the exported lint is comprehensive,
        # not just the five negative-scan patterns).
        ("shear", " detected"),
        ("isotropy", " established"),
        ("Bianchi geometry", " detected"),
        ("Bianchi family", " identified"),
        ("finding", " rescued"),
        ("validated as", " native"),
    )
)


def lint_caption(text: str) -> None:
    lowered = text.lower()
    for phrase in _FORBIDDEN_PHRASES:
        if phrase.lower() in lowered:
            raise EstimandRegistryError(
                "caption carries forbidden flattening/independence/"
                "merge/measurement/over-claim language")


def generate_caption(registry: EstimandRegistry) -> str:
    graph = registry.dependency_graph()
    text = (
        f"[estimand_registry] {len(registry.ids())} representative "
        "analysis contracts (CF4/K1/DESI/ACT/JWST), every field explicit "
        f"and fail-closed, across {len(graph)} named dependence clusters "
        "(never independent rows). The template-mean and covariance-"
        "factor generative branches stay separate. Specification "
        "mechanics only; no measurement or family identification."
    )
    lint_caption(text)
    return text
