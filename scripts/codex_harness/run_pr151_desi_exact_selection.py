#!/usr/bin/env python3
"""PR-151 runner: freeze the official DESI DR1 mock-conditioned result.

``--write`` materializes and ``--check`` byte-compares the result pack built
from ``docs/generated/desi_official_mock_card.json``.  The heavy card is
created only after the authenticated acquisition manifest contains all 1000
EZmock FFA realizations, all 25 AbacusSummit FFA validation realizations, and
the preregistered 15-pair random-catalogue replication audit.

The official mocks calibrate a concrete finite-rank measurement.  They do not
identify which physical or observational component caused the measured
dipole, and they carry no geometry or Bianchi-family interpretation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
for root in (REPO, REPO / "htt", REPO / "htt" / "src"):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from obsstat.desi_exact_selection_mock import (  # noqa: E402
    DESIExactSelectionError,
    SCHEMA_VERSION,
    generate_official_caption,
    lint_caption,
    refuse_attribution_without_official_mocks,
    refuse_bianchi_from_desi,
    refuse_desi_detection,
    refuse_fixed_alpha,
    refuse_generic_grf_attribution,
    refuse_hard_coded_cap_ratio,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr151_spec.yaml"
CARD_PATH = REPO / "docs/generated/desi_official_mock_card.json"
OUTPUTS = {
    "manifest_mock": "docs/generated/pr151_mock_manifest.json",
    "refit": "docs/generated/pr151_per_mock_refit.json",
    "covariance": "docs/generated/pr151_two_tier_covariance.json",
    "confusion": "docs/generated/pr151_component_confusion.json",
    "null": "docs/generated/pr151_survey_conditional_null.json",
    "captions": "docs/generated/pr151_captions.json",
    "mutations": "docs/generated/pr151_mutation_report.json",
    "manifest": "docs/generated/pr151_artifact_manifest.json",
}
REDACTED = "[REDACTED-PATTERN]"


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _render(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False,
                       sort_keys=True) + "\n").encode()


def _finite_number(value: object) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(float(value)))


def _validate_finite_rank(rank: dict, observed: float,
                          values: list[float], label: str) -> None:
    if (not _finite_number(observed) or not isinstance(values, list)
            or not values or not all(_finite_number(value) for value in values)):
        raise SystemExit(f"{label} finite-rank inputs are invalid")
    n = len(values)
    upper = sum(float(value) >= float(observed) for value in values)
    lower = sum(float(value) <= float(observed) for value in values)
    ties = sum(float(value) == float(observed) for value in values)
    p_upper = (1 + upper) / (n + 1)
    p_lower = (1 + lower) / (n + 1)
    p_two = min(1.0, 2.0 * min(p_upper, p_lower))
    strict_rank = 1 + sum(float(value) < float(observed) for value in values)
    expected = {
        "n_mock": n,
        "observed": float(observed),
        "upper_exceedance_count": upper,
        "lower_exceedance_count": lower,
        "tie_count": ties,
        "observation_inclusive_strict_rank": strict_rank,
        "right_tail_p": p_upper,
        "left_tail_p": p_lower,
        "central_two_sided_p": p_two,
        "support_resolution": 1.0 / (n + 1),
    }
    for key, value in expected.items():
        actual = rank.get(key)
        if isinstance(value, float):
            if (not _finite_number(actual)
                    or not math.isclose(float(actual), value, rel_tol=1e-12,
                                        abs_tol=1e-15)):
                raise SystemExit(f"{label} finite-rank arithmetic mismatch at {key}")
        elif actual != value:
            raise SystemExit(f"{label} finite-rank arithmetic mismatch at {key}")
    k = int(math.floor(0.025 * (n + 1)))
    interval = rank.get("central_95pct_finite_predictive_interval")
    if k < 1:
        if interval is not None:
            raise SystemExit(f"{label} finite predictive interval should be null")
    else:
        ordered = sorted(float(value) for value in values)
        expected_interval = {
            "lower_order_1_based": k,
            "upper_order_1_based": n - k + 1,
            "lower": ordered[k - 1],
            "upper": ordered[n - k],
            "finite_predictive_coverage": 1.0 - 2.0 * k / (n + 1),
        }
        if not isinstance(interval, dict):
            raise SystemExit(f"{label} finite predictive interval missing")
        for key, value in expected_interval.items():
            actual = interval.get(key)
            if isinstance(value, float):
                if (not _finite_number(actual)
                        or not math.isclose(float(actual), value, rel_tol=1e-12,
                                            abs_tol=1e-15)):
                    raise SystemExit(
                        f"{label} finite predictive interval mismatch at {key}")
            elif actual != value:
                raise SystemExit(
                    f"{label} finite predictive interval mismatch at {key}")


def _verify_baseline_commit(spec: dict) -> None:
    sha = str(spec.get("baseline_commit") or "")
    if len(sha) != 40:
        raise SystemExit("baseline_commit must be a full 40-hex id")
    probe = subprocess.run(
        ["git", "cat-file", "-e", f"{sha}^{{commit}}"], cwd=REPO,
        capture_output=True, check=False,
    )
    if probe.returncode != 0:
        raise SystemExit(f"baseline_commit {sha} does not resolve")


def _verify_remediation_state(spec: dict) -> None:
    contract = spec["remediation_state_contract"]
    target = REPO / contract["path"]
    if _sha(target) != contract["sha256"]:
        raise SystemExit("remediation state drifted from the spec pin")
    payload = yaml.safe_load(target.read_text(encoding="utf-8"))
    findings = payload.get("findings") or []
    statuses: dict[str, int] = {}
    for row in findings:
        key = str(row.get("scientific_status"))
        statuses[key] = statuses.get(key, 0) + 1
    required = {
        str(key): int(value)
        for key, value in contract["required_scientific_status_counts"].items()
    }
    if len(findings) != int(contract["finding_count"]) or statuses != required:
        raise SystemExit(
            f"remediation state drifted: count={len(findings)} statuses={statuses}"
        )


def _load_inputs(spec: dict) -> tuple[dict, dict, str]:
    if not CARD_PATH.is_file():
        raise SystemExit(
            "official DESI mock card absent; finish the authenticated acquisition "
            "and run scripts/desi_official_mock_card.py"
        )
    card = json.loads(CARD_PATH.read_text(encoding="utf-8"))
    if card.get("schema") != "htt.desi_official_mock_card.v2":
        raise SystemExit(f"DESI card schema is {card.get('schema')!r}, expected v2")
    if card.get("status") != "OFFICIAL_MOCK_CONDITIONAL_RESULT":
        raise SystemExit(f"DESI card status is {card.get('status')!r}")

    acquisition_path = Path(card["provenance"]["acquisition_manifest"])
    if not acquisition_path.is_file():
        raise SystemExit(f"acquisition manifest absent: {acquisition_path}")
    acquisition_sha = _sha(acquisition_path)
    if acquisition_sha != card["provenance"]["acquisition_manifest_sha256"]:
        raise SystemExit("DESI acquisition manifest changed after card generation")
    acquisition = json.loads(acquisition_path.read_text(encoding="utf-8"))
    expected_counts = {
        "ezmock": int(spec["data_scope"]["expected_ezmock_count"]),
        "abacus": int(spec["data_scope"]["expected_abacus_count"]),
    }
    if acquisition.get("status") != "complete":
        raise SystemExit("DESI acquisition is not complete")
    if acquisition.get("authenticated_counts") != expected_counts:
        raise SystemExit(
            f"DESI authenticated counts drifted: {acquisition.get('authenticated_counts')}"
        )
    completion = acquisition.get("completion_gates") or {}
    required_completion = {
        "expected_mock_counts", "observed_authenticated",
        "registered_random_replication_complete", "final_full_data_rehash",
    }
    if (set(completion) != required_completion
            or any(completion.get(key) is not True
                   for key in required_completion)
            or acquisition.get("final_full_data_rehash") is not True):
        raise SystemExit("DESI acquisition completion gates are not all green")
    if acquisition.get("aggregate_input_hash") != card["provenance"]["aggregate_input_hash"]:
        raise SystemExit("aggregate DESI input hash differs between acquisition and card")
    observed = acquisition.get("observed") or {}
    if observed.get("status") != "authenticated":
        raise SystemExit("authenticated observed DESI record is required")
    return card, acquisition, acquisition_sha


def _validate_card(spec: dict, card: dict, acquisition: dict) -> None:
    scope = spec["data_scope"]
    ez_expected = int(scope["expected_ezmock_count"])
    ab_expected = int(scope["expected_abacus_count"])
    ez = card["ezmock"]
    ab = card["abacus_validation"]
    observed = card.get("observed") or {}
    observed_amplitude = observed.get("dipole_amplitude")
    direction = observed.get("direction") or {}
    if (not _finite_number(observed_amplitude)
            or float(observed_amplitude) < 0
            or not _finite_number(direction.get("amplitude"))
            or not math.isclose(float(observed_amplitude),
                                float(direction["amplitude"]),
                                rel_tol=1e-12, abs_tol=1e-15)):
        raise SystemExit("observed DESI dipole amplitude/direction is invalid")
    if (len(ez["realizations"]) != ez_expected or
            int(ez["rank"]["n_mock"]) != ez_expected):
        raise SystemExit("official EZmock result does not contain exactly 1000 rows")
    if (len(ab["realizations"]) != ab_expected or
            int(ab["rank"]["n_mock"]) != ab_expected):
        raise SystemExit("Abacus validation does not contain exactly 25 rows")
    if ab.get("pooled_with_ezmock") is not False:
        raise SystemExit("EZmock and Abacus ensembles must never be pooled")
    if [row["realization"] for row in ez["realizations"]] != list(range(1, 1001)):
        raise SystemExit("EZmock realization inventory is not exactly 1..1000")
    if [row["realization"] for row in ab["realizations"]] != list(range(25)):
        raise SystemExit("Abacus realization inventory is not exactly 0..24")
    _validate_finite_rank(
        ez["rank"], float(observed_amplitude),
        [row.get("dipole_amplitude") for row in ez["realizations"]],
        "EZmock")
    _validate_finite_rank(
        ab["rank"], float(observed_amplitude),
        [row.get("dipole_amplitude") for row in ab["realizations"]],
        "Abacus")
    for family, rows in (("ezmock", ez["realizations"]),
                         ("abacus", ab["realizations"])):
        for row in rows:
            vector = row.get("dipole")
            amplitude = row.get("dipole_amplitude")
            if (not isinstance(vector, list) or len(vector) != 3
                    or not all(_finite_number(value) for value in vector)
                    or not _finite_number(amplitude)
                    or float(amplitude) < 0
                    or not math.isclose(
                        math.sqrt(sum(float(value) ** 2 for value in vector)),
                        float(amplitude), rel_tol=1e-12, abs_tol=1e-15)):
                raise SystemExit(
                    f"{family} {row.get('realization')} dipole vector/amplitude mismatch")
            if (not _finite_number(row.get("cleaned_dipole_amplitude"))
                    or not _finite_number(row.get("beta_hat"))
                    or set((row.get("alpha_hat_per_cap") or {})) != {"NGC", "SGC"}
                    or not all(_finite_number(value) and float(value) > 0
                               for value in row["alpha_hat_per_cap"].values())):
                raise SystemExit(
                    f"{family} {row.get('realization')} refit fields are invalid")
            window = row.get("random_window") or {}
            if int(window.get("random_index", -1)) != 0:
                raise SystemExit(
                    f"{family} {row.get('realization')} lacks its primary random-0 window"
                )
            source_hashes = window.get("source_sha256", {})
            if len(source_hashes) != 2 or any(
                    len(str(digest)) != 64 or
                    any(char not in "0123456789abcdef" for char in str(digest).lower())
                    for digest in source_hashes.values()):
                raise SystemExit("each primary mock window must bind two source hashes")

    frozen = {
        ("ezmock", int(value))
        for value in scope["random_replication_registry"]["ezmock_realizations"]
    } | {
        ("abacus", int(value))
        for value in scope["random_replication_registry"]["abacus_realizations"]
    }
    audit = card["random_replication_sensitivity"]
    rows = audit.get("rows") or []
    actual = {(row["family"], int(row["realization"])) for row in rows}
    if int(audit.get("n_audited", -1)) != len(frozen) or actual != frozen:
        raise SystemExit(f"random replication registry mismatch: {actual} != {frozen}")
    if any(row.get("random_indices") != [0, 1] for row in rows):
        raise SystemExit("random replication rows must compare indices 0 and 1")
    if audit.get("families") != {"ezmock": 10, "abacus": 5}:
        raise SystemExit("random replication family counts mismatch")
    for row in rows:
        p0 = row.get("amplitude_r0")
        p1 = row.get("amplitude_r1")
        absolute = row.get("absolute_amplitude_difference")
        relative = row.get("relative_amplitude_difference")
        angle = row.get("dipole_direction_difference_deg")
        if (not all(_finite_number(value) for value in
                    (p0, p1, absolute, relative, angle))
                or float(p0) <= 0 or float(p1) < 0
                or not math.isclose(float(absolute),
                                    abs(float(p1) - float(p0)),
                                    rel_tol=1e-12, abs_tol=1e-15)
                or not math.isclose(float(relative),
                                    float(absolute) / float(p0),
                                    rel_tol=1e-12, abs_tol=1e-15)
                or not 0 <= float(angle) <= 180):
            raise SystemExit("random replication sensitivity row is invalid")
    if len(acquisition.get("records", [])) != ez_expected + ab_expected:
        raise SystemExit("acquisition record inventory is incomplete")

    config = card["config"]
    estimator = spec["estimator"]
    expected_config = {
        "nside": int(estimator["nside"]),
        "z_min_inclusive": float(estimator["z_min_inclusive"]),
        "z_max_inclusive": float(estimator["z_max_inclusive"]),
        "weight_column": estimator["required_weight_column"],
        "sample": estimator["sample"],
    }
    for key, value in expected_config.items():
        if config.get(key) != value:
            raise SystemExit(f"DESI estimator config drift at {key}: {config.get(key)!r}")
    config_digest = hashlib.sha256(json.dumps(
        config, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if card.get("config_hash") != f"sha256:{config_digest}":
        raise SystemExit("DESI card config hash mismatch")
    provenance = card.get("provenance") or {}
    environment = provenance.get("generation_environment") or {}
    if not all(environment.get(key) for key in
               ("python", "numpy", "git_commit", "worktree_state")):
        raise SystemExit("DESI card generation environment is incomplete")


def _base_metadata(spec: dict, card_sha: str, acquisition_sha: str) -> dict:
    return {
        "owner": spec["owner"],
        "implementation_scope": list(spec["implementation_scope"]),
        "claim_tier": spec["claim_tier"],
        "claim_level": spec["claim_level"],
        "transfer_source": spec["transfer_source"],
        "config_hash": f"sha256:{_sha(SPEC_PATH)}",
        "input_hashes": [
            {"path": str(CARD_PATH.relative_to(REPO)),
             "sha256": f"sha256:{card_sha}"},
            {"path": "authenticated_DESI_acquisition_manifest",
             "sha256": f"sha256:{acquisition_sha}"},
        ],
        "sky_support_status": (
            "observed DR1 window plus an authenticated mock-specific random-0 "
            "NGC/SGC NSIDE64 window for every official mock"
        ),
        "mask_status": (
            "selection support is defined by the observed and mock-specific "
            "authenticated random windows; no substitute binary mask"
        ),
        "covariance_status": (
            "empirical finite-rank support from 1000 EZmocks with the 25 "
            "Abacus validation mocks reported separately"
        ),
        "null_mock_status": (
            "1000 EZmocks; 25 separate Abacus validation mocks; random-1 "
            "replication audit on a frozen 10-EZmock plus 5-Abacus subset"
        ),
        "caveats": [
            "conditional on the official FFA mock fidelity and frozen estimator",
            "a finite-rank consistency result does not identify a causal component",
            "no geometry, family-identification, or native-solver claim",
            "all 102 remediation findings remain OPEN",
        ],
        "generating_command": (
            "venv/bin/python -B scripts/codex_harness/"
            "run_pr151_desi_exact_selection.py --write"
        ),
        "git_worktree_state": "code and input hashes recorded; generated before PR commit",
    }


def _result_label(rank: dict) -> str:
    return ("finite-rank tension at the registered 0.05 two-sided threshold"
            if float(rank["central_two_sided_p"]) < 0.05 else
            "finite-rank consistency at the registered 0.05 two-sided threshold")


def build_reports(spec: dict, card: dict, acquisition: dict,
                  acquisition_sha: str) -> tuple[dict, ...]:
    card_sha = _sha(CARD_PATH)
    meta = _base_metadata(spec, card_sha, acquisition_sha)
    counts = acquisition["authenticated_counts"]
    audit = card["random_replication_sensitivity"]
    manifest_mock = {
        "schema": "pr151.mock_manifest.v2", **meta,
        "official_mocks_abandoned": False,
        "availability_status": "public_obtainable_and_acquired",
        "acquisition_status": "complete",
        "authenticated_counts": counts,
        "expected_counts": {"ezmock": 1000, "abacus": 25},
        "primary_random_index": 0,
        "full_18_random_policy": (
            "not required for this frozen low-ell estimator; random-1 on 15 "
            "preregistered mocks measures single-random integration sensitivity"
        ),
        "causal_attribution_status": "not_identified_by_the_official_mock_null",
        "acquisition_manifest_sha256": acquisition_sha,
        "aggregate_input_hash": acquisition["aggregate_input_hash"],
    }
    refit = {
        "schema": "pr151.per_mock_refit.v2", **meta,
        "observed": card["observed"],
        "estimator_config": card["config"],
        "alpha_and_nuisance_refit_per_mock": True,
        "mock_specific_random_window_per_realization": True,
        "primary_statistic": "raw weighted number-count dipole amplitude",
        "realization_counts": counts,
    }
    covariance = {
        "schema": "pr151.separate_official_null_ensembles.v2", **meta,
        "ezmock_amplitude_summary": card["ezmock"]["amplitude_summary"],
        "abacus_validation_amplitude_summary":
            card["abacus_validation"]["amplitude_summary"],
        "ezmock_abacus_transport_check": card["ezmock_abacus_transport_check"],
        "ezmock_abacus_pooled": False,
        "note": (
            "the 1000-member EZmock ensemble defines primary finite-rank support; "
            "the 25-member Abacus ensemble is a separate validation tier"
        ),
    }
    confusion = {
        "schema": "pr151.component_identification_boundary.v2", **meta,
        "causal_attribution_identified": False,
        "components": ["clustering", "kinematic", "selection"],
        "reason": (
            "the official mock-conditioned amplitude null calibrates consistency "
            "but does not by itself decompose the observed vector among components"
        ),
        "official_mock_result_is_abandoned": False,
    }
    null = {
        "schema": "pr151.official_mock_conditional_null.v2", **meta,
        "observed_dipole_amplitude": card["observed"]["dipole_amplitude"],
        "observed_direction": card["observed"]["direction"],
        "ezmock_finite_rank": card["ezmock"]["rank"],
        "ezmock_result": _result_label(card["ezmock"]["rank"]),
        "abacus_validation_finite_rank": card["abacus_validation"]["rank"],
        "abacus_validation_result":
            _result_label(card["abacus_validation"]["rank"]),
        "random_replication_sensitivity": audit,
        "causal_attribution": "not_identified",
        "headline": (
            f"DESI DR1 BGS weighted dipole: EZmock two-sided finite-rank "
            f"p={card['ezmock']['rank']['central_two_sided_p']:.6f} "
            f"(N=1000); separate Abacus p="
            f"{card['abacus_validation']['rank']['central_two_sided_p']:.6f} "
            f"(N=25)"
        ),
    }
    caption = generate_official_caption(card)
    lint_caption(caption)
    captions = {
        "schema": "pr151.captions.v2", **meta,
        "captions": {"official_mock_result": caption},
    }
    return manifest_mock, refit, covariance, confusion, null, captions


def _redact(message: str, patterns: list[str]) -> str:
    for pattern in patterns:
        needle = pattern.lower()
        while needle in message.lower():
            start = message.lower().index(needle)
            message = message[:start] + REDACTED + message[start + len(pattern):]
    return message


def run_mutations(spec: dict, meta: dict) -> dict:
    patterns = [str(value) for value in spec["forbidden_output_language"]]
    executions = {
        "hard_coded_cap_ratio": lambda: refuse_hard_coded_cap_ratio("hard_coded"),
        "fixed_alpha_mock": lambda: refuse_fixed_alpha(False),
        "generic_grf_causal_attribution":
            lambda: refuse_generic_grf_attribution("clustering_dominated_causal"),
        "attribution_without_official_mocks":
            lambda: refuse_attribution_without_official_mocks(False, "causal_attribution"),
        "desi_dipole_detection":
            lambda: refuse_desi_detection("desi_dipole_detection"),
        "bianchi_family_from_desi":
            lambda: refuse_bianchi_from_desi("bianchi_family"),
    }
    registered = {row["mutation_id"]: row["kill_rule"]
                  for row in spec["mutation_registry"]}
    if set(registered) != set(executions):
        raise SystemExit("mutation registry does not match live executions")
    rows = []
    for mutation_id, execution in executions.items():
        killed = False
        message = "MUTANT SURVIVED"
        try:
            execution()
        except DESIExactSelectionError as exc:
            killed = True
            message = _redact(str(exc), patterns)[:220]
        rows.append({
            "mutation_id": mutation_id,
            "kill_rule": registered[mutation_id],
            "killed": killed,
            "kill_message_redacted": message,
        })
    return {
        "schema": "pr151.mutation_report.v2", **meta,
        "mutations": rows,
        "surviving_mutation_count": sum(not row["killed"] for row in rows),
    }


def _scan_payloads(spec: dict, payloads: dict[str, dict]) -> None:
    forbidden = [str(value).lower() for value in spec["forbidden_output_language"]]
    for name, payload in payloads.items():
        scan = dict(payload)
        scan.pop("forbidden_use", None)
        raw = json.dumps(scan, ensure_ascii=False).lower()
        hits = [phrase for phrase in forbidden if phrase in raw]
        if hits:
            raise SystemExit(f"forbidden claim phrase in {name}: {hits}")


def _emit(rel: str, payload: dict, write: bool,
          problems: list[str], wrote: list[str]) -> None:
    target = REPO / rel
    rendered = _render(payload)
    if write:
        if target.is_file() and target.read_bytes() == rendered:
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_suffix(target.suffix + ".tmp")
        temp.write_bytes(rendered)
        temp.replace(target)
        wrote.append(rel)
        return
    if not target.is_file():
        problems.append(f"missing artifact: {rel}")
    elif target.read_bytes() != rendered:
        problems.append(f"stale artifact: {rel}")


def build(write: bool) -> int:
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    if spec.get("schema") != "htt.long_horizon.pr151_desi_official_mocks.v2":
        raise SystemExit("PR-151 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    card, acquisition, acquisition_sha = _load_inputs(spec)
    _validate_card(spec, card, acquisition)

    (manifest_mock, refit, covariance, confusion, null,
     captions) = build_reports(spec, card, acquisition, acquisition_sha)
    meta = _base_metadata(spec, _sha(CARD_PATH), acquisition_sha)
    mutations = run_mutations(spec, meta)
    if mutations["surviving_mutation_count"]:
        raise SystemExit("one or more registered claim mutations survived")

    payloads = {
        "manifest_mock": manifest_mock, "refit": refit,
        "covariance": covariance, "confusion": confusion,
        "null": null, "captions": captions, "mutations": mutations,
    }
    _scan_payloads(spec, payloads)
    problems: list[str] = []
    wrote: list[str] = []
    for key, payload in payloads.items():
        _emit(OUTPUTS[key], payload, write, problems, wrote)

    manifest = {
        "schema": "pr151.artifact_manifest.v2", **meta,
        "artifact_mode": spec["artifact_mode"],
        "allowed_use": spec["allowed_use"],
        "forbidden_use": list(spec["forbidden_output_language"]),
        "claim_identity": spec["claim_identity"],
        "source_card": {
            "path": str(CARD_PATH.relative_to(REPO)),
            "sha256": _sha(CARD_PATH),
        },
        "acquisition": {
            "path": card["provenance"]["acquisition_manifest"],
            "sha256": acquisition_sha,
            "aggregate_input_hash": acquisition["aggregate_input_hash"],
            "authenticated_counts": acquisition["authenticated_counts"],
        },
        "artifacts": {
            OUTPUTS[key]: _sha(REPO / OUTPUTS[key])
            for key in payloads if (REPO / OUTPUTS[key]).is_file()
        },
    }
    _emit(OUTPUTS["manifest"], manifest, write, problems, wrote)
    if problems:
        print(json.dumps({"ok": False, "problems": problems}, indent=2))
        return 2

    rank = card["ezmock"]["rank"]
    print(json.dumps({
        "ok": True,
        "mode": "write" if write else "check",
        "wrote": wrote,
        "official_mocks_abandoned": False,
        "authenticated_counts": acquisition["authenticated_counts"],
        "ezmock_right_tail_p": rank["right_tail_p"],
        "ezmock_two_sided_p": rank["central_two_sided_p"],
        "random_replication_n": card["random_replication_sensitivity"]["n_audited"],
        "surviving_mutations": 0,
    }, indent=2))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    raise SystemExit(build(write=args.write))


if __name__ == "__main__":
    main()
