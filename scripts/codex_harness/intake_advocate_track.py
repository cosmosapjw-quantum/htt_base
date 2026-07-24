#!/usr/bin/env python3
"""Materialize PR-167..PR-183 through the PR-167-owned intake transaction.

This is intentionally separate from ``intake_long_horizon_roadmap.py``.  The
older intake keeps ownership of PR-119..PR-166 and its prohibition on adding
the advocate suffix is hash-pinned here.  A pre-intake semantic receipt seals
every existing card and its orchestration state before this writer adds the
new suffix.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

import yaml

try:  # Script execution places this directory directly on sys.path.
    import intake_long_horizon_roadmap as legacy
    from pr167_intake_contract import (
        create_pre_intake_receipt,
        file_sha256,
        semantic_sha256,
        validate_pre_intake_receipt,
    )
except ModuleNotFoundError:  # Package import used by pytest.
    from scripts.codex_harness import intake_long_horizon_roadmap as legacy
    from scripts.codex_harness.pr167_intake_contract import (
        create_pre_intake_receipt,
        file_sha256,
        semantic_sha256,
        validate_pre_intake_receipt,
    )


REPO = Path(__file__).resolve().parents[2]
_HTT_SRC = REPO / "htt" / "src"
if str(_HTT_SRC) not in sys.path:
    sys.path.insert(0, str(_HTT_SRC))

from common.status_snapshot import validate_status_contract

ROADMAP = REPO / "docs/research_program/LONG_HORIZON_RESCUE_PR_ROADMAP_20260714.md"
SPEC = REPO / "docs/research_program/long_horizon_rescue/pr167_spec.yaml"
LEGACY_INTAKE = REPO / "scripts/codex_harness/intake_long_horizon_roadmap.py"
BACKLOG_YAML = REPO / "docs/codex_handoff/pr_backlog.yaml"
BACKLOG_JSON = REPO / "docs/codex_handoff/pr_backlog.json"
STATUS_YAML = REPO / "docs/codex_handoff/pr_status.yaml"
MACHINE_BACKLOG_YAML = REPO / "machine_readable/pr_backlog.yaml"
MACHINE_BACKLOG_JSON = REPO / "machine_readable/pr_backlog.json"
MACHINE_STATUS_YAML = REPO / "machine_readable/pr_status.yaml"
RECEIPT = REPO / "docs/generated/pr167_pre_intake_semantic_receipt.json"
CROSSWALK = REPO / "docs/generated/pr167_advocate_crosswalk.json"
MANIFEST = REPO / "docs/generated/pr167_artifact_manifest.json"
TRANSACTION_JOURNAL = (
    REPO / ".agent-harness/generated/pr167_intake_write_journal.json"
)

FIRST_ID = 167
LAST_ID = 183
CARD_RE = re.compile(r"^#### PR-(1(?:6[7-9]|7\d|8[0-3])) — (.+)$", re.MULTILINE)
THEORY_CARDS = {168, 169, 170, 171, 175, 182}
HYPOTHESIS_ONLY_ARTIFACT_CARDS = {171, 174, 175, 182, 183}
REGISTERED_NOT_SCHEDULED_CARDS = {174, 175, 182}
EXPLICIT_APPROVED_SEQUENCE_CARDS = {168, 169, 170, 171}
BACKGROUND_EXECUTION_CONTRACTS = {
    "PR-151": {
        "kind": "acquisition",
        "allowed_phase": "acquire",
        "partial_scientific_use": "forbidden",
    }
}
SAFE_CLAIM_IMPACT = {
    168: "Four-axis-conditional geodesic-frame degeneracy and code-integrity result; no observational claim.",
    169: "Constraint- and admissibility-conditional witness result, or algebraic_only if either gate fails.",
    170: "Externally attributed Buchert/two-patch conditional identity and witness; not a new theorem.",
    171: "Class-conditional ODE stability result; persistent tilt retires the no-go claim.",
    173: "Finite-ensemble resolution and MC-SE honesty infrastructure; unresolved at the current Monte Carlo budget is terminal.",
    176: "Conservative-dependence cross-channel falsifier; structurally distinct from monopole leakage, with non_informative terminal allowed.",
    177: "ACT-release-simulation-conditional modulation candidate or null on 40<L<763 using 400 release simulations; not raw-QE reproduction.",
    179: "Selection/systematics-conditional raw-catalogue directional statistic with matched null; not cosmological anisotropy.",
    180: "Planck compact/E2E-null boost-residual consistency result; no confirmation or detection claim.",
}


def _load_mapping(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.relative_to(REPO)} must contain a mapping")
    return payload


def _head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _baseline_file_text(commit: str, path: Path) -> str:
    relative = path.relative_to(REPO).as_posix()
    return subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _wave(pr_number: int) -> int:
    if pr_number == 167:
        return 22
    if 168 <= pr_number <= 171:
        return 23
    if 172 <= pr_number <= 175:
        return 24
    if 176 <= pr_number <= 179:
        return 25
    if 180 <= pr_number <= 181:
        return 26
    return 27


def _verification_level(pr_number: int) -> str:
    return "L1" if pr_number in {167, 168, 172, 173, 182} else "L2"


def _claim_tier(pr_number: int, lane: str, claim_level: Mapping[str, str]) -> str:
    if lane == "needs_native":
        return "blocked"
    if pr_number == 167:
        return "diagnostic_only"
    if lane == "hypothesis_only":
        return "exploratory"
    level = str(claim_level.get("level", "NOT_APPLICABLE"))
    if level in {"NOT_APPLICABLE", "C1"}:
        return "exploratory"
    return "conditional"


def _dependency_contracts(
    dependencies: list[str], contract: Mapping[str, Any]
) -> list[dict[str, str]]:
    overrides = contract.get("dependency_modes", {}) or {}
    if not isinstance(overrides, dict):
        raise ValueError("dependency_modes must be a mapping")
    unknown = sorted(set(overrides) - set(dependencies))
    if unknown:
        raise ValueError(f"dependency-mode overrides name non-dependencies: {unknown}")
    allowed_modes = {
        "requires_success",
        "requires_terminal_receipt",
        "requires_adjudicated_claim_set",
    }
    rows = []
    for dependency in dependencies:
        mode = str(overrides.get(dependency, "requires_success"))
        if mode not in allowed_modes:
            raise ValueError(f"invalid dependency mode for {dependency}: {mode}")
        rows.append({"upstream_id": dependency, "mode": mode})
    return rows


def _safe_semantic_overrides(card: dict[str, Any], pr_number: int, amendment: str) -> None:
    card["dod"].append(amendment)
    if pr_number in SAFE_CLAIM_IMPACT:
        card["claim_impact"] = SAFE_CLAIM_IMPACT[pr_number]
    if pr_number == 167:
        card["kill"] = (
            "Preserve every canonical PR-000--166 card (expected count 113). "
            "Refuse intake on any missing, extra, semantically changed, or logically "
            "migrated card outside the registered PR-151 foreground-to-background "
            "migration, or on any invalid advocate dependency/lane contract."
        )
    elif pr_number == 168:
        card["dod"] = [
            text.replace("dual-engine", "blind four-axis CAS") for text in card["dod"]
        ]
        card["kill"] = (
            "If the registered spectral-degeneracy identity does not reach "
            "CAS_4AXIS_PASS, B_accel and all production consumers remain unchanged."
        )
    elif pr_number == 169:
        card["kill"] = (
            "If any constraint or physical-admissibility gate fails, terminate as "
            "algebraic_only and do not promote a constructive witness."
        )
    elif pr_number == 170:
        card["dod"] = [
            text.replace("dual-engine SymPy+Wolfram", "blind four-axis CAS").replace(
                "dual-engine identity seal", "blind four-axis identity seal"
            )
            for text in card["dod"]
        ]
    elif pr_number == 171:
        card["dod"] = [
            re.sub(
                r"정량 suppression ceiling\(Pi_X/momentum-source < 10\^-6\.\.-7\)을 산출\.",
                "The suppression functional and falsifier are preregistered without fixing a conclusion value.",
                text,
            )
            for text in card["dod"]
        ]
        card["kill"] = (
            "A physically admissible persistent-tilt counterexample retires the no-go "
            "claim; a missing CAS axis yields CAS_BLOCKED."
        )
    elif pr_number == 173:
        card["dod"] = [
            "Every stochastic headline reports Monte Carlo uncertainty and finite-rank resolution 1/(N+1).",
            "The typed outputs are RESOLVED_WITHIN_REGISTERED_MC_CONTRACT or NUMERICALLY_UNRESOLVED_AT_CURRENT_MC_BUDGET; neither is a physical signal/noise or validation label.",
            amendment,
        ]
        card["kill"] = (
            "If a shipped headline overlaps its certified MC uncertainty or discrete "
            "rank resolution, label it numerically unresolved at the current Monte Carlo budget."
        )
    elif pr_number == 176:
        card["dod"] = [
            "Measure theta=div(v) as an estimand structurally distinct from the bulk-flow dipole and radial-monopole estimator without claiming immunity to shared leakage.",
            "Report channel-wise injections, conservative dependence bounds, frame/transfer declarations, and NON_INFORMATIVE when joint covariance is unavailable or invalid.",
            amendment,
        ]
        card["kill"] = (
            "Before PR-155 use only channel-wise falsifiers with a conservative dependence "
            "bound; if joint covariance remains unidentified or the channel is near-rigid "
            "translation, terminate as non_informative."
        )
    elif pr_number == 177:
        card["dod"] = [
            "Freeze the 40<L<763 released-kappa off-diagonal estimator before results and apply identical observed/release-simulation pipelines to exactly 400 public simulations.",
            "Report NO_RESOLVED_COUPLING_AT_CURRENT_MC_RESOLUTION, NUMERICALLY_UNRESOLVED_AT_CURRENT_MC_BUDGET, or ACT_RELEASE_SIMULATION_CONDITIONAL_MODULATION_CANDIDATE after the mask-leakage control.",
            amendment,
        ]
        card["kill"] = (
            "Block the candidate if support leaves 40<L<763, the observed and release-simulation "
            "pipelines differ, mask leakage reproduces the coupling, covariance/null metadata are "
            "incomplete, or the MC decision is unresolved; never call this raw-QE or sky detection."
        )
    elif pr_number == 174:
        card["targets"] = [
            "Internal SW-only anisotropic ray-integration mechanics with no likelihood, transfer registration, or production consumer."
        ]
        card["dod"] = [
            "Compare preregistered SW-only ray-integration mechanics with an independent analytic fixture under a no-likelihood firewall.",
            amendment,
        ]
        card["kill"] = (
            "An analytic mismatch blocks the mechanics without selecting which side is physically correct; "
            "any transfer registration, likelihood, or production consumer is a hard failure."
        )
    elif pr_number == 175:
        card["targets"] = [
            "Internal structure-constant invariant identities and external-anchor agreement; no atlas ranking or family classifier."
        ]
        card["dod"] = [
            "If separately authorized, preregister one four-axis CAS contract for the invariant identities and external-anchor comparison.",
            amendment,
        ]
        card["kill"] = (
            "Any CAS axis or external-anchor mismatch yields CAS_CONFLICT or CAS_FAIL; any atlas rank or family label is a hard failure."
        )
        card["anti_drift"] = [
            "Record result blinding plus independence and lineage receipts for all four registered CAS axes; prohibit tautological self-checks and majority vote."
        ]
    elif pr_number == 178:
        card["dod"] = [
            "Freeze redshift shells and a reconstruction-free estimator while retaining the authenticated PR-151 matched support for joint shell covariance and inferential ranks.",
            "Without terminal matched support, emit descriptive shell summaries only with no kinematic, clustering, anisotropy, or causal attribution.",
            amendment,
        ]
        card["kill"] = (
            "Return ABSTAIN if joint per-shell covariance is missing or invalid, and "
            "WINDOW_SELECTION_DOMINATED_DIAGNOSTIC if frozen controls reproduce direction evolution."
        )
    elif pr_number == 179:
        card["kill"] = (
            "If the matched selection/systematics null contains the directional statistic, "
            "report only a selection/systematics-conditional upper limit or null."
        )
    elif pr_number == 180:
        card["dod"] = [
            "Subtract the fixed analytic pure-boost template and evaluate the residual against the frozen Planck compact/E2E mask, null, covariance, and PR-173 MC-resolution contract.",
            "Do not claim restored independence; a separate preregistered cross-covariance or conditional-independence test is required for any independence statement.",
            amendment,
        ]
        card["kill"] = (
            "If the residual is within the PR-173-certified Planck compact/E2E null floor, "
            "report CONSISTENT_WITH_PURE_BOOST_WITHIN_THIS_PIPELINE, never confirmation; "
            "a resolved residual is only NOT_EXPLAINED_BY_THE_FIXED_BOOST_TEMPLATE_WITHIN_THIS_PIPELINE."
        )
    elif pr_number == 182:
        card["targets"] = [
            "Solver-free parity theorem and future native-atlas handedness reference vector; no present-data family adjudication."
        ]
        card["dod"] = [
            "If separately authorized, register a blind four-axis parity identity contract and a no-data-adjudication reference-signal schema.",
            amendment,
        ]
        card["kill"] = (
            "Any shipped-data family label, family rank, handedness conclusion, production/manuscript consumer, "
            "or pre-native data sign comparison immediately blocks the card."
        )
        card["claim_impact"] = (
            "Solver-free parity identity and future native-atlas reference vector only; no family adjudication."
        )
    elif pr_number == 183:
        card["targets"] = [
            "Native-dependent low-ell T/E coherence interface plus separately owned observer-side feature schema."
        ]
        card["dod"] = [
            "Before authenticated PR-159--161 receipts, produce only an interface schema and separately labeled observer-side feature extractor.",
            amendment,
        ]
        card["kill"] = (
            "Keep the card dormant if any native receipt, version, convention, or upstream gate is absent; "
            "reject AniCLASS, external, empirical-proxy, theory-g, and SW-only substitutes."
        )
        card["claim_impact"] = (
            "Native-dependent hypothesis-test interface only; no pre-native sign/ratio prediction or family inference."
        )


def _artifact_contract(pr_number: int) -> tuple[str, str]:
    artifact_mode = (
        "hypothesis_only"
        if pr_number in HYPOTHESIS_ONLY_ARTIFACT_CARDS
        else "standard_internal"
    )
    if pr_number in REGISTERED_NOT_SCHEDULED_CARDS:
        authorization = "REGISTERED_NOT_SCHEDULED"
    elif pr_number == 183:
        authorization = "NATIVE_BLOCKED"
    elif pr_number in EXPLICIT_APPROVED_SEQUENCE_CARDS:
        authorization = "EXPLICIT_APPROVED_SEQUENCE"
    else:
        authorization = "DAG_SCHEDULABLE"
    return artifact_mode, authorization


def parse_advocate_cards(
    roadmap_text: str, spec: Mapping[str, Any]
) -> list[dict[str, Any]]:
    matches = list(CARD_RE.finditer(roadmap_text))
    if len(matches) != LAST_ID - FIRST_ID + 1:
        raise ValueError(f"expected 17 advocate roadmap cards, found {len(matches)}")
    contracts = spec.get("card_contracts")
    amendments = spec.get("claim_amendments")
    title_overrides = spec.get("title_overrides", {}) or {}
    if (
        not isinstance(contracts, dict)
        or not isinstance(amendments, dict)
        or not isinstance(title_overrides, dict)
    ):
        raise ValueError("PR-167 SPEC lacks card_contracts or claim_amendments")
    cards: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        pr_number = int(match.group(1))
        expected = FIRST_ID + index
        if pr_number != expected:
            raise ValueError(f"expected PR-{expected:03d}, found PR-{pr_number:03d}")
        pr_id = f"PR-{pr_number:03d}"
        end = matches[index + 1].start() if index + 1 < len(matches) else roadmap_text.find("\n### Checkpoint", match.end())
        if end < 0:
            end = len(roadmap_text)
        block = roadmap_text[match.end() : end]
        fields = legacy._field_map(block)
        required = {
            "Owner / dependencies / cost",
            "실제로 할 것",
            "하지 말 것",
            "주의·anti-drift",
            "검증·산출물",
            "Exit / kill",
            "최대 claim",
        }
        missing = sorted(required - set(fields))
        if missing:
            raise ValueError(f"{pr_id} missing roadmap fields: {missing}")
        contract = contracts.get(pr_id)
        if not isinstance(contract, dict):
            raise ValueError(f"PR-167 SPEC lacks a typed contract for {pr_id}")
        dependencies = contract.get("depends")
        if not isinstance(dependencies, list) or not all(
            isinstance(dep, str) for dep in dependencies
        ):
            raise ValueError(f"{pr_id} typed dependencies are malformed")
        owner_line = fields["Owner / dependencies / cost"]
        owner = legacy._owner(owner_line)
        scopes = legacy._implementation_scopes(owner_line, owner)
        lane = str(contract.get("execution_lane"))
        activation = str(contract.get("activation_state"))
        if lane not in {"defensible", "hypothesis_only", "needs_native"}:
            raise ValueError(f"{pr_id} has invalid execution lane {lane!r}")
        if activation not in {"PENDING", "NEEDS_NATIVE"}:
            raise ValueError(f"{pr_id} has invalid activation state {activation!r}")
        claim_level = legacy._claim_level(pr_number, fields["최대 claim"])
        title = str(title_overrides.get(pr_id, match.group(2))).strip()
        if not title:
            raise ValueError(f"{pr_id} title is empty")
        test_slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:48]
        artifact_mode, execution_authorization = _artifact_contract(pr_number)
        card: dict[str, Any] = {
            "id": pr_id,
            "wave": _wave(pr_number),
            "title": title,
            "owner": owner,
            "contributors": legacy._contributors(owner_line, owner),
            "adjudicator_role": "independent_non_author_reviewer",
            "implementation_scopes": scopes,
            "depends": dependencies,
            "dependency_contracts": _dependency_contracts(dependencies, contract),
            "targets": [fields.get("Targets", f"Roadmap card {pr_id}: {title}")],
            "files": legacy._planned_files(pr_id, scopes),
            "tests": [
                "venv/bin/python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml --status docs/codex_handoff/pr_status.yaml --strict-rescue-slice",
                f"to-be-created:venv/bin/python -B -m pytest -p no:cacheprovider -q tests/pr_cards/test_{pr_id.lower().replace('-', '_')}_{test_slug}.py",
            ],
            "dod": [fields["실제로 할 것"], fields["검증·산출물"]],
            "kill": fields["Exit / kill"],
            "cost": legacy._cost(owner_line),
            "level": _verification_level(pr_number),
            "scope": "pre-solver" if activation == "PENDING" else "post-native",
            "risk": "high" if "high" in legacy._cost(owner_line) else "medium" if "medium" in legacy._cost(owner_line) else "low",
            "claim_tier_ceiling": _claim_tier(pr_number, lane, claim_level),
            "claim_level": claim_level,
            "claim_impact": fields["최대 claim"],
            "forbidden": [fields["하지 말 것"]],
            "anti_drift": [fields["주의·anti-drift"]],
            "roadmap_anchor": f"docs/research_program/LONG_HORIZON_RESCUE_PR_ROADMAP_20260714.md#pr-{pr_number}",
            "activation_state": activation,
            "execution_lane": lane,
            "scientific_artifact_mode": artifact_mode,
            "execution_authorization": execution_authorization,
            "public_use": False,
            "spec_first_required": True,
            "scientific_status_on_intake": "OPEN",
        }
        amendment = amendments.get(pr_id)
        if not isinstance(amendment, str) or not amendment.strip():
            if pr_number in SAFE_CLAIM_IMPACT:
                raise ValueError(f"{pr_id} required claim amendment is missing")
            amendment = "Card execution remains bounded by the PR-167 status and claim firewall."
        _safe_semantic_overrides(card, pr_number, amendment)
        if pr_number in THEORY_CARDS:
            card["cas_contract"] = {
                "schema": "htt.cas_contract.v2",
                "required_axes": [
                    "wolfram_xact",
                    "sympy_high_precision",
                    "sage_singular",
                    "lean_mathlib",
                ],
                "missing_axis_outcome": "CAS_BLOCKED",
                "result_blinding": "required_until_adjudication",
            }
        if pr_number == 183:
            card["external_dependency_contracts"] = [
                {
                    "upstream_id": "AUTHENTICATED_NATIVE_DELIVERY",
                    "mode": "requires_authenticated_external_receipt",
                    "scope": "native_low_ell_delivery",
                }
            ]
        for field in legacy.SEMANTIC_CLAIM_PROSE_FIELDS:
            card[field] = legacy._qualify_claim_level_prose(card[field])
        cards.append(card)
    return cards


def _wave_rows() -> list[dict[str, Any]]:
    return [
        {"wave": 22, "title": "Advocate intake and execution contract"},
        {"wave": 23, "title": "Advocate theory"},
        {"wave": 24, "title": "Advocate oracle and gates-off substrate"},
        {"wave": 25, "title": "Advocate data falsifiers"},
        {"wave": 26, "title": "Advocate statistics"},
        {"wave": 27, "title": "Advocate hypothesis-only and needs-native registry"},
    ]


def materialize_backlog(
    existing: Mapping[str, Any], cards: list[dict[str, Any]], spec: Mapping[str, Any]
) -> dict[str, Any]:
    payload = copy.deepcopy(dict(existing))
    old_cards = payload.get("prs")
    if not isinstance(old_cards, list):
        raise ValueError("backlog prs must be a list")
    ids = [card.get("id") for card in old_cards if isinstance(card, dict)]
    advocate_ids = [card["id"] for card in cards]
    present = [pr_id for pr_id in advocate_ids if pr_id in ids]
    if present:
        if present != advocate_ids or ids[-len(advocate_ids) :] != advocate_ids:
            raise ValueError("partial or non-contiguous advocate intake present")
        payload["prs"] = [*old_cards[: -len(advocate_ids)], *cards]
        return payload
    if len(old_cards) != 113:
        raise ValueError(f"advocate intake requires the preserved 113-card DAG, found {len(old_cards)}")
    payload["prs"] = [*old_cards, *cards]
    policy = payload.setdefault("policy", {})
    order = policy.get("topological_order")
    if not isinstance(order, list) or len(order) != 113:
        raise ValueError("pre-intake policy.topological_order must contain 113 ids")
    policy["topological_order"] = [*order, *advocate_ids]
    long_horizon = policy.get("long_horizon_intake")
    if not isinstance(long_horizon, dict) or long_horizon.get("advocate_slice") != "deferred_to_PR-167":
        raise ValueError("legacy intake has not delegated the advocate slice to PR-167")
    long_horizon["advocate_slice"] = "active_PR-167..PR-183"
    policy["advocate_intake"] = {
        "spec": str(SPEC.relative_to(REPO)),
        "active_slice": "PR-167..PR-183",
        "pre_intake_receipt": str(RECEIPT.relative_to(REPO)),
        "preserved_card_count": 113,
        "scientific_rescue_count_on_intake": 0,
        "ordinary_scheduler_lane": "defensible",
        "separate_nonautomatic_lane": "hypothesis_only",
        "native_dormant_lane": "needs_native",
    }
    waves = payload.get("waves")
    if not isinstance(waves, list) or [row.get("wave") for row in waves[-9:]] != list(range(13, 22)):
        raise ValueError("pre-intake wave 13..21 suffix is malformed")
    payload["waves"] = [*waves, *_wave_rows()]
    return payload


def materialize_status(
    existing: Mapping[str, Any], cards: list[dict[str, Any]]
) -> dict[str, Any]:
    status = copy.deepcopy(dict(existing))
    if status.get("in_progress") != "PR-151":
        raise ValueError("pre-intake foreground must be the live PR-151 acquisition")
    status["in_progress"] = "PR-167"
    status["background_in_progress"] = ["PR-151"]
    status["background_execution_contracts"] = copy.deepcopy(
        BACKGROUND_EXECUTION_CONTRACTS
    )
    pending = status.get("pending", []) or []
    dormant = status.get("dormant_external", []) or []
    if not isinstance(pending, list) or not isinstance(dormant, list):
        raise ValueError("pre-intake pending/dormant status is malformed")
    status["pending"] = [*pending, *[card["id"] for card in cards if 168 <= int(card["id"][-3:]) <= 182]]
    status["dormant_external"] = [*dormant, "PR-183"]
    status["execution_lane"] = {
        card["id"]: card["execution_lane"] for card in cards
    }
    return status


def _preserving_backlog_text(
    existing_text: str, payload: Mapping[str, Any], cards: list[dict[str, Any]]
) -> str:
    order_marker = "  - PR-166\n  checkpoint_every_completed_prs: 5\n"
    if existing_text.count(order_marker) != 1:
        raise ValueError("cannot locate the unique PR-166 policy-order boundary")
    order_rows = "".join(f"  - {card['id']}\n" for card in cards)
    text = existing_text.replace(
        order_marker,
        f"  - PR-166\n{order_rows}  checkpoint_every_completed_prs: 5\n",
    )
    legacy_marker = "    advocate_slice: deferred_to_PR-167\n"
    if text.count(legacy_marker) != 1:
        raise ValueError("cannot locate the unique legacy advocate delegation marker")
    text = text.replace(legacy_marker, "    advocate_slice: active_PR-167..PR-183\n")
    policy_rows = yaml.safe_dump(
        {"advocate_intake": payload["policy"]["advocate_intake"]},
        sort_keys=False,
        allow_unicode=True,
        width=100,
    )
    policy_rows = "".join(f"  {line}\n" for line in policy_rows.rstrip().splitlines())
    waves_marker = "waves:\n"
    if text.count(waves_marker) != 1:
        raise ValueError("cannot locate the unique waves marker")
    text = text.replace(waves_marker, policy_rows + waves_marker)
    prs_marker = "prs:\n"
    if text.count(prs_marker) != 1:
        raise ValueError("cannot locate the unique prs marker")
    wave_text = yaml.safe_dump(
        {"waves": _wave_rows()}, sort_keys=False, allow_unicode=True, width=100
    ).removeprefix("waves:\n")
    text = text.replace(prs_marker, wave_text + prs_marker)
    card_text = yaml.safe_dump(
        {"prs": cards}, sort_keys=False, allow_unicode=True, width=100
    ).removeprefix("prs:\n")
    text = text.rstrip() + "\n" + card_text
    if yaml.safe_load(text) != payload:
        raise ValueError("preserving advocate YAML differs from semantic payload")
    return text


def _refresh_advocate_backlog_text(
    existing_text: str, payload: Mapping[str, Any], cards: list[dict[str, Any]]
) -> str:
    """Replace only the already-materialized advocate suffix."""

    marker = "- id: PR-167\n"
    if existing_text.count(marker) != 1:
        raise ValueError("cannot locate unique PR-167 advocate suffix boundary")
    prefix, _ = existing_text.split(marker, 1)
    card_text = yaml.safe_dump(
        {"prs": cards}, sort_keys=False, allow_unicode=True, width=100
    ).removeprefix("prs:\n")
    text = prefix + card_text
    if yaml.safe_load(text) != payload:
        raise ValueError("refreshed advocate YAML differs from semantic payload")
    return text


def _preserving_status_text(
    existing_text: str, status: Mapping[str, Any], cards: list[dict[str, Any]]
) -> str:
    """Apply the PR-167 state migration without reflowing the long notes block."""

    pending_marker = "dormant_external:\n"
    if existing_text.count(pending_marker) != 1:
        raise ValueError("cannot locate unique dormant_external status boundary")
    advocate_pending = "".join(
        f"- {card['id']}\n"
        for card in cards
        if 168 <= int(card["id"][-3:]) <= 182
    )
    text = existing_text.replace(pending_marker, advocate_pending + pending_marker)
    dormant_marker = "- PR-166\nin_progress: PR-151\n"
    if text.count(dormant_marker) != 1:
        raise ValueError("cannot locate unique PR-166/PR-151 status boundary")
    lane_text = yaml.safe_dump(
        {"execution_lane": status["execution_lane"]},
        sort_keys=False,
        allow_unicode=True,
        width=100,
    )
    replacement = (
        "- PR-166\n"
        "- PR-183\n"
        "in_progress: PR-167\n"
        "background_in_progress:\n"
        "- PR-151\n"
        + yaml.safe_dump(
            {"background_execution_contracts": status["background_execution_contracts"]},
            sort_keys=False,
            allow_unicode=True,
            width=100,
        )
        + lane_text
    )
    text = text.replace(dormant_marker, replacement)
    if yaml.safe_load(text) != status:
        raise ValueError("preserving advocate status text differs from semantic payload")
    return text


def _refresh_status_lane_text(existing_text: str, status: Mapping[str, Any]) -> str:
    """Refresh the background contract and lane projection under PR-167 ownership."""

    start_marker = "background_in_progress:\n"
    end_marker = "execution_resolutions:\n"
    if existing_text.count(start_marker) != 1 or existing_text.count(end_marker) != 1:
        raise ValueError("cannot locate unique execution-lane status boundaries")
    prefix, remainder = existing_text.split(start_marker, 1)
    _, suffix = remainder.split(end_marker, 1)
    lane_text = yaml.safe_dump(
        {
            "background_in_progress": status["background_in_progress"],
            "background_execution_contracts": status[
                "background_execution_contracts"
            ],
            "execution_lane": status["execution_lane"],
        },
        sort_keys=False,
        allow_unicode=True,
        width=100,
    )
    text = prefix + lane_text + end_marker + suffix
    if yaml.safe_load(text) != status:
        raise ValueError("refreshed advocate status text differs from semantic payload")
    return text


def _json_text(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def _yaml_text(value: Any) -> str:
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True, width=100)


def _transaction_targets() -> set[Path]:
    return {
        RECEIPT,
        CROSSWALK,
        MANIFEST,
        BACKLOG_YAML,
        MACHINE_BACKLOG_YAML,
        BACKLOG_JSON,
        MACHINE_BACKLOG_JSON,
        STATUS_YAML,
        MACHINE_STATUS_YAML,
    }


def _path_hash(path: Path) -> str | None:
    return file_sha256(path) if path.is_file() else None


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_journal(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(temporary)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(_json_text(payload))
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp_path, 0o600)
        os.replace(temp_path, path)
        _fsync_directory(path.parent)
    finally:
        temp_path.unlink(missing_ok=True)


def _recover_interrupted_transaction(
    journal_path: Path, expected_targets: set[Path]
) -> str | None:
    """Finish or roll back a journaled write after an interrupted process."""

    if not journal_path.is_file():
        return None
    payload = json.loads(journal_path.read_text(encoding="utf-8"))
    if payload.get("schema") != "htt.pr167.write_journal.v1":
        raise ValueError("PR-167 transaction journal schema mismatch")
    entries = payload.get("entries")
    if not isinstance(entries, list) or not all(isinstance(row, dict) for row in entries):
        raise ValueError("PR-167 transaction journal entries are malformed")
    targets = {Path(str(row.get("target"))).resolve() for row in entries}
    expected = {path.resolve() for path in expected_targets}
    if targets != expected:
        raise ValueError("PR-167 transaction journal target set mismatch")
    for row in entries:
        target = Path(str(row["target"])).resolve()
        staged = Path(str(row.get("staged"))).resolve()
        if (
            staged.parent != target.parent
            or not staged.name.startswith(f".{target.name}.staged.")
        ):
            raise ValueError(f"unsafe PR-167 staged path for {target}")
        backup_raw = row.get("backup")
        if backup_raw:
            backup = Path(str(backup_raw)).resolve()
            if (
                backup.parent != target.parent
                or not backup.name.startswith(f".{target.name}.backup.")
            ):
                raise ValueError(f"unsafe PR-167 backup path for {target}")

    all_new = all(
        _path_hash(Path(str(row["target"]))) == row.get("new_sha256")
        for row in entries
    )
    if not all_new:
        for row in entries:
            target = Path(str(row["target"]))
            backup_raw = row.get("backup")
            if row.get("prior_exists"):
                backup = Path(str(backup_raw))
                if (
                    not backup.is_file()
                    or _path_hash(backup) != row.get("prior_sha256")
                ):
                    raise ValueError(
                        f"PR-167 rollback backup missing or corrupt for {target}"
                    )
                os.chmod(backup, int(row["prior_mode"]))
                os.replace(backup, target)
            else:
                target.unlink(missing_ok=True)
    for row in entries:
        for field in ("staged", "backup"):
            raw = row.get(field)
            if raw:
                Path(str(raw)).unlink(missing_ok=True)
    journal_path.unlink(missing_ok=True)
    for directory in {journal_path.parent, *{path.parent for path in targets}}:
        _fsync_directory(directory)
    return "rolled_forward" if all_new else "rolled_back"


def _atomic_write_many(
    files: Mapping[Path, str], *, journal_path: Path | None = None
) -> None:
    """Publish a mode-preserving, journaled, crash-recoverable generation."""

    if not files:
        return
    targets = {path.resolve() for path in files}
    if len(targets) != len(files):
        raise ValueError("PR-167 transaction targets must be unique")
    journal = journal_path or (next(iter(files)).parent / ".pr167_write_journal.json")
    _recover_interrupted_transaction(journal, set(files))
    entries: list[dict[str, Any]] = []
    journal_written = False
    try:
        for path, text_value in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            prior_exists = path.is_file()
            prior_mode = path.stat().st_mode & 0o777 if prior_exists else 0o644
            prior_hash = _path_hash(path)
            backup_path: Path | None = None
            if prior_exists:
                handle, backup_raw = tempfile.mkstemp(
                    prefix=f".{path.name}.backup.", dir=path.parent
                )
                backup_path = Path(backup_raw)
                with os.fdopen(handle, "wb") as stream:
                    stream.write(path.read_bytes())
                    stream.flush()
                    os.fsync(stream.fileno())
                os.chmod(backup_path, prior_mode)

            handle, staged_raw = tempfile.mkstemp(
                prefix=f".{path.name}.staged.", dir=path.parent
            )
            staged_path = Path(staged_raw)
            with os.fdopen(handle, "w", encoding="utf-8") as stream:
                stream.write(text_value)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(staged_path, prior_mode)
            entries.append(
                {
                    "target": str(path.resolve()),
                    "staged": str(staged_path.resolve()),
                    "backup": str(backup_path.resolve()) if backup_path else None,
                    "prior_exists": prior_exists,
                    "prior_sha256": prior_hash,
                    "prior_mode": prior_mode,
                    "new_sha256": _path_hash(staged_path),
                }
            )
        for directory in {Path(row["target"]).parent for row in entries}:
            _fsync_directory(directory)
        try:
            _write_journal(
                journal,
                {"schema": "htt.pr167.write_journal.v1", "entries": entries},
            )
        finally:
            journal_written = journal.is_file()
        for row in entries:
            os.replace(Path(row["staged"]), Path(row["target"]))
        for directory in {Path(row["target"]).parent for row in entries}:
            _fsync_directory(directory)
        if not all(
            _path_hash(Path(row["target"])) == row["new_sha256"]
            for row in entries
        ):
            raise OSError("PR-167 transaction post-write hash verification failed")
        _recover_interrupted_transaction(journal, set(files))
        journal_written = False
    except BaseException:
        if journal_written:
            try:
                _recover_interrupted_transaction(journal, set(files))
                journal_written = False
            except BaseException as recovery_exc:
                raise RuntimeError(
                    "PR-167 transaction failed and journal recovery was incomplete"
                ) from recovery_exc
        raise
    finally:
        if not journal_written:
            for row in entries:
                for field in ("staged", "backup"):
                    raw = row.get(field)
                    if raw:
                        Path(str(raw)).unlink(missing_ok=True)


def _crosswalk_payload(
    spec: Mapping[str, Any],
    cards: list[dict[str, Any]],
    receipt: Mapping[str, Any],
    *,
    receipt_file_sha256: str,
) -> dict[str, Any]:
    contract = spec.get("crosswalk_contract")
    if not isinstance(contract, dict):
        raise ValueError("PR-167 SPEC crosswalk_contract is malformed")
    extensions = contract.get("reclassified_extensions")
    if not isinstance(extensions, dict):
        raise ValueError("PR-167 SPEC reclassified_extensions is malformed")
    payload = {
        "schema": "htt.pr167.advocate_crosswalk.v1",
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "artifact_mode": "governance_crosswalk",
        "allowed_use": "internal advocate scheduling only",
        "public_use": False,
        "scientific_effect": "none",
        "transfer_source": "none",
        "sky_support_mask_status": "not_applicable_governance",
        "covariance_null_mock_status": "not_applicable_governance",
        "registered_cards": [
            {
                "id": card["id"],
                "depends": card["depends"],
                "execution_lane": card["execution_lane"],
                "activation_state": card["activation_state"],
                "scientific_artifact_mode": card["scientific_artifact_mode"],
                "execution_authorization": card["execution_authorization"],
            }
            for card in cards
        ],
        "reclassified_extensions": extensions,
        "reclassified_candidates_are_new_cards": False,
        "pre_intake_receipt_sha256": receipt["receipt_sha256"],
        "config_hash": semantic_sha256(contract),
        "input_hashes": [
            f"{SPEC.relative_to(REPO)}:{file_sha256(SPEC)}",
            f"{ROADMAP.relative_to(REPO)}:{file_sha256(ROADMAP)}",
            f"{RECEIPT.relative_to(REPO)}:{receipt_file_sha256}",
        ],
        "caveats": [
            "Registration and crosswalk consistency are not scientific rescue.",
            "Hypothesis-only and needs-native cards are excluded from the ordinary scheduler.",
        ],
        "generating_command": "python scripts/codex_harness/intake_advocate_track.py --write",
        "git_commit_or_worktree_state": f"{spec['baseline_commit']}; PR-167 worktree",
    }
    return payload


def _artifact_manifest_payload(
    spec: Mapping[str, Any],
    cards: list[dict[str, Any]],
    receipt: Mapping[str, Any],
    crosswalk: Mapping[str, Any],
    backlog_text: str,
    status_text: str,
    *,
    receipt_text: str,
    crosswalk_text: str,
) -> dict[str, Any]:
    return {
        "schema": "htt.pr167.artifact_manifest.v1",
        "pr_id": "PR-167",
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "artifact_mode": "governance_transaction_manifest",
        "allowed_use": "internal DAG orchestration and audit only",
        "public_use": False,
        "scientific_effect": "none",
        "transfer_source": "none",
        "sky_support_mask_status": "not_applicable_governance",
        "covariance_null_mock_status": "not_applicable_governance",
        "preserved_card_count": int(receipt["preserved_card_count"]),
        "registered_advocate_card_count": len(cards),
        "registered_advocate_ids": [card["id"] for card in cards],
        "status_transition": {
            "foreground": "PR-167",
            "background_in_progress": ["PR-151"],
            "permitted_existing_card_migration": receipt[
                "permitted_status_migrations"
            ],
        },
        "claim_state": {
            "research_remediation_open": 102,
            "research_remediation_rescued": 0,
            "cf4_p0_findings_open": 2,
        },
        "config_hash": semantic_sha256(
            {
                "card_contracts": spec["card_contracts"],
                "status_contract": spec["status_contract"],
                "artifact_mode_contracts": spec["artifact_mode_contracts"],
            }
        ),
        "input_hashes": [
            f"{SPEC.relative_to(REPO)}:{file_sha256(SPEC)}",
            f"{ROADMAP.relative_to(REPO)}:{file_sha256(ROADMAP)}",
            f"{LEGACY_INTAKE.relative_to(REPO)}:{file_sha256(LEGACY_INTAKE)}",
        ],
        "artifact_hashes": [
            f"{RECEIPT.relative_to(REPO)}:{hashlib.sha256(receipt_text.encode('utf-8')).hexdigest()}",
            f"{CROSSWALK.relative_to(REPO)}:{hashlib.sha256(crosswalk_text.encode('utf-8')).hexdigest()}",
            f"{BACKLOG_YAML.relative_to(REPO)}:{hashlib.sha256(backlog_text.encode('utf-8')).hexdigest()}",
            f"{STATUS_YAML.relative_to(REPO)}:{hashlib.sha256(status_text.encode('utf-8')).hexdigest()}",
        ],
        "verification_commands": [
            "python scripts/codex_harness/intake_advocate_track.py --check",
            "python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml --status docs/codex_handoff/pr_status.yaml --strict-rescue-slice",
            "python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --json",
        ],
        "caveats": [
            "Intake changes orchestration only and rescues no scientific finding.",
            "Hypothesis-only registration is not execution authorization or public-use permission.",
            "The native-dependent PR-183 card remains dormant until authenticated native receipts exist.",
            "Partial PR-151 mocks remain forbidden for calibrated scientific ranks.",
        ],
        "generating_command": "python scripts/codex_harness/intake_advocate_track.py --write",
        "git_commit_or_worktree_state": f"{spec['baseline_commit']}; PR-167 worktree",
    }


def _expected_manifest_from_disk(
    spec: Mapping[str, Any], cards: list[dict[str, Any]], receipt: Mapping[str, Any]
) -> dict[str, Any]:
    baseline_backlog_text = _baseline_file_text(
        str(spec["baseline_commit"]), BACKLOG_YAML
    )
    baseline_backlog = yaml.safe_load(baseline_backlog_text)
    baseline_status_text = _baseline_file_text(
        str(spec["baseline_commit"]), STATUS_YAML
    )
    baseline_status = yaml.safe_load(baseline_status_text)
    if not isinstance(baseline_backlog, dict) or not isinstance(
        baseline_status, dict
    ):
        raise ValueError("PR-167 baseline backlog/status is malformed")
    intake_backlog = materialize_backlog(baseline_backlog, cards, spec)
    intake_status = materialize_status(baseline_status, cards)
    intake_backlog_text = _preserving_backlog_text(
        baseline_backlog_text, intake_backlog, cards
    )
    intake_status_text = _preserving_status_text(
        baseline_status_text, intake_status, cards
    )
    receipt_text = RECEIPT.read_text(encoding="utf-8")
    crosswalk_text = CROSSWALK.read_text(encoding="utf-8")
    crosswalk = json.loads(crosswalk_text)
    return _artifact_manifest_payload(
        spec,
        cards,
        receipt,
        crosswalk,
        intake_backlog_text,
        intake_status_text,
        receipt_text=receipt_text,
        crosswalk_text=crosswalk_text,
    )


def _validate_sources(spec: Mapping[str, Any]) -> None:
    source = spec.get("source_contract")
    receipt = spec.get("pre_intake_receipt")
    if not isinstance(source, dict) or not isinstance(receipt, dict):
        raise ValueError("PR-167 SPEC source or receipt contract is malformed")
    if spec.get("spec_status") != "approved_for_implementation":
        raise ValueError("PR-167 SPEC is not approved for implementation")
    if file_sha256(ROADMAP) != source.get("roadmap_sha256"):
        raise ValueError("PR-167 roadmap hash drift")
    if file_sha256(LEGACY_INTAKE) != source.get("existing_intake_owner_sha256"):
        raise ValueError("legacy intake owner drift; its advocate prohibition may have been weakened")


def check_materialized(spec: Mapping[str, Any], cards: list[dict[str, Any]]) -> None:
    if TRANSACTION_JOURNAL.exists():
        raise ValueError(
            "PR-167 intake has an interrupted write journal; rerun --write to recover"
        )
    if not RECEIPT.is_file():
        raise ValueError("PR-167 semantic receipt is missing")
    if not CROSSWALK.is_file():
        raise ValueError("PR-167 advocate crosswalk is missing")
    if not MANIFEST.is_file():
        raise ValueError("PR-167 artifact manifest is missing")
    backlog = _load_mapping(BACKLOG_YAML)
    status = _load_mapping(STATUS_YAML)
    backlog_cards = backlog.get("prs")
    if not isinstance(backlog_cards, list):
        raise ValueError("canonical advocate backlog cards are malformed")
    validate_status_contract(cards=backlog_cards, status=status)
    if BACKLOG_YAML.read_text(encoding="utf-8") != MACHINE_BACKLOG_YAML.read_text(encoding="utf-8"):
        raise ValueError("advocate YAML backlog mirrors differ")
    if STATUS_YAML.read_text(encoding="utf-8") != MACHINE_STATUS_YAML.read_text(encoding="utf-8"):
        raise ValueError("advocate YAML status mirrors differ")
    docs_json = json.loads(BACKLOG_JSON.read_text(encoding="utf-8"))
    machine_json = json.loads(MACHINE_BACKLOG_JSON.read_text(encoding="utf-8"))
    if docs_json != backlog or machine_json != backlog:
        raise ValueError("advocate JSON backlog mirrors differ from canonical YAML")
    actual_by_id = {
        card.get("id"): card
        for card in backlog_cards
        if isinstance(card, dict)
    }
    expected_ids = [card["id"] for card in cards]
    if any(pr_id not in actual_by_id for pr_id in expected_ids):
        raise ValueError("PR-167..PR-183 cards are missing from the current DAG")
    for expected_card in cards:
        current_card = actual_by_id[expected_card["id"]]
        for field in (
            "execution_lane",
            "activation_state",
            "scientific_artifact_mode",
            "execution_authorization",
            "public_use",
        ):
            if current_card.get(field) != expected_card.get(field):
                raise ValueError(
                    f"{expected_card['id']} intake invariant drifted: {field}"
                )
        if not set(expected_card["depends"]).issubset(
            set(current_card.get("depends", []))
        ):
            raise ValueError(
                f"{expected_card['id']} lost a registered intake dependency"
            )
    receipt_payload = json.loads(RECEIPT.read_text(encoding="utf-8"))
    receipt_spec = spec["pre_intake_receipt"]
    validate_pre_intake_receipt(
        receipt_payload,
        backlog=backlog,
        status=status,
        expected_baseline_commit=str(spec["baseline_commit"]),
        expected_backlog_sha256=str(receipt_spec["expected_pre_intake_backlog_sha256"]),
        expected_status_sha256=str(receipt_spec["expected_pre_intake_status_sha256"]),
        expected_roadmap_sha256=file_sha256(ROADMAP),
    )
    expected_crosswalk = _crosswalk_payload(
        spec,
        cards,
        receipt_payload,
        receipt_file_sha256=file_sha256(RECEIPT),
    )
    actual_crosswalk = json.loads(CROSSWALK.read_text(encoding="utf-8"))
    if actual_crosswalk != expected_crosswalk:
        raise ValueError("PR-167 advocate crosswalk drift")
    actual_manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    artifact_rows = actual_manifest.get("artifact_hashes")
    if not isinstance(artifact_rows, list) or len(artifact_rows) != 4:
        raise ValueError("PR-167 artifact manifest hash rows are malformed")
    artifact_hashes: dict[str, str] = {}
    for row in artifact_rows:
        if not isinstance(row, str) or ":" not in row:
            raise ValueError("PR-167 artifact manifest hash row is malformed")
        path, digest = row.rsplit(":", 1)
        if len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            raise ValueError("PR-167 artifact manifest digest is malformed")
        artifact_hashes[path] = digest
    expected_artifact_paths = {
        RECEIPT.relative_to(REPO).as_posix(),
        CROSSWALK.relative_to(REPO).as_posix(),
        BACKLOG_YAML.relative_to(REPO).as_posix(),
        STATUS_YAML.relative_to(REPO).as_posix(),
    }
    if set(artifact_hashes) != expected_artifact_paths:
        raise ValueError("PR-167 artifact manifest hash path set drift")
    for path in (RECEIPT, CROSSWALK):
        relative = path.relative_to(REPO).as_posix()
        if artifact_hashes[relative] != file_sha256(path):
            raise ValueError(f"PR-167 durable artifact hash drift: {relative}")
    expected_manifest = _expected_manifest_from_disk(spec, cards, receipt_payload)
    expected_manifest["artifact_hashes"] = artifact_rows
    if actual_manifest != expected_manifest:
        raise ValueError("PR-167 artifact manifest drift")


def _prevalidate_refresh_state(
    spec: Mapping[str, Any], backlog: Mapping[str, Any], status: Mapping[str, Any]
) -> dict[str, Any]:
    """Validate the current generation before any refresh write is staged."""

    if not RECEIPT.is_file():
        raise ValueError("PR-167 semantic receipt is missing before refresh")
    if BACKLOG_YAML.read_bytes() != MACHINE_BACKLOG_YAML.read_bytes():
        raise ValueError("refusing refresh from divergent YAML backlog mirrors")
    if STATUS_YAML.read_bytes() != MACHINE_STATUS_YAML.read_bytes():
        raise ValueError("refusing refresh from divergent YAML status mirrors")
    if json.loads(BACKLOG_JSON.read_text(encoding="utf-8")) != backlog:
        raise ValueError("refusing refresh from divergent docs JSON backlog mirror")
    if json.loads(MACHINE_BACKLOG_JSON.read_text(encoding="utf-8")) != backlog:
        raise ValueError("refusing refresh from divergent machine JSON backlog mirror")
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    receipt_spec = spec["pre_intake_receipt"]
    validate_pre_intake_receipt(
        receipt,
        backlog=backlog,
        status=status,
        expected_baseline_commit=str(spec["baseline_commit"]),
        expected_backlog_sha256=str(
            receipt_spec["expected_pre_intake_backlog_sha256"]
        ),
        expected_status_sha256=str(receipt_spec["expected_pre_intake_status_sha256"]),
        expected_roadmap_sha256=file_sha256(ROADMAP),
    )
    current_cards = backlog.get("prs")
    if not isinstance(current_cards, list):
        raise ValueError("current advocate backlog cards are malformed")
    current_suffix = current_cards[-(LAST_ID - FIRST_ID + 1) :]
    expected_ids = [f"PR-{number:03d}" for number in range(FIRST_ID, LAST_ID + 1)]
    if [card.get("id") for card in current_suffix if isinstance(card, dict)] != expected_ids:
        raise ValueError("refusing refresh from partial/non-contiguous advocate suffix")
    card_lanes = {
        str(card["id"]): card["execution_lane"]
        for card in current_suffix
        if isinstance(card, dict) and "execution_lane" in card
    }
    if status.get("execution_lane") != card_lanes:
        raise ValueError("refusing refresh from internally inconsistent lane projection")
    if status.get("background_in_progress") != ["PR-151"]:
        raise ValueError("refusing refresh from unexpected background execution state")
    if status.get("background_execution_contracts") != BACKGROUND_EXECUTION_CONTRACTS:
        raise ValueError("refusing refresh from a drifted background acquisition contract")
    validate_status_contract(cards=current_cards, status=status)
    return receipt


def _validate_computed_generation(
    spec: Mapping[str, Any],
    cards: list[dict[str, Any]],
    backlog: Mapping[str, Any],
    status: Mapping[str, Any],
    receipt: Mapping[str, Any],
    backlog_text: str,
    status_text: str,
) -> None:
    receipt_spec = spec["pre_intake_receipt"]
    validate_pre_intake_receipt(
        receipt,
        backlog=backlog,
        status=status,
        expected_baseline_commit=str(spec["baseline_commit"]),
        expected_backlog_sha256=str(
            receipt_spec["expected_pre_intake_backlog_sha256"]
        ),
        expected_status_sha256=str(receipt_spec["expected_pre_intake_status_sha256"]),
        expected_roadmap_sha256=file_sha256(ROADMAP),
    )
    if yaml.safe_load(backlog_text) != backlog or yaml.safe_load(status_text) != status:
        raise ValueError("computed transaction text differs from its semantic payload")
    if status.get("background_execution_contracts") != BACKGROUND_EXECUTION_CONTRACTS:
        raise ValueError("computed PR-151 background contract drift")
    if status.get("execution_lane") != {
        card["id"]: card["execution_lane"] for card in cards
    }:
        raise ValueError("computed advocate execution-lane projection drift")
    all_cards = backlog.get("prs")
    if not isinstance(all_cards, list):
        raise ValueError("computed advocate backlog cards are malformed")
    validate_status_contract(cards=all_cards, status=status)


def write_transaction(spec: Mapping[str, Any], cards: list[dict[str, Any]]) -> None:
    _recover_interrupted_transaction(TRANSACTION_JOURNAL, _transaction_targets())
    backlog = _load_mapping(BACKLOG_YAML)
    current_ids = [card.get("id") for card in backlog.get("prs", []) if isinstance(card, dict)]
    advocate_ids = [card["id"] for card in cards]
    if any(pr_id in current_ids for pr_id in advocate_ids):
        current_status = _load_mapping(STATUS_YAML)
        if (
            current_status.get("in_progress") == "PR-167"
            and "PR-167" not in set(current_status.get("completed", []) or [])
        ):
            old_receipt = _prevalidate_refresh_state(spec, backlog, current_status)
            refreshed_backlog = materialize_backlog(backlog, cards, spec)
            refreshed_status = copy.deepcopy(current_status)
            refreshed_status["background_execution_contracts"] = copy.deepcopy(
                BACKGROUND_EXECUTION_CONTRACTS
            )
            refreshed_status["execution_lane"] = {
                card["id"]: card["execution_lane"] for card in cards
            }
            backlog_text = _refresh_advocate_backlog_text(
                BACKLOG_YAML.read_text(encoding="utf-8"), refreshed_backlog, cards
            )
            status_text = _refresh_status_lane_text(
                STATUS_YAML.read_text(encoding="utf-8"), refreshed_status
            )
            baseline_backlog = yaml.safe_load(
                _baseline_file_text(str(spec["baseline_commit"]), BACKLOG_YAML)
            )
            baseline_status = yaml.safe_load(
                _baseline_file_text(str(spec["baseline_commit"]), STATUS_YAML)
            )
            if not isinstance(baseline_backlog, dict) or not isinstance(
                baseline_status, dict
            ):
                raise ValueError("PR-167 baseline backlog/status is malformed")
            receipt_spec = spec["pre_intake_receipt"]
            receipt_payload = create_pre_intake_receipt(
                backlog=baseline_backlog,
                status=baseline_status,
                baseline_commit=str(spec["baseline_commit"]),
                backlog_sha256=str(
                    receipt_spec["expected_pre_intake_backlog_sha256"]
                ),
                status_sha256=str(receipt_spec["expected_pre_intake_status_sha256"]),
                roadmap_sha256=file_sha256(ROADMAP),
                generated_at_utc=str(old_receipt.get("generated_at_utc") or ""),
            )
            receipt_text = _json_text(receipt_payload)
            receipt_file_hash = hashlib.sha256(
                receipt_text.encode("utf-8")
            ).hexdigest()
            crosswalk_payload = _crosswalk_payload(
                spec,
                cards,
                receipt_payload,
                receipt_file_sha256=receipt_file_hash,
            )
            crosswalk_text = _json_text(crosswalk_payload)
            manifest_payload = _artifact_manifest_payload(
                spec,
                cards,
                receipt_payload,
                crosswalk_payload,
                backlog_text,
                status_text,
                receipt_text=receipt_text,
                crosswalk_text=crosswalk_text,
            )
            _validate_computed_generation(
                spec,
                cards,
                refreshed_backlog,
                refreshed_status,
                receipt_payload,
                backlog_text,
                status_text,
            )
            _atomic_write_many(
                {
                    RECEIPT: receipt_text,
                    CROSSWALK: crosswalk_text,
                    MANIFEST: _json_text(manifest_payload),
                    BACKLOG_YAML: backlog_text,
                    MACHINE_BACKLOG_YAML: backlog_text,
                    BACKLOG_JSON: _json_text(refreshed_backlog),
                    MACHINE_BACKLOG_JSON: _json_text(refreshed_backlog),
                    STATUS_YAML: status_text,
                    MACHINE_STATUS_YAML: status_text,
                },
                journal_path=TRANSACTION_JOURNAL,
            )
        check_materialized(spec, cards)
        return
    receipt_spec = spec["pre_intake_receipt"]
    backlog_hash = file_sha256(BACKLOG_YAML)
    status_hash = file_sha256(STATUS_YAML)
    if backlog_hash != receipt_spec.get("expected_pre_intake_backlog_sha256"):
        raise ValueError("pre-intake canonical backlog hash does not match the approved PR-167 SPEC")
    if status_hash != receipt_spec.get("expected_pre_intake_status_sha256"):
        raise ValueError("pre-intake canonical status hash does not match the approved PR-167 SPEC")
    if _head() != spec.get("baseline_commit"):
        raise ValueError("PR-167 intake baseline commit mismatch")
    status = _load_mapping(STATUS_YAML)
    receipt = create_pre_intake_receipt(
        backlog=backlog,
        status=status,
        baseline_commit=str(spec["baseline_commit"]),
        backlog_sha256=backlog_hash,
        status_sha256=status_hash,
        roadmap_sha256=file_sha256(ROADMAP),
    )
    new_backlog = materialize_backlog(backlog, cards, spec)
    new_status = materialize_status(status, cards)
    backlog_text = _preserving_backlog_text(
        BACKLOG_YAML.read_text(encoding="utf-8"), new_backlog, cards
    )
    status_text = _preserving_status_text(
        STATUS_YAML.read_text(encoding="utf-8"), new_status, cards
    )
    receipt_text = _json_text(receipt)
    receipt_file_hash = hashlib.sha256(receipt_text.encode("utf-8")).hexdigest()
    crosswalk_payload = _crosswalk_payload(
        spec,
        cards,
        receipt,
        receipt_file_sha256=receipt_file_hash,
    )
    crosswalk_text = _json_text(crosswalk_payload)
    manifest_text = _json_text(
        _artifact_manifest_payload(
            spec,
            cards,
            receipt,
            crosswalk_payload,
            backlog_text,
            status_text,
            receipt_text=receipt_text,
            crosswalk_text=crosswalk_text,
        )
    )
    _validate_computed_generation(
        spec,
        cards,
        new_backlog,
        new_status,
        receipt,
        backlog_text,
        status_text,
    )
    _atomic_write_many(
        {
            RECEIPT: receipt_text,
            CROSSWALK: crosswalk_text,
            MANIFEST: manifest_text,
            BACKLOG_YAML: backlog_text,
            MACHINE_BACKLOG_YAML: backlog_text,
            BACKLOG_JSON: _json_text(new_backlog),
            MACHINE_BACKLOG_JSON: _json_text(new_backlog),
            STATUS_YAML: status_text,
            MACHINE_STATUS_YAML: status_text,
        },
        journal_path=TRANSACTION_JOURNAL,
    )
    check_materialized(spec, cards)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        spec = _load_mapping(SPEC)
        _validate_sources(spec)
        cards = parse_advocate_cards(ROADMAP.read_text(encoding="utf-8"), spec)
        if args.write:
            write_transaction(spec, cards)
        else:
            check_materialized(spec, cards)
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(
        f"OK: PR-{FIRST_ID}..PR-{LAST_ID} advocate intake "
        f"{'written' if args.write else 'verified'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
