#!/usr/bin/env python3
"""PR-125 runner: canonical frame/order/domain premise contract.

``--write`` builds / ``--check`` verifies (fresh build must semantically
equal disk):

- the registered premise-contract registry (explicit contracts only);
- the theorem-to-frame dependency graph (every CHECKED signature in
  THEOREM_SIGNATURES_V2 binds to exactly one registered contract);
- the exact kinematic witness report (round-trip / associativity /
  antisymmetry / limit predicates, all exact Fractions);
- the mutation report (six preregistered mutants, all killed by the real
  validators in ``common.frame_contract``).

Convention contract correctness at roadmap_rescue_v1:C1 only; no physical
statement is validated and no remediation disposition changes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt" / "src"))

import yaml  # noqa: E402

from common.frame_contract import (  # noqa: E402
    BackgroundClass,
    Frame,
    FrameBoost,
    FrameContractError,
    HarmonicConvention,
    KinematicState,
    PerturbativeOrder,
    PremiseContract,
    RedshiftDepthConvention,
    UnitsConvention,
    compose_beta,
    flrw_limit,
    global_tilt_limit,
    legacy_reproduction_contract,
    local_boost_limit,
    no_tilt_limit,
    require_flrw_limit,
    transform_tilt,
)
from common.theorem_signatures import load_signature_registry  # noqa: E402

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr125_spec.yaml"
OUTPUTS = {
    "registry": "docs/generated/pr125_frame_contract_registry.json",
    "graph": "docs/generated/pr125_theorem_frame_graph.json",
    "witness": "docs/generated/pr125_kinematic_witness_report.json",
    "mutations": "docs/generated/pr125_mutation_report.json",
    "manifest": "docs/generated/pr125_artifact_manifest.json",
}

# The three registered active contracts (explicit fields only).
REGISTERED_CONTRACTS = {
    "mes_linear_cmb": PremiseContract(
        frame=Frame.CMB, perturbative_order=PerturbativeOrder.LINEAR,
        background_class=BackgroundClass.FLRW_FLAT,
        units=UnitsConvention.DIMENSIONLESS_HUBBLE_NORMALIZED,
        harmonic_convention=HarmonicConvention.COMPLEX_SPHERICAL_CAMB,
        redshift_depth_convention=RedshiftDepthConvention.CZ_KM_S,
    ),
    "comparator_exact_normal": PremiseContract(
        frame=Frame.NORMAL, perturbative_order=PerturbativeOrder.EXACT,
        background_class=BackgroundClass.FLRW_CURVED,
        units=UnitsConvention.DIMENSIONLESS_HUBBLE_NORMALIZED,
        harmonic_convention=HarmonicConvention.COMPLEX_SPHERICAL_CAMB,
        redshift_depth_convention=RedshiftDepthConvention.CZ_KM_S,
    ),
    "teff_exact_cmb": PremiseContract(
        frame=Frame.CMB, perturbative_order=PerturbativeOrder.EXACT,
        background_class=BackgroundClass.FLRW_FLAT,
        units=UnitsConvention.DIMENSIONLESS_HUBBLE_NORMALIZED,
        harmonic_convention=HarmonicConvention.COMPLEX_SPHERICAL_CAMB,
        redshift_depth_convention=RedshiftDepthConvention.CZ_KM_S,
    ),
    # Pure-algebra sector: the comparator/fractional-program theorems whose
    # prose says "(no sky frame)" — no background, harmonics, or depth
    # exist in their hypotheses, and the contract says so instead of
    # fabricating premise metadata.
    "algebraic_frame_free": PremiseContract(
        frame=Frame.FRAME_FREE, perturbative_order=PerturbativeOrder.EXACT,
        background_class=BackgroundClass.NOT_APPLICABLE_ALGEBRAIC,
        units=UnitsConvention.PURE_NUMBER,
        harmonic_convention=HarmonicConvention.NOT_APPLICABLE,
        redshift_depth_convention=RedshiftDepthConvention.NOT_APPLICABLE,
    ),
}

# Every CHECKED signature binds to exactly one registered contract. The
# prose `frame` strings in THEOREM_SIGNATURES_V2 remain human-facing; this
# map is the machine binding the graph enforces.
CHECKED_SIGNATURE_BINDINGS = {
    "SIG-P3": "mes_linear_cmb",
    "SIG-MES-PROV": "mes_linear_cmb",
    "SIG-MES-BR": "mes_linear_cmb",
    "SIG-MES-REFREEZE": "mes_linear_cmb",
    "SIG-MES-MESB-TRACE": "mes_linear_cmb",
    "SIG-P11": "algebraic_frame_free",
    "SIG-P18": "algebraic_frame_free",
    "SIG-T1p": "algebraic_frame_free",
    "SIG-DL1": "algebraic_frame_free",
    "SIG-L-T2-EXIST": "algebraic_frame_free",
    "SIG-T2G": "algebraic_frame_free",
    "SIG-TSUM": "algebraic_frame_free",
}

# Convention distinctions that live in the signature HYPOTHESES rather than
# the frame contract are carried into the graph rows instead of erased.
BINDING_NOTES = {
    "SIG-MES-REFREEZE": (
        "carries the SAG observer-motion eps1-attribution convention in its "
        "hypotheses; eps-attribution is not a frame-contract field (typing "
        "it is later-PR work), so the distinction is preserved here as a "
        "note, not erased by sharing mes_linear_cmb"
    ),
    "SIG-P11": (
        "comparator W^2 slice-normal attribution is a REGISTERED "
        "INTERPRETIVE QUESTION (KE program); the binding is frame-free "
        "algebra, not an attribution ruling"
    ),
}

FORBIDDEN_OUTPUT_LANGUAGE = (
    "frame contract validates physics", "FLRW certified", "EGS certified",
    "Bianchi geometry detected", "Bianchi family identified",
    "finding rescued", "validated as native",
)
FRAME_CONTRACT_SOURCE = "htt/src/common/frame_contract.py"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _render(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
            + "\n").encode()


def _semantic_artifact(rel: str, payload: dict) -> dict:
    """Keep the frozen frame source digest as generation-time provenance."""

    normalized = json.loads(json.dumps(payload))
    if rel != OUTPUTS["manifest"]:
        return normalized
    rows = normalized.get("input_hashes")
    if not isinstance(rows, list):
        return normalized
    prefix = f"{FRAME_CONTRACT_SOURCE}:"
    for index, row in enumerate(rows):
        if not isinstance(row, str) or not row.startswith(prefix):
            continue
        digest = row.removeprefix(prefix)
        if len(digest) == 64 and all(char in "0123456789abcdef" for char in digest):
            rows[index] = f"{prefix}<generation-time-source>"
    return normalized


def _worktree_state() -> str:
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                          capture_output=True, text=True, check=True)
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=REPO,
                           capture_output=True, text=True, check=True)
    return head.stdout.strip() + ("; dirty" if dirty.stdout.strip() else "")


def build_registry(spec: dict) -> dict:
    legacy = legacy_reproduction_contract()
    return {
        "schema": "pr125.frame_contract_registry.v1",
        "contracts": {
            name: {"contract_id": contract.contract_id,
                   **contract.as_payload()}
            for name, contract in REGISTERED_CONTRACTS.items()
        },
        "legacy_reproduction_contract": {
            "contract_id": legacy.contract_id, **legacy.as_payload(),
            "channel": "labeled reproduction only — active producers must "
                       "construct explicit contracts",
        },
        "sign_registry": spec["frame_contract"]["sign_registry"],
        "explicit_fields_required": True,
    }


def build_graph(bindings: dict | None = None) -> dict:
    if bindings is None:
        bindings = CHECKED_SIGNATURE_BINDINGS
    registry = load_signature_registry(REPO)
    checked = [e.entry_id for e in registry.entries
               if e.signature_status.value == "CHECKED"]
    unbound = sorted(set(checked) - set(bindings))
    overbound = sorted(set(bindings) - set(checked))
    if unbound:
        raise FrameContractError(
            f"CHECKED signatures without a frame binding: {unbound}"
        )
    if overbound:
        raise FrameContractError(
            f"frame bindings for non-CHECKED signatures: {overbound}"
        )
    rows = {}
    for sig_id, contract_name in sorted(bindings.items()):
        contract = REGISTERED_CONTRACTS[contract_name]
        entry = registry.entry(sig_id)
        rows[sig_id] = {
            "contract_name": contract_name,
            "contract_id": contract.contract_id,
            "prose_frame": entry.frame,
            "prose_order": entry.perturbative_order,
            "convention_note": BINDING_NOTES.get(sig_id),
        }
    return {
        "schema": "pr125.theorem_frame_graph.v1",
        "rule": ("every CHECKED signature binds to exactly one registered "
                 "premise contract; MIGRATION_PENDING entries are excluded "
                 "until fully typed"),
        "checked_count": len(checked),
        "bindings": rows,
    }


def _pair_ok(boost: FrameBoost) -> bool:
    try:
        FrameBoost.validate_pair(boost, boost.inverse())
    except FrameContractError:
        return False
    return True


def build_witness_report() -> dict:
    b1, b2, b3 = Fraction(1, 3), Fraction(1, 5), Fraction(-1, 7)
    round_trip = compose_beta(compose_beta(b1, b2), -compose_beta(b1, b2))
    assoc_left = compose_beta(compose_beta(b1, b2), b3)
    assoc_right = compose_beta(b1, compose_beta(b2, b3))
    boost = FrameBoost(source=Frame.MATTER, target=Frame.CMB,
                       beta=Fraction(1234, 1000000))
    antisym = boost.inverse().beta == -boost.beta
    ident = boost.then(boost.inverse())

    sheared = KinematicState(beta=0, sigma2=Fraction(1, 10**8), w2=0,
                             delta_omega_k=0)
    flrw = KinematicState(beta=0, sigma2=0, w2=0, delta_omega_k=0)
    boosted = local_boost_limit(sheared, boost)
    tilted = KinematicState(beta=Fraction(1234, 1000000), sigma2=0, w2=0,
                            delta_omega_k=0)

    checks = {
        "round_trip_exact_zero": round_trip == 0,
        "associativity_exact": assoc_left == assoc_right,
        "antisymmetry_exact": antisym,
        "composed_identity_beta_zero": ident.beta == 0,
        "no_tilt_holds_with_shear": no_tilt_limit(sheared),
        "flrw_fails_with_shear": not flrw_limit(sheared),
        "flrw_holds_when_all_vanish": flrw_limit(flrw),
        # rest-in-declared-frame witness for the REGISTERED subtraction
        # semantics: value 0 in the source frame reads as -boost.beta in
        # the target frame (derived, not pinned by fiat)
        "local_boost_subtracts_tilt": boosted.beta == -boost.beta,
        "boost_pair_validator_accepts_true_inverse": _pair_ok(boost),
        "global_tilt_needs_homogeneous_class": (
            global_tilt_limit(
                tilted,
                PremiseContract(
                    frame=Frame.MATTER,
                    perturbative_order=PerturbativeOrder.LINEAR,
                    background_class=BackgroundClass.BIANCHI_V,
                    units=UnitsConvention.DIMENSIONLESS_HUBBLE_NORMALIZED,
                    harmonic_convention=(
                        HarmonicConvention.COMPLEX_SPHERICAL_CAMB),
                    redshift_depth_convention=(
                        RedshiftDepthConvention.CZ_KM_S),
                ))
            and not global_tilt_limit(
                tilted,
                REGISTERED_CONTRACTS["mes_linear_cmb"])
        ),
    }
    if not all(checks.values()):
        raise FrameContractError(f"kinematic witnesses failed: {checks}")
    return {
        "schema": "pr125.kinematic_witness_report.v1",
        "exactness": "all witnesses computed with exact Fractions",
        "checks": checks,
    }


def run_mutations(spec: dict) -> dict:
    rows = []

    def record(mutation_id: str, action) -> None:
        try:
            action()
        except FrameContractError as exc:
            rows.append({"mutation_id": mutation_id, "executed": True,
                         "killed": True, "kill_message": str(exc)[:160]})
            return
        rows.append({"mutation_id": mutation_id, "executed": True,
                     "killed": False, "kill_message": None})

    record("unknown_frame_rejected", lambda: PremiseContract(
        frame="HELIOCENTRIC_UNREGISTERED",
        perturbative_order=PerturbativeOrder.LINEAR,
        background_class=BackgroundClass.FLRW_FLAT,
        units=UnitsConvention.KM_S,
        harmonic_convention=HarmonicConvention.REAL_SPHERICAL,
        redshift_depth_convention=RedshiftDepthConvention.CZ_KM_S))
    record("defaulted_field_rejected", lambda: PremiseContract.from_payload(
        {"frame": "CMB", "perturbative_order": "LINEAR"}))

    def sign_flip() -> None:
        # KILLED BY THE REAL VALIDATOR: a same-sign A->B / B->A pair (the
        # sign-flip defect) must be rejected by FrameBoost.validate_pair.
        forward = FrameBoost(source=Frame.NORMAL, target=Frame.MATTER,
                             beta=Fraction(1, 100))
        mutant_backward = FrameBoost(source=Frame.MATTER,
                                     target=Frame.NORMAL,
                                     beta=Fraction(1, 100))
        FrameBoost.validate_pair(forward, mutant_backward)
    record("sign_flip_tilt_witness", sign_flip)

    record("beta_zero_egs_shortcut", lambda: require_flrw_limit(
        KinematicState(beta=0, sigma2=Fraction(1, 10**8), w2=0,
                       delta_omega_k=0)))

    def alias() -> None:
        wrong_boost = FrameBoost(source=Frame.ELECTRON, target=Frame.CMB,
                                 beta=Fraction(1, 1000))
        transform_tilt(Fraction(1, 100), wrong_boost,
                       declared_frame=Frame.MATTER,
                       requested_frame=Frame.NORMAL)
    record("alias_without_transform", alias)

    def unbound() -> None:
        # KILLED BY THE REAL VALIDATOR: build_graph itself must reject the
        # mutant binding map with SIG-P3 removed.
        bindings = dict(CHECKED_SIGNATURE_BINDINGS)
        bindings.pop("SIG-P3")
        build_graph(bindings=bindings)
    record("unbound_checked_signature", unbound)

    registered = [m["mutation_id"] for m in spec["mutation_registry"]]
    executed = [m["mutation_id"] for m in rows]
    if executed != registered:
        raise SystemExit(f"mutation set drifted: {registered} vs {executed}")
    survivors = [m for m in rows if not m["killed"]]
    return {
        "schema": "pr125.mutation_report.v1",
        "mutations": rows,
        "surviving_mutation_count": len(survivors),
    }


def _emit(rel: str, payload: dict, write: bool,
          problems: list[str], wrote: list[str]) -> None:
    target = REPO / rel
    if write:
        rendered = _render(payload)
        if target.is_file() and target.read_bytes() == rendered:
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_bytes(rendered)
        tmp.replace(target)
        wrote.append(rel)
        return
    if not target.is_file():
        problems.append(f"missing artifact: {rel}")
        return
    if rel == OUTPUTS["manifest"]:
        try:
            existing = json.loads(target.read_text(encoding="utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            problems.append(f"invalid artifact: {rel}")
            return
        if (
            isinstance(existing, dict)
            and _semantic_artifact(rel, existing) == _semantic_artifact(rel, payload)
        ):
            return
    if target.read_bytes() != _render(payload):
        problems.append(f"stale artifact: {rel}")


def build(write: bool) -> int:
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    if spec.get("schema") != "htt.long_horizon.pr125_frame_contract.v1":
        raise SystemExit("pr125 spec schema mismatch")
    problems: list[str] = []
    wrote: list[str] = []

    registry = build_registry(spec)
    graph = build_graph()
    witness = build_witness_report()
    mutations = run_mutations(spec)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["registry"], registry, write, problems, wrote)
    _emit(OUTPUTS["graph"], graph, write, problems, wrote)
    _emit(OUTPUTS["witness"], witness, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr125.artifact_manifest.v1",
        "owner": spec["owner"],
        "claim_tier": spec["claim_tier"],
        "claim_level": spec["claim_level"],
        "artifact_mode": spec["artifact_mode"],
        "allowed_use": spec["allowed_use"],
        "forbidden_use": list(spec["forbidden_output_language"]),
        "transfer_source": spec["transfer_source"],
        "config_hash": _sha(SPEC_PATH),
        "input_hashes": [
            f"{rel}:{_sha(REPO / rel)}"
            for rel in ("docs/research_program/THEOREM_SIGNATURES_V2.yaml",
                        "htt/src/common/frame_contract.py")
        ],
        "caveats": [
            "Convention contract correctness at roadmap_rescue_v1:C1 only.",
            "No physical statement is validated; all 102 findings stay OPEN.",
            "beta = 0 alone never satisfies the FLRW/EGS limit.",
        ],
        "artifacts": {
            rel: _sha(REPO / rel) if (REPO / rel).is_file() else None
            for key, rel in OUTPUTS.items() if key != "manifest"
        },
    }
    if write:
        # artifacts written above; recompute hashes now they exist
        manifest["artifacts"] = {
            rel: _sha(REPO / rel)
            for key, rel in OUTPUTS.items() if key != "manifest"
        }
    _emit(OUTPUTS["manifest"], manifest, write, problems, wrote)

    if problems:
        print(json.dumps({"ok": False, "problems": problems}))
        return 2
    for key, rel in OUTPUTS.items():
        payload = json.loads((REPO / rel).read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload.pop("forbidden_use", None)
        text = json.dumps(payload, ensure_ascii=False)
        for phrase in FORBIDDEN_OUTPUT_LANGUAGE:
            if phrase in text:
                print(json.dumps({"ok": False,
                                  "reason": f"forbidden phrase in {rel}"}))
                return 2
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "checked_signatures_bound": graph["checked_count"],
        "surviving_mutations": 0,
        "worktree": _worktree_state(),
    }, indent=2))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    sys.exit(build(write=args.write))


if __name__ == "__main__":
    main()
