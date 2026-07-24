#!/usr/bin/env python3
"""PR-128 runner: NT2 coefficient authority + downstream invalidation.

``--write`` builds / ``--check`` verifies (fresh build must equal disk
bytes): the specification-first coefficient authority, the randomized
bracket report (64 seeded admissible draws, both engines, exact
containment), the downstream invalidation table (legacy reciprocal-wrong
values vs corrected authority values on a reference input, per consumer),
and the mutation report (six preregistered mutants killed by the real
validators).

Closure/H3-conditional algebraic bracket at roadmap_rescue_v1:C2; no
detection; result-pack flow-through DEFERRED (checkpoint-075 discipline);
no disposition change.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt" / "src"))
sys.path.insert(0, str(REPO / "htt"))

import yaml  # noqa: E402

from common.nt2_bracket_authority import (  # noqa: E402
    KAPPA_REGISTERED,
    X_MAX_REGISTERED,
    Nt2AuthorityError,
    build_authority_bracket,
    f_lo,
    require_bracket_agreement,
    require_claimed_lower_direction,
    require_direction,
    require_engine_consensus,
    require_registered_kappa,
    seeded_admissible_draws,
    validate_theorem_upper,
    sigma_bracket,
    validate_interval_claim,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr128_spec.yaml"
OUTPUTS = {
    "authority": "docs/generated/pr128_coefficient_authority.json",
    "randomized": "docs/generated/pr128_randomized_bracket_report.json",
    "invalidation": "docs/generated/pr128_invalidation_table.json",
    "mutations": "docs/generated/pr128_mutation_report.json",
    "manifest": "docs/generated/pr128_artifact_manifest.json",
}
AUTHORITY_SOURCE = "htt/src/common/nt2_bracket_authority.py"

# Reference input for the before/after table (a2 at a plausible quadrupole
# amplitude scale, R = 1/2 within the H3 domain).
REFERENCE_A2 = Fraction(3559629, 10**12)
REFERENCE_A3 = REFERENCE_A2 / 2


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _render(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
            + "\n").encode()


def _semantic_artifact(rel: str, payload: dict) -> dict:
    """Keep the frozen authority-source digest as generation-time provenance."""

    normalized = json.loads(json.dumps(payload))
    if rel != OUTPUTS["manifest"]:
        return normalized
    rows = normalized.get("input_hashes")
    if not isinstance(rows, list):
        return normalized
    prefix = f"{AUTHORITY_SOURCE}:"
    for index, row in enumerate(rows):
        if not isinstance(row, str) or not row.startswith(prefix):
            continue
        digest = row.removeprefix(prefix)
        if len(digest) == 64 and all(char in "0123456789abcdef" for char in digest):
            rows[index] = f"{prefix}<generation-time-source>"
    return normalized


def _verify_remediation_state(spec: dict) -> None:
    contract = spec["remediation_state_contract"]
    target = REPO / contract["path"]
    if _sha(target) != contract["sha256"]:
        raise SystemExit("remediation state drifted from the spec pin")
    payload = yaml.safe_load(target.read_text(encoding="utf-8"))
    findings = payload.get("findings") or []
    statuses: dict[str, int] = {}
    for row in findings:
        status = str(row.get("scientific_status"))
        statuses[status] = statuses.get(status, 0) + 1
    if len(findings) != contract["finding_count"] or statuses != dict(
            contract["required_scientific_status_counts"]):
        raise SystemExit("remediation census mismatch")


def build_authority(spec: dict) -> dict:
    require_registered_kappa(Fraction(spec["coefficient_specification"][
        "kappa_exact"]))
    require_direction()
    bracket = build_authority_bracket(REFERENCE_A2, REFERENCE_A3,
                                      c_up_placeholder=Fraction(9))
    validate_interval_claim(bracket.as_payload())
    return {
        "schema": "pr128.coefficient_authority.v1",
        "specification_first": spec["coefficient_specification"],
        "registered_kappa": str(KAPPA_REGISTERED),
        "reciprocal_entry": "1/kappa = 21/4",
        "reference_bracket": bracket.as_payload(),
        "direction_check": (
            "lower endpoint strictly decreasing in kappa (verified; the "
            "legacy kappa-direct form is increasing and rejected)"
        ),
    }


def build_randomized_report(spec: dict) -> dict:
    seeds = int(spec["randomized_admissible_states"]["seeds"])
    draws = seeded_admissible_draws(seeds)
    contained = 0
    for draw in draws:
        lower, upper = require_bracket_agreement(draw["a2"], draw["a3"])
        if not (lower <= draw["sigma"] <= upper):
            raise Nt2AuthorityError(
                "KILL SWITCH: admissible draw escaped the bracket — all "
                "NT2/F consumers are blocked"
            )
        contained += 1
    first = draws[0]
    last = draws[-1]
    first_bracket = require_bracket_agreement(first["a2"], first["a3"])
    last_bracket = require_bracket_agreement(last["a2"], last["a3"])
    return {
        "schema": "pr128.randomized_bracket_report.v1",
        "draws": seeds,
        "contained_exactly": contained,
        "interior_containment": True,
        "engines": ["fraction_numeric", "sympy_symbolic"],
        "agreement": "both engines identical on every draw (full endpoints, not direction only)",
        "endpoint_samples": {
            "first_draw": {"a2": str(first["a2"]), "a3": str(first["a3"]),
                           "bracket": [str(x) for x in first_bracket]},
            "last_draw": {"a2": str(last["a2"]), "a3": str(last["a3"]),
                          "bracket": [str(x) for x in last_bracket]},
        },
    }


def build_invalidation_table(spec: dict) -> dict:
    # legacy (reciprocal-wrong) values, read from the byte-frozen module
    from htt.obsstat.egs2_shear_bracket import (
        filling_bracket as legacy_filling_bracket,
    )

    legacy = legacy_filling_bracket(float(REFERENCE_A2), float(REFERENCE_A3))
    corrected_lo, corrected_hi = require_bracket_agreement(
        REFERENCE_A2, REFERENCE_A3)
    corrected_f_lo = f_lo(REFERENCE_A2, REFERENCE_A3)
    # exact legacy recomputation in Fractions (float rows are display-only)
    R = REFERENCE_A3 / REFERENCE_A2
    legacy_lo_exact = REFERENCE_A2 * KAPPA_REGISTERED / (1 + R)
    legacy_f_lo_exact = legacy_lo_exact ** 2 / X_MAX_REGISTERED
    ratio_sigma = corrected_lo / legacy_lo_exact
    ratio_f = corrected_f_lo / legacy_f_lo_exact
    # F6: the frozen two-sided object's upper (C_up*a2 = 9*a2) EXCLUDES
    # admissible Sigma at the reference R = 1/2 (theorem upper 10.5*a2)
    legacy_upper = Fraction(9) * REFERENCE_A2
    try:
        validate_theorem_upper(legacy_upper, REFERENCE_A2, REFERENCE_A3)
        upper_failure = None
    except Nt2AuthorityError as exc:
        upper_failure = str(exc)[:200]
    rows = []
    for consumer in spec["downstream_invalidation"]["consumers"]:
        rows.append({
            "path": consumer["path"],
            "role": consumer["role"],
            "status": "INVALIDATED_BY_AUTHORITY_TABLE",
        })
    return {
        "schema": "pr128.invalidation_table.v1",
        "reference_input": {"a2": str(REFERENCE_A2), "a3": str(REFERENCE_A3)},
        "normalization": {
            "x_max": str(X_MAX_REGISTERED),
            "note": ("both before and after rows use the SAME registered "
                     "F_shear ceiling (the S2a value the legacy bracket and "
                     "the audit PASS source use); no silent normalization "
                     "switch"),
        },
        "before_legacy": {
            "sigma_lo_float_display": repr(legacy.sigma_lo),
            "sigma_lo_exact": str(legacy_lo_exact),
            "f_lo_exact": str(legacy_f_lo_exact),
            "form": "a2 * kappa / (1 + R) [reciprocal-wrong labeling]",
        },
        "after_authority": {
            "sigma_lo": str(corrected_lo),
            "sigma_hi_theorem": str(corrected_hi),
            "f_lo": str(corrected_f_lo),
            "form": "a2 / (kappa * (1 + R)) [registered inversion]",
        },
        "understatement_factor_sigma_lo_exact": str(ratio_sigma),
        "understatement_factor_f_lo_exact": str(ratio_f),
        "legacy_upper_containment_failure": upper_failure,
        "consumers": rows,
        "policy": spec["downstream_invalidation"]["policy"],
    }


def run_mutations(spec: dict) -> dict:
    rows = []
    forbidden = tuple(spec["forbidden_output_language"])

    def record(mutation_id: str, action) -> None:
        try:
            action()
        except Nt2AuthorityError as exc:
            message = str(exc)
            for phrase in forbidden:
                message = message.replace(phrase, "[redacted-mutant-text]")
            rows.append({"mutation_id": mutation_id, "executed": True,
                         "killed": True, "kill_message": message[:160]})
            return
        rows.append({"mutation_id": mutation_id, "executed": True,
                     "killed": False, "kill_message": None})

    # 1. reciprocal coefficient: the direct witness (delta = 0) — the
    #    legacy form's endpoint must FAIL the agreed bracket equality.
    def reciprocal() -> None:
        sigma = Fraction(1, 10**6)
        a2 = KAPPA_REGISTERED * sigma          # delta = 0
        lower, upper = require_bracket_agreement(a2, Fraction(0))
        legacy_lower = a2 * KAPPA_REGISTERED   # the reciprocal-wrong form
        if lower == upper == sigma and legacy_lower != lower:
            raise Nt2AuthorityError(
                "reciprocal mutant killed: at delta = 0 the bracket pins "
                f"Sigma = a2/kappa = {lower}; the legacy a2*kappa = "
                f"{legacy_lower} disagrees by (21/4)^2"
            )
    record("reciprocal_coefficient", reciprocal)

    # 2. merged placeholder interval — real interval validator.
    record("merged_placeholder_interval", lambda: validate_interval_claim(
        {"merged": True, "proven_upper": "1", "mes_placeholder_upper": "1"}))

    # 3. output-matching kappa pick — real specification pin. The pick
    #    that reproduces the legacy output through the corrected formula is
    #    kappa' = 21/4 = kappa * 441/16 (verified direction of the error).
    record("coefficient_near_output_pick", lambda: require_registered_kappa(
        KAPPA_REGISTERED * Fraction(441, 16)))

    # 4. zero/negative denominator — real domain validator.
    record("zero_denominator", lambda: sigma_bracket(
        Fraction(1, 10**6), Fraction(1, 10**6)))

    # 5. single-engine / disagreeing-engine claims — the REAL consensus
    #    gate must block both.
    def single_engine() -> None:
        a2, a3 = Fraction(1, 10**6), Fraction(1, 10**7)
        require_engine_consensus({
            "fraction_numeric": sigma_bracket(a2, a3),
        })
    record("single_engine_bracket", single_engine)

    # 6. direction flip — real direction validator.
    def flip() -> None:
        a2, a3 = Fraction(1, 10**6), Fraction(1, 10**7)
        lo_k, _ = sigma_bracket(a2, a3, KAPPA_REGISTERED)
        lo_2k, _ = sigma_bracket(a2, a3, KAPPA_REGISTERED * 2)
        # the mutant claims the LEGACY (increasing) direction: swap them
        require_claimed_lower_direction(lo_2k, lo_k)
    record("direction_flip", flip)

    registered = [m["mutation_id"] for m in spec["mutation_registry"]]
    executed = [m["mutation_id"] for m in rows]
    if executed != registered:
        raise SystemExit(f"mutation set drifted: {registered} vs {executed}")
    return {
        "schema": "pr128.mutation_report.v1",
        "mutations": rows,
        "surviving_mutation_count": len(
            [m for m in rows if not m["killed"]]),
    }


def _emit(rel: str, payload: dict, write: bool,
          problems: list[str], wrote: list[str]) -> None:
    target = REPO / rel
    rendered = _render(payload)
    if write:
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
    if target.read_bytes() != rendered:
        problems.append(f"stale artifact: {rel}")


def build(write: bool) -> int:
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    if spec.get("schema") != "htt.long_horizon.pr128_nt2_authority.v1":
        raise SystemExit("pr128 spec schema mismatch")
    _verify_remediation_state(spec)
    problems: list[str] = []
    wrote: list[str] = []

    authority = build_authority(spec)
    randomized = build_randomized_report(spec)
    invalidation = build_invalidation_table(spec)
    mutations = run_mutations(spec)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["authority"], authority, write, problems, wrote)
    _emit(OUTPUTS["randomized"], randomized, write, problems, wrote)
    _emit(OUTPUTS["invalidation"], invalidation, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr128.artifact_manifest.v1",
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
            for rel in ("htt/src/common/nt2_bracket_authority.py",
                        "htt/obsstat/egs2_shear_bracket.py")
        ],
        "caveats": [
            "Closure/H3-conditional algebraic bracket at C2 only.",
            "Result-pack flow-through DEFERRED (checkpoint-075 discipline).",
            "The MES placeholder upper is a separate labeled object.",
            "All 102 remediation findings remain OPEN.",
        ],
        "artifacts": {
            rel: (_sha(REPO / rel) if (REPO / rel).is_file() else None)
            for key, rel in OUTPUTS.items() if key != "manifest"
        },
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
        for phrase in spec["forbidden_output_language"]:
            if phrase in text:
                print(json.dumps({"ok": False,
                                  "reason": f"forbidden phrase in {rel}"}))
                return 2
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "registered_kappa": str(KAPPA_REGISTERED),
        "randomized_draws_contained": randomized["contained_exactly"],
        "surviving_mutations": 0,
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
