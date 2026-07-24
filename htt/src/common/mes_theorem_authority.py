"""PR-124 typed MES theorem/convention authority (the delivered successor
``mes.typed-successor.pr124`` that PR-122 reserved).

This module carries, per MES branch:

- the exact coefficient triple (strings of exact rationals);
- the source authority (arXiv/DOI or scan authority, page/equation, and the
  SHA-256 of the archived primary-source bytes where accessible);
- the convention translation (eps definitions, SAG observer-motion
  convention, C1/C2 reduction, W^2 normalization);
- the REAL independent derivation lineages with the inflation-exclusion
  rule (same implementation fingerprint collapses; a second engine never
  adds a lineage);
- the physical assumption uncertainty as its own field.

It also implements the authority *verifier*: authorization is derived from
exact receipt bytes (the generated PR-124 artifacts), never from
caller-supplied status strings. ``MesAuthorityVerification`` can only be
instantiated by running the full byte-level verification; the PR-122
successor pointer requires that instance to become AVAILABLE.

Claim discipline: this authority is domain/frame-conditional derived
mechanics at roadmap_rescue_v1:C1. It validates no observed scientific
result, changes no remediation disposition, and never turns engine
agreement into derivation independence (they are reported separately).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

SCHEMA_VERSION = "pr124.mes_theorem_authority.v1"

AUTHORITY_TABLE_PATH = "docs/generated/pr124_mes_authority_table.json"
CAS_CONTRACT_PATH = (
    "docs/generated/pr124_cas/CAS_CONTRACT_PR124_MES_GEODESIC.json"
)
CAS_ADJUDICATION_PATH = "docs/generated/pr124_cas_adjudication.json"
D2_RECEIPT_PATH = "docs/generated/pr124_d2_authority_receipt.json"
LINEAGE_RECEIPT_PATH = "docs/generated/pr124_lineage_receipt.json"

MINIMUM_LINEAGES_FOR_VERIFIED = 2

ARCHIVED_PRIMARY_SOURCES = {
    "mesa": {
        "path": "docs/audits/mes_primary_sources/mesa_astro-ph_9501016_PRD51_1525.txt",
        "sha256": "d500ffeef60f1f006393b7b2a21823b51bc4c9c9b41b7fb983f0393ce800217e",
        "citation": "Maartens, Ellis & Stoeger 1995a, PRD 51, 1525 (arXiv:astro-ph/9501016)",
    },
    "companion": {
        "path": "docs/audits/mes_primary_sources/companion_astro-ph_9510126_deltaT.txt",
        "sha256": "7ae6cf9288027338829d9964138596c2b909d49471193fa008d1c966eaab9765",
        "citation": "Maartens, Ellis & Stoeger 1996 companion (arXiv:astro-ph/9510126)",
    },
    "sag1997": {
        "path": "docs/audits/mes_primary_sources/sag1997_astro-ph_9904346_ApJ476_435.tex",
        "sha256": "00bb2c7c485ffb14433a90dae2d5d7709fbecd9c4eef986ec27d72f7dae5370e",
        "citation": "Stoeger, Araujo & Gebbie 1997, ApJ 476, 435 (arXiv:astro-ph/9904346)",
    },
}

CONVENTION_TRANSLATION = {
    "eps_definition": (
        "eps_L are the covariant CMB temperature multipole bound amplitudes "
        "of the linearized almost-EGS hierarchy (MESa eqs 51/52 context)"
    ),
    "eps1_attribution": (
        "SAG observer-motion convention: the observed CMB dipole is the "
        "observer's peculiar motion, so the residual cosmological dipole "
        "bound is eps1 = 0 (SAG 1997 eq 12; MESa notes the same limit)"
    ),
    "c1_c2_reduction": (
        "C1: a spatial-gradient bound is <= the same-order time-derivative "
        "bound; C2: k-th time derivatives reduce by (1/(Theta t_R))^k with "
        "Theta t_R ~ 3; net factor (1/3)^d per total derivative order d"
    ),
    "w2_normalization": "W^2 = omega_ab omega^ab / (6 H^2) (registered code convention)",
    "ceiling_map": "W2_max = (3/2) B_omega^2; Sigma2_max = (3/2) B_sigma^2",
}

# Registered derivation lineages. ``implementation_fingerprint`` is the
# inflation-exclusion key: identical fingerprints collapse to ONE lineage
# regardless of how many engines re-evaluate them.
BRANCHES: dict[str, dict] = {
    "MES_G_SIGMA": {
        "congruence": "geodesic",
        "status": "VERIFIED",
        "coefficients_exact": ("5/3", "3", "3/7"),
        "sources": [
            {**ARCHIVED_PRIMARY_SOURCES["mesa"], "equation": "eq (59); raw eq (51)"},
        ],
        "lineages": [
            {
                "lineage_id": "mesa_published_eq59",
                "kind": "published_paper",
                "implementation_fingerprint": "arXiv:astro-ph/9501016:eq59",
            },
            {
                "lineage_id": "in_repo_c1c2_reduction_from_eq51",
                "kind": "in_repo_reduction",
                "implementation_fingerprint": (
                    "htt/obsstat/egs3_mes_rederivation.py::reduce_raw_bound(_RAW_SIGMA)"
                ),
                "source_path": "htt/obsstat/egs3_mes_rederivation.py",
                "source_sha256": (
                    "8051e61e01cc7d2a6d321677d9027f6b2aa2ce5fe740abd59ae1754030f4ec6f"
                ),
            },
        ],
        "physical_assumption_uncertainty": (
            "C2 is an order-of-magnitude estimate (Theta t_R ~ 3); the bound "
            "is linear almost-EGS and diagonal-combination conditional"
        ),
    },
    "MES_G_OMEGA": {
        "congruence": "geodesic",
        "status": "VERIFIED",
        "coefficients_exact": ("10/3", "2/15", "0"),
        "sources": [
            {**ARCHIVED_PRIMARY_SOURCES["mesa"], "equation": "eq (60); raw eq (52)"},
            {**ARCHIVED_PRIMARY_SOURCES["sag1997"], "equation": "eq (4)"},
        ],
        "lineages": [
            {
                "lineage_id": "mesa_published_eq60",
                "kind": "published_paper",
                "implementation_fingerprint": "arXiv:astro-ph/9501016:eq60",
            },
            {
                "lineage_id": "sag1997_published_eq4",
                "kind": "external_citing_source",
                "implementation_fingerprint": "arXiv:astro-ph/9904346:eq4",
            },
            {
                "lineage_id": "in_repo_c1c2_reduction_from_eq52",
                "kind": "in_repo_reduction",
                "implementation_fingerprint": (
                    "htt/obsstat/egs3_mes_rederivation.py::reduce_raw_bound(_RAW_OMEGA_MESA)"
                ),
                "source_path": "htt/obsstat/egs3_mes_rederivation.py",
                "source_sha256": (
                    "8051e61e01cc7d2a6d321677d9027f6b2aa2ce5fe740abd59ae1754030f4ec6f"
                ),
            },
        ],
        "physical_assumption_uncertainty": (
            "same C1/C2 regime as the shear branch; geodesic congruence "
            "(u_dot = 0) is load-bearing — the triple does not survive tilt"
        ),
    },
    "MES_G_ACCEL": {
        "congruence": "geodesic",
        "status": "VERIFIED_STRUCTURAL",
        "coefficients_exact": ("0", "0", "0"),
        "sources": [
            {**ARCHIVED_PRIMARY_SOURCES["mesa"], "equation": "p.123 (geodesic flow, u_dot = 0)"},
            {**ARCHIVED_PRIMARY_SOURCES["sag1997"], "equation": "assumption set (no acceleration bound)"},
        ],
        "lineages": [
            # A structural ABSENCE claim (no acceleration bound) has no raw
            # published bound to reduce, so only distinct PUBLICATIONS count
            # as lineages here — an in-repo restatement re-citing MESa p.123
            # is the same origin and would inflate the count.
            {
                "lineage_id": "mesa_geodesic_assumption",
                "kind": "published_paper",
                "implementation_fingerprint": "arXiv:astro-ph/9501016:p123-geodesic",
            },
            {
                "lineage_id": "sag1997_geodesic_assumption_set",
                "kind": "external_citing_source",
                "implementation_fingerprint": (
                    "arXiv:astro-ph/9904346:assumption-set-no-accel-bound"
                ),
            },
        ],
        "physical_assumption_uncertainty": (
            "structural: u_dot = 0 removes the dipole acceleration source, "
            "so no acceleration ceiling exists on the geodesic branch "
            "(A^2 = 0); both lineages are publications carrying the geodesic "
            "assumption set (SAG 1997 is Stoeger-coauthored — correlated "
            "authorship disclosed)"
        ),
    },
    "MES_NG_OMEGA": {
        "congruence": "non_geodesic",
        "status": "UNVERIFIED_PRINT_ONLY",
        "coefficients_exact": ("3/4", "2", "2/7"),
        "sources": [
            {
                "path": None,
                "sha256": None,
                "citation": "Maartens, Ellis & Stoeger 1995b, PRD 51, 5942 (print-only; no accessible archive)",
                "equation": "registered as Thm 3.2 / eq 3.12 numbering of an in-house reconstruction; appears in no accessible source",
            },
        ],
        "lineages": [
            {
                "lineage_id": "mesb_print_only",
                "kind": "published_paper",
                "implementation_fingerprint": "PRD-51-5942:print-only",
            },
        ],
        "physical_assumption_uncertainty": (
            "non-geodesic (tilted) congruence; the registered triple is not "
            "reconstructable from any accessible source and the in-house "
            "reconstruction was REFUTED (rev-r190); never a live ceiling"
        ),
    },
    "MES_NG_ACCEL": {
        "congruence": "non_geodesic",
        "status": "UNVERIFIED_PRINT_ONLY",
        "coefficients_exact": ("3/4", "1", "3/14"),
        "sources": [
            {
                "path": None,
                "sha256": None,
                "citation": "Maartens, Ellis & Stoeger 1995b, PRD 51, 5942 (print-only; no accessible archive)",
                "equation": "no acceleration bound appears in any accessible primary source",
            },
        ],
        "lineages": [
            {
                "lineage_id": "mesb_print_only",
                "kind": "published_paper",
                "implementation_fingerprint": "PRD-51-5942:print-only",
            },
        ],
        "physical_assumption_uncertainty": (
            "both accessible primary papers are geodesic; an acceleration "
            "ceiling has no accessible derivation at all"
        ),
    },
}


class MesAuthorityError(ValueError):
    """Raised when the PR-124 authority receipts fail verification."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_independent_lineages(lineages: Sequence[Mapping]) -> int:
    """Collapse lineages by implementation fingerprint (inflation guard).

    Re-evaluating the same implementation/AST/expression on another engine
    keeps the same fingerprint and therefore never increases this count.
    """
    fingerprints = set()
    for lineage in lineages:
        fingerprint = str(lineage.get("implementation_fingerprint") or "")
        if not fingerprint:
            raise MesAuthorityError(
                "every lineage needs an implementation_fingerprint"
            )
        fingerprints.add(fingerprint)
    return len(fingerprints)


def validate_claimed_lineage_count(
    lineages: Sequence[Mapping], claimed_count: int
) -> int:
    """Reject source-count inflation: a claimed independent-derivation count
    above the fingerprint-collapsed count is an error."""
    collapsed = count_independent_lineages(lineages)
    if claimed_count > collapsed:
        raise MesAuthorityError(
            f"claimed independent derivation count {claimed_count} exceeds "
            f"the fingerprint-collapsed count {collapsed} (same-implementation "
            "re-evaluation never adds a derivation)"
        )
    return collapsed


def validate_branch_entry(branch_id: str, entry: Mapping) -> dict:
    """Fail-closed structural validation of one branch row (branch-swap and
    status/coefficient binding guard)."""
    registered = BRANCHES.get(branch_id)
    if registered is None:
        raise MesAuthorityError(f"unknown MES branch {branch_id!r}")
    if str(entry.get("congruence")) != registered["congruence"]:
        raise MesAuthorityError(
            f"{branch_id}: congruence {entry.get('congruence')!r} does not "
            f"match the registered branch ({registered['congruence']})"
        )
    if str(entry.get("status")) != registered["status"]:
        raise MesAuthorityError(
            f"{branch_id}: status {entry.get('status')!r} does not match the "
            f"registered branch ({registered['status']})"
        )
    if tuple(entry.get("coefficients_exact") or ()) != tuple(
        registered["coefficients_exact"]
    ):
        raise MesAuthorityError(
            f"{branch_id}: coefficient triple does not match the registered "
            "branch (branch-swap or corruption)"
        )
    claimed = int(entry.get("independent_derivation_count", -1))
    collapsed = validate_claimed_lineage_count(registered["lineages"], claimed)
    if claimed != collapsed:
        raise MesAuthorityError(
            f"{branch_id}: independent_derivation_count {claimed} != "
            f"fingerprint-collapsed count {collapsed}"
        )
    verified_like = registered["status"] in {"VERIFIED", "VERIFIED_STRUCTURAL"}
    if verified_like and collapsed < MINIMUM_LINEAGES_FOR_VERIFIED:
        raise MesAuthorityError(
            f"{branch_id}: a verified branch needs at least "
            f"{MINIMUM_LINEAGES_FOR_VERIFIED} independent lineages"
        )
    if not verified_like and collapsed >= MINIMUM_LINEAGES_FOR_VERIFIED:
        raise MesAuthorityError(
            f"{branch_id}: an unverified print-only branch cannot claim "
            f"{collapsed} independent lineages"
        )
    return {"branch_id": branch_id, "independent_derivation_count": collapsed}


def branch_table_payload() -> dict:
    """The canonical branch-authority table content (deterministic)."""
    table = {}
    for branch_id, entry in BRANCHES.items():
        table[branch_id] = {
            "branch_id": branch_id,
            "congruence": entry["congruence"],
            "status": entry["status"],
            "coefficients_exact": list(entry["coefficients_exact"]),
            "sources": entry["sources"],
            "convention_translation": CONVENTION_TRANSLATION,
            "lineages": entry["lineages"],
            "independent_derivation_count": count_independent_lineages(
                entry["lineages"]
            ),
            "physical_assumption_uncertainty": entry[
                "physical_assumption_uncertainty"
            ],
        }
    return table


def validate_d2_receipt(payload: Mapping, repo_root: Path) -> dict:
    """Fail-closed D2 dual-track receipt validation (zero-test guard)."""
    rust = payload.get("rust_target")
    python_anchor = payload.get("python_anchor")
    if not isinstance(rust, Mapping) or not isinstance(python_anchor, Mapping):
        raise MesAuthorityError("d2 receipt needs rust_target and python_anchor")
    value = rust.get("d2_value_uK2")
    if not isinstance(value, (int, float)) or not value > 0.0:
        raise MesAuthorityError(
            f"rust D2 target must be executed and NONZERO (got {value!r})"
        )
    for count_key in ("tests_collected", "tests_passed"):
        count = rust.get(count_key)
        if not isinstance(count, int) or count < 1:
            raise MesAuthorityError(f"rust receipt {count_key} must be >= 1")
    if int(rust.get("tests_failed", -1)) != 0:
        raise MesAuthorityError("rust receipt must record zero failures")
    for path_key, sha_key in (
        ("source_path", "source_sha256"),
        ("cargo_manifest_path", "cargo_manifest_sha256"),
        ("transcript_path", "transcript_sha256"),
    ):
        rel = str(rust.get(path_key) or "")
        expected = str(rust.get(sha_key) or "")
        if not rel or not expected:
            raise MesAuthorityError(f"rust receipt missing {path_key}/{sha_key}")
        target = repo_root / rel
        if not target.is_file():
            raise MesAuthorityError(f"rust receipt path missing: {rel}")
        actual = sha256_file(target)
        if actual != expected:
            raise MesAuthorityError(
                f"rust receipt hash mismatch for {rel}: {actual} != {expected}"
            )
    if not str(rust.get("toolchain") or "").strip():
        raise MesAuthorityError("rust receipt must record the toolchain")

    passed = python_anchor.get("tests_passed")
    collected = python_anchor.get("tests_collected")
    if (
        not isinstance(passed, int)
        or not isinstance(collected, int)
        or collected < 1
        or passed != collected
    ):
        raise MesAuthorityError(
            "python anchor receipt must record full collected == passed counts"
        )
    for path_key, sha_key in (
        ("test_path", "test_sha256"),
        ("golden_path", "golden_sha256"),
    ):
        rel = str(python_anchor.get(path_key) or "")
        expected = str(python_anchor.get(sha_key) or "")
        target = repo_root / rel
        if not rel or not expected or not target.is_file():
            raise MesAuthorityError(f"python anchor missing {path_key}")
        if sha256_file(target) != expected:
            raise MesAuthorityError(f"python anchor hash mismatch for {rel}")
    separation = str(payload.get("derivation_stream_separation") or "")
    if "Ma-Bertschinger" not in separation or "Ellis" not in separation:
        raise MesAuthorityError(
            "d2 receipt must state the separated derivation streams"
        )
    if "1002.086744" in json.dumps(dict(rust)):
        raise MesAuthorityError(
            "the executed receipt must not claim the dump_dl_spectrum_sparse "
            "bit-identical anchor (documented gap)"
        )
    return {"d2_value_uK2": float(value)}


def _load_json(path: Path, subject: str) -> Mapping:
    if not path.is_file():
        raise MesAuthorityError(f"{subject} missing: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MesAuthorityError(f"{subject} is not valid JSON") from exc
    if not isinstance(payload, Mapping):
        raise MesAuthorityError(f"{subject} must be a JSON object")
    return payload


def _verify_cas_adjudication(repo_root: Path) -> dict:
    """Validate the frozen PR-124 adjudication as historical evidence.

    Stored axis envelopes cannot establish current CAS authority.  A current
    pass requires a parent-observed ``cas_gate.py run-adjudicate`` execution.
    """
    contract_path = repo_root / CAS_CONTRACT_PATH
    if not contract_path.is_file():
        raise MesAuthorityError("CAS contract missing")
    contract_sha = sha256_file(contract_path)
    adjudication = _load_json(
        repo_root / CAS_ADJUDICATION_PATH, "CAS adjudication"
    )
    if adjudication.get("aggregate_status") != "CAS_4AXIS_PASS":
        raise MesAuthorityError(
            "authority requires CAS_4AXIS_PASS (got "
            f"{adjudication.get('aggregate_status')!r}); three axes never pass"
        )
    if adjudication.get("contract_sha256") != contract_sha:
        raise MesAuthorityError(
            "CAS adjudication is bound to a different contract hash (stale)"
        )
    statuses = adjudication.get("axis_statuses")
    if not isinstance(statuses, Mapping) or sorted(statuses) != [
        "lean", "sage_singular", "sympy", "wolfram_xact"
    ]:
        raise MesAuthorityError("adjudication must record all four axes")
    if any(status != "PASS" for status in statuses.values()):
        raise MesAuthorityError("every axis must be PASS for authority")
    if adjudication.get("errors"):
        raise MesAuthorityError("adjudication carries errors")
    if adjudication.get("missing_axes"):
        raise MesAuthorityError("adjudication reports missing axes")
    contract = _load_json(contract_path, "CAS contract")
    expected = (
        contract.get("target", {}).get("expected_exact_values")
        if isinstance(contract.get("target"), Mapping) else None
    )
    if not isinstance(expected, Mapping):
        raise MesAuthorityError("CAS contract lacks expected_exact_values")
    return {
        "contract_sha256": contract_sha,
        "expected_exact_values": expected,
        "historical_aggregate_status": "CAS_4AXIS_PASS",
        "current_authority": False,
    }


def validate_ceiling_map(b_exact: str, ceiling_exact: str) -> None:
    """The registered ceiling map is (3/2) B^2 exactly; anything else is the
    historical W^2-normalization defect class."""
    from fractions import Fraction

    b = Fraction(str(b_exact))
    ceiling = Fraction(str(ceiling_exact))
    if ceiling != Fraction(3, 2) * b * b:
        raise MesAuthorityError(
            f"ceiling map violated: {ceiling} != (3/2)*({b})^2 "
            f"(off by factor {ceiling / (Fraction(3, 2) * b * b)})"
        )


def validate_hierarchy_strict(e1: str, e2: str, e3: str) -> None:
    """Strict geodesic admissibility B_sigma > B_omega > 0 with the VERIFIED
    geodesic triples. Raises at (and above) the exact boundary e1_crit —
    accepting the boundary is the registered limit mutation."""
    from fractions import Fraction

    f1, f2, f3 = Fraction(str(e1)), Fraction(str(e2)), Fraction(str(e3))
    b_sigma = Fraction(5, 3) * f1 + 3 * f2 + Fraction(3, 7) * f3
    b_omega = Fraction(10, 3) * f1 + Fraction(2, 15) * f2
    if not (b_sigma > b_omega > 0):
        raise MesAuthorityError(
            f"strict hierarchy fails at e1={f1}: B_sigma={b_sigma} "
            f"!> B_omega={b_omega} (admissibility requires e1 < e1_crit)"
        )


def _branches_match_contract(expected: Mapping) -> None:
    """P0 guard: the authority BRANCHES coefficients/ceilings must equal the
    four-axis-adjudicated contract values — otherwise a BRANCHES edit could
    launder corrupted coefficients under the CAS receipt."""
    from fractions import Fraction

    def triple(values) -> tuple:
        return tuple(Fraction(str(v)) for v in values)

    pairs = (
        ("MES_G_SIGMA", "sigma_triple"),
        ("MES_G_OMEGA", "omega_triple"),
        ("MES_G_ACCEL", "accel_triple"),
    )
    for branch_id, key in pairs:
        registered = triple(BRANCHES[branch_id]["coefficients_exact"])
        adjudicated = triple(expected[key])
        if registered != adjudicated:
            raise MesAuthorityError(
                f"{branch_id} coefficients {registered} differ from the "
                f"four-axis-adjudicated contract values {adjudicated}"
            )
    # ceiling self-consistency against the adjudicated exact values
    validate_ceiling_map(expected["B_omega_exact"], expected["W2_max_exact"])
    validate_ceiling_map(expected["B_sigma_exact"], expected["Sigma2_max_exact"])
    # hierarchy witnesses: strict at e1 = 0; the observed dipole must FAIL
    eps = expected["eps_registered"]
    validate_hierarchy_strict("0", eps["e2"], eps["e3"])
    try:
        validate_hierarchy_strict(expected["e1_observed"], eps["e2"], eps["e3"])
    except MesAuthorityError:
        pass
    else:
        raise MesAuthorityError(
            "the observed dipole unexpectedly satisfies the strict "
            "hierarchy (admissibility exclusion lost)"
        )


def _verify_lineage_sources(repo_root: Path) -> None:
    """P1 guard: in-repo lineage fingerprints must resolve to real files with
    pinned bytes — otherwise 'independent derivations' are just strings."""
    for branch_id, entry in BRANCHES.items():
        for lineage in entry["lineages"]:
            rel = lineage.get("source_path")
            if lineage.get("kind") == "in_repo_reduction" and not rel:
                raise MesAuthorityError(
                    f"{branch_id}: in-repo lineage "
                    f"{lineage.get('lineage_id')} lacks a pinned source"
                )
            if not rel:
                continue
            expected = str(lineage.get("source_sha256") or "")
            target = repo_root / str(rel)
            if not expected or not target.is_file():
                raise MesAuthorityError(
                    f"{branch_id}: lineage source missing: {rel}"
                )
            if sha256_file(target) != expected:
                raise MesAuthorityError(
                    f"{branch_id}: lineage source bytes drifted: {rel}"
                )


def _verify_archived_sources(repo_root: Path) -> None:
    """P1 guard: the archived primary-source scans must match their declared
    pins (a swapped MESa transcription must not flow into the contract)."""
    for key, source in ARCHIVED_PRIMARY_SOURCES.items():
        target = repo_root / source["path"]
        if not target.is_file():
            raise MesAuthorityError(f"archived primary source missing: {key}")
        if sha256_file(target) != source["sha256"]:
            raise MesAuthorityError(
                f"archived primary source bytes drifted: {key}"
            )


def _verify_consumer_scan(repo_root: Path) -> dict:
    """Live consumer-level scan (stale triples, bypasses, hash drift).

    Uses the consumer-only scanning layer so verification does not recurse
    through the successor-registry validation that depends on this verifier.
    """
    from common.mes_successor_registry import (  # local import: avoid cycle at module load
        MesConsumerIssueCode,
        scan_consumer_sources_only,
    )

    findings = scan_consumer_sources_only(repo_root)
    stale = [f for f in findings
             if f.code is MesConsumerIssueCode.STALE_MES_TRIPLE]
    if stale:
        raise MesAuthorityError(
            f"stale MES triples in active consumers: "
            f"{[f.subject for f in stale]}"
        )
    if findings:
        raise MesAuthorityError(
            "consumer scan not clean: "
            f"{[(f.code.value, f.subject) for f in findings]}"
        )
    return {"stale_triples": 0, "findings": 0}


@dataclass(frozen=True)
class MesAuthorityVerification:
    """Proof-of-verification token.

    Instantiating this class RUNS the full byte-level verification against
    the repository; it raises ``MesAuthorityError`` on any failure. A caller
    therefore cannot fabricate an instance whose receipts do not verify —
    possession of the instance is the authorization evidence the PR-122
    successor pointer requires (strings alone never escalate).
    """

    repo_root: Path
    receipt_sha256: str = field(init=False, default="")
    d2_value_uK2: float = field(init=False, default=0.0)
    cas_contract_sha256: str = field(init=False, default="")

    def __post_init__(self) -> None:
        root = Path(self.repo_root).resolve()
        # 1. legacy theorem registry byte quarantine + honest counting
        from common.theorem_signatures import (
            TheoremSignatureError,
            load_signature_registry,
        )

        registry = load_signature_registry(root)
        # negative probe: the raw legacy entry count must FAIL the counting
        # rule (a gate that accepts the historical overstatement is broken)
        if registry.legacy_entry_count > registry.theorem_count():
            try:
                registry.reject_overstated_count(registry.legacy_entry_count)
            except TheoremSignatureError:
                pass
            else:
                raise MesAuthorityError(
                    "overstatement gate is broken: the raw legacy entry "
                    "count was accepted as a theorem count"
                )

        # 2. four-axis CAS adjudication bound to the on-disk contract, and
        #    the P0 guard: BRANCHES coefficients/ceilings/witnesses must
        #    equal the adjudicated contract's exact values (a BRANCHES edit
        #    cannot launder corrupted coefficients under the CAS receipt)
        cas = _verify_cas_adjudication(root)
        _branches_match_contract(cas["expected_exact_values"])
        if not cas["current_authority"]:
            raise MesAuthorityError(
                "stored PR-124 CAS adjudication is diagnostic-only; current "
                "authority requires parent-observed cas_gate.py "
                "run-adjudicate"
            )

        # 2b. lineage sources and archived primary sources are byte-pinned
        _verify_lineage_sources(root)
        _verify_archived_sources(root)

        # 3. D2 dual-track execution receipt (nonzero, hash-bound)
        d2_payload = _load_json(root / D2_RECEIPT_PATH, "D2 receipt")
        d2 = validate_d2_receipt(d2_payload, root)

        # 4. lineage receipt consistent with the registered branch table
        lineage_payload = _load_json(
            root / LINEAGE_RECEIPT_PATH, "lineage receipt"
        )
        branches = lineage_payload.get("branches")
        if not isinstance(branches, Mapping) or set(branches) != set(BRANCHES):
            raise MesAuthorityError(
                "lineage receipt must cover exactly the registered branches"
            )
        for branch_id, entry in branches.items():
            validate_branch_entry(branch_id, entry)

        # 5. authority table artifact: content equals the registered table.
        #    Read the bytes ONCE and hash the same bytes (no TOCTOU window
        #    between the content check and the receipt hash).
        table_path = root / AUTHORITY_TABLE_PATH
        if not table_path.is_file():
            raise MesAuthorityError("authority table missing")
        table_bytes = table_path.read_bytes()
        try:
            table_payload = json.loads(table_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MesAuthorityError("authority table is not valid JSON") from exc
        if not isinstance(table_payload, Mapping):
            raise MesAuthorityError("authority table must be a JSON object")
        if table_payload.get("branch_table") != branch_table_payload():
            raise MesAuthorityError(
                "authority table content differs from the registered branch "
                "table (branch swap or drift)"
            )
        refs = table_payload.get("bound_artifacts")
        if not isinstance(refs, Mapping):
            raise MesAuthorityError("authority table must bind its artifacts")
        for rel, expected in refs.items():
            target = root / str(rel)
            if not target.is_file() or sha256_file(target) != str(expected):
                raise MesAuthorityError(
                    f"authority table binding stale for {rel}"
                )

        # 6. live consumer scan: zero stale triples, zero findings
        _verify_consumer_scan(root)

        object.__setattr__(self, "repo_root", root)
        object.__setattr__(self, "receipt_sha256", sha256_bytes(table_bytes))
        object.__setattr__(self, "d2_value_uK2", d2["d2_value_uK2"])
        object.__setattr__(
            self, "cas_contract_sha256", cas["contract_sha256"]
        )


def verify_authority_receipt(repo_root: Path) -> MesAuthorityVerification:
    """Run the full verification; raises MesAuthorityError on any failure."""
    return MesAuthorityVerification(repo_root=Path(repo_root))
