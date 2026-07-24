from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path

import pytest
import yaml


REPO = Path(__file__).resolve().parents[2]
HARNESS = REPO / "scripts/codex_harness"
if str(HARNESS) not in sys.path:
    sys.path.insert(0, str(HARNESS))

from validate_pr_dag import (  # noqa: E402
    validate_backlog,
    validate_long_horizon_rescue_slice,
)
from intake_long_horizon_roadmap import (  # noqa: E402
    _preserving_yaml_text,
    check_materialized,
    materialize_payload,
    parse_roadmap_cards,
)


BACKLOG_YAML = REPO / "docs/codex_handoff/pr_backlog.yaml"
BACKLOG_JSON = REPO / "docs/codex_handoff/pr_backlog.json"
MACHINE_BACKLOG_YAML = REPO / "machine_readable/pr_backlog.yaml"
MACHINE_BACKLOG_JSON = REPO / "machine_readable/pr_backlog.json"
STATUS = REPO / "docs/codex_handoff/pr_status.yaml"
MACHINE_STATUS = REPO / "machine_readable/pr_status.yaml"
REGISTRY = REPO / "docs/codex_handoff/authorized_principals.yaml"
MACHINE_REGISTRY = REPO / "machine_readable/authorized_principals.yaml"
ROADMAP = REPO / "docs/research_program/LONG_HORIZON_RESCUE_PR_ROADMAP_20260714.md"
CHECKPOINT_065 = REPO / "docs/generated/progress_checkpoints/checkpoint_065.md"
EXPECTED_LEGACY_SLICE_SHA256 = (
    "31caa40afe347857ffbe920a7a5837264dab11d9ecdc430fd6721ab990254899"
)
EXPECTED_CHECKPOINT_065_SHA256 = (
    "dbee93f333d5ca33bb67ac2fed7c2a13720112a2df4b7ffaec17734f3321b809"
)
BARE_ACTIVE_CLAIM_LEVEL_RE = re.compile(
    r"(?<![A-Za-z0-9_:])C([0-6])(?!-[A-Za-z0-9])\b"
)
SEMANTIC_CLAIM_FIELDS = (
    "title",
    "targets",
    "dod",
    "kill",
    "claim_impact",
    "forbidden",
    "anti_drift",
)


def _yaml(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _cards(payload: dict[str, object]) -> list[dict[str, object]]:
    cards = payload["prs"]
    assert isinstance(cards, list)
    assert all(isinstance(card, dict) for card in cards)
    return cards  # type: ignore[return-value]


def _card(payload: dict[str, object], pr_id: str) -> dict[str, object]:
    return next(card for card in _cards(payload) if card["id"] == pr_id)


def _pr119_intake_text() -> str:
    """Project the approved intake view without depending on owner-local git history."""

    cards = parse_roadmap_cards(ROADMAP.read_text(encoding="utf-8"))
    return _preserving_yaml_text(BACKLOG_YAML.read_text(encoding="utf-8"), cards)


def _pr119_intake_payload() -> dict[str, object]:
    payload = copy.deepcopy(_yaml(BACKLOG_YAML))
    cards = _cards(payload)
    first = next(index for index, card in enumerate(cards) if card["id"] == "PR-119")
    last = next(index for index, card in enumerate(cards) if card["id"] == "PR-166")
    payload["prs"] = cards[: last + 1]
    allowed = {card["id"] for card in _cards(payload)}
    payload["policy"]["topological_order"] = [
        pr_id
        for pr_id in payload["policy"]["topological_order"]
        if pr_id in allowed
    ]
    payload["policy"]["long_horizon_intake"]["advocate_slice"] = (
        "deferred_to_PR-167"
    )
    payload["policy"].pop("advocate_intake", None)
    payload["waves"] = [
        row for row in payload["waves"] if row.get("wave", 22) <= 21
    ]
    assert first == 65
    assert last == 112
    return payload


def _pr119_status(payload: dict[str, object]) -> dict[str, object]:
    """Project live orchestration state onto the PR-119 intake card set."""

    allowed = {card["id"] for card in _cards(payload)}
    status = copy.deepcopy(_yaml(STATUS))
    for field in (
        "completed",
        "blocked",
        "skipped",
        "pending",
        "dormant_external",
        "background_in_progress",
    ):
        status[field] = [pr_id for pr_id in status.get(field, []) if pr_id in allowed]
    if status.get("in_progress") not in allowed:
        status["in_progress"] = None
    for field in ("execution_lane", "execution_resolutions"):
        status[field] = {
            pr_id: value
            for pr_id, value in status.get(field, {}).items()
            if pr_id in allowed
        }
    if status["background_in_progress"] != ["PR-151"]:
        status["background_execution_contracts"] = {}
    return status


def _strings(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)


def test_pr119_intake_is_exact_atomic_and_preserves_frozen_legacy_slice() -> None:
    backlog = _pr119_intake_payload()
    info = validate_backlog(backlog)
    status = _pr119_status(backlog)

    validate_long_horizon_rescue_slice(backlog, info, status=status)

    ids = [card["id"] for card in _cards(backlog)]
    assert len(ids) == 113
    assert ids[65:] == [f"PR-{number:03d}" for number in range(119, 167)]
    assert not set(ids) & {f"PR-{number:03d}" for number in range(167, 184)}
    assert _canonical_sha256(_cards(backlog)[:65]) == EXPECTED_LEGACY_SLICE_SHA256
    assert hashlib.sha256(CHECKPOINT_065.read_bytes()).hexdigest() == (
        EXPECTED_CHECKPOINT_065_SHA256
    )


def test_intake_rewrite_is_deterministic_idempotent_and_preserves_frozen_prefix() -> None:
    original_text = _pr119_intake_text()
    cards = parse_roadmap_cards(ROADMAP.read_text(encoding="utf-8"))
    payload_once = materialize_payload(copy.deepcopy(_pr119_intake_payload()), cards)
    rendered_once = _preserving_yaml_text(original_text, cards)
    assert yaml.safe_load(rendered_once) == payload_once

    payload_twice = materialize_payload(copy.deepcopy(payload_once), cards)
    rendered_twice = _preserving_yaml_text(rendered_once, cards)
    assert payload_twice == payload_once
    assert rendered_twice == rendered_once

    marker = "\n- id: PR-119\n"
    original_prefix = original_text[: original_text.index(marker) + 1]
    rewritten_prefix = rendered_once[: rendered_once.index(marker) + 1]
    assert rewritten_prefix == original_prefix


def test_intake_rewrite_repairs_policy_and_rescue_wave_metadata_drift() -> None:
    canonical = _pr119_intake_payload()
    cards = parse_roadmap_cards(ROADMAP.read_text(encoding="utf-8"))
    drifted = copy.deepcopy(canonical)
    drifted["policy"]["long_horizon_intake"][
        "scientific_rescue_count_on_intake"
    ] = 999
    drifted["waves"][-1]["title"] = "drifted wave 21"

    repaired = materialize_payload(drifted, cards)

    assert repaired["policy"]["long_horizon_intake"] == canonical["policy"][
        "long_horizon_intake"
    ]
    assert repaired["waves"] == canonical["waves"]

    canonical_text = _pr119_intake_text()
    drifted_text = canonical_text.replace(
        "scientific_rescue_count_on_intake: 0",
        "scientific_rescue_count_on_intake: 999",
        1,
    ).replace(
        "title: Dormant post-native solver and atlas programme",
        "title: drifted wave 21",
        1,
    )
    assert _preserving_yaml_text(drifted_text, cards) == canonical_text


def test_pr119_checker_accepts_later_atomic_dag_slices() -> None:
    payload = _yaml(BACKLOG_YAML)
    cards = parse_roadmap_cards(ROADMAP.read_text(encoding="utf-8"))

    check_materialized(payload, cards)


def test_pr119_authoring_roots_and_generated_mirrors_are_exact() -> None:
    assert BACKLOG_YAML.read_bytes() == MACHINE_BACKLOG_YAML.read_bytes()
    assert STATUS.read_bytes() == MACHINE_STATUS.read_bytes()
    assert REGISTRY.read_bytes() == MACHINE_REGISTRY.read_bytes()
    assert json.loads(BACKLOG_JSON.read_text(encoding="utf-8")) == _yaml(BACKLOG_YAML)
    assert json.loads(MACHINE_BACKLOG_JSON.read_text(encoding="utf-8")) == _yaml(
        BACKLOG_YAML
    )


def test_pr119_typed_edges_are_fail_closed_and_not_science_promotion() -> None:
    backlog = _yaml(BACKLOG_YAML)

    pr157 = _card(backlog, "PR-157")
    assert {edge["mode"] for edge in pr157["dependency_contracts"]} == {
        "requires_terminal_receipt"
    }
    assert pr157["claim_level"] == {
        "scheme": "not_applicable_governance_v1",
        "level": "NOT_APPLICABLE",
    }
    for pr_id in ("PR-158", "PR-166"):
        assert {edge["mode"] for edge in _card(backlog, pr_id)["dependency_contracts"]} == {
            "requires_adjudicated_claim_set"
        }
    assert _card(backlog, "PR-159")["external_dependency_contracts"] == [
        {
            "upstream_id": "AUTHENTICATED_NATIVE_DELIVERY",
            "mode": "requires_authenticated_external_receipt",
            "scope": "native_low_ell_delivery",
        }
    ]
    assert all(
        _card(backlog, f"PR-{number:03d}")["activation_state"]
        == "DORMANT_EXTERNAL"
        for number in range(159, 167)
    )
    assert all(
        _card(backlog, f"PR-{number:03d}")["scientific_status_on_intake"] == "OPEN"
        for number in range(119, 167)
    )

    pr150 = _card(backlog, "PR-150")
    assert pr150["execution_constraints"] == {
        "recorded_on": "2026-07-15",
        "authority": "explicit_user_instruction",
        "pr3_ffp10_e2e_download": "COMPLETE",
        "pr4_npipe_e2e_download": "NOT_STARTED",
        "pr4_npipe_all_downloads": "FORBIDDEN",
        "pr4_npipe_reduction": "SKIP_ENTIRELY",
        "pr4_data_analysis": "SKIP_ENTIRELY",
        "pr4_numeric_figure_combined_outputs": "FORBIDDEN",
        "original_joint_pr3_pr4_c3_gate_satisfied": False,
    }
    assert pr150["claim_level"] == {
        "scheme": "roadmap_rescue_v1",
        "level": "C2",
    }
    assert "PR4 관련 산출물은 비수치 SKIPPED_BY_USER_SCOPE" in pr150["dod"][1]
    forbidden = pr150["forbidden"]
    assert isinstance(forbidden, list) and len(forbidden) == 1
    assert all(
        token in forbidden[0]
        for token in (
            "full-frequency",
            "component-separated",
            "single-channel",
            "subset-stream",
            "partial-range",
            "reduction",
            "analysis",
            "numeric result",
            "figure",
            "PR3+PR4 combined output",
        )
    )
    assert "original joint roadmap_rescue_v1:C3 claim" in pr150["claim_impact"]


def test_active_claim_level_prose_is_scheme_qualified_but_finding_ids_are_immutable() -> None:
    backlog = _yaml(BACKLOG_YAML)
    for card in _cards(backlog)[65:]:
        for field in SEMANTIC_CLAIM_FIELDS:
            assert not any(
                BARE_ACTIVE_CLAIM_LEVEL_RE.search(text)
                for text in _strings(card[field])
            ), f"{card['id']} {field} contains a bare claim level"

    # These are immutable audit finding identifiers, not claim-level prose.
    assert "C1-K5-MV-F1" in _card(backlog, "PR-120")["targets"][0]
    assert "C3-K5-VCORR-ML-F1" in _card(backlog, "PR-120")["targets"][0]


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda payload: _cards(payload).pop(), "coverage mismatch"),
        (
            lambda payload: _card(payload, "PR-120").__setitem__("owner", "TEFF"),
            "forbidden or unknown active owner",
        ),
        (
            lambda payload: _card(payload, "PR-120").__setitem__(
                "claim_level", {"level": "C1"}
            ),
            "explicit scheme and level",
        ),
        (
            lambda payload: _card(payload, "PR-120")["dependency_contracts"][0].__setitem__(
                "upstream_id", "PR-118"
            ),
            "exactly match depends",
        ),
        (
            lambda payload: _card(payload, "PR-120")["dependency_contracts"][0].__setitem__(
                "mode", "requires_terminal_receipt"
            ),
            "restricted to PR-157",
        ),
        (
            lambda payload: _card(payload, "PR-150")["execution_constraints"].__setitem__(
                "pr4_data_analysis", "RUN"
            ),
            "PR3-complete/PR4-skip constraint",
        ),
        (
            lambda payload: _card(payload, "PR-150").__setitem__(
                "forbidden",
                [
                    "NPIPE full-frequency download forbidden; component-separated/single-channel subset allowed."
                ],
            ),
            "unconditionally forbid all PR4/NPIPE download",
        ),
        (
            lambda payload: _card(payload, "PR-150").__setitem__(
                "claim_impact", "PR3-only diagnostic C2"
            ),
            "unqualified roadmap claim level",
        ),
        (
            lambda payload: _card(payload, "PR-150")["dod"].append(
                "PR4 component-separated subset download is allowed."
            ),
            "unconditionally forbid all PR4/NPIPE download",
        ),
        (
            lambda payload: _card(payload, "PR-150")["dod"].append(
                "Bare active ceiling C3"
            ),
            "unqualified roadmap claim level",
        ),
        (
            lambda payload: _card(payload, "PR-159")[
                "external_dependency_contracts"
            ][0].__setitem__("scope", "generic_delivery"),
            "native_low_ell_delivery scope",
        ),
    ],
)
def test_strict_rescue_validator_rejects_semantic_drift(mutation, message: str) -> None:
    backlog = copy.deepcopy(_pr119_intake_payload())
    mutation(backlog)

    with pytest.raises(ValueError, match=message):
        validate_long_horizon_rescue_slice(backlog, validate_backlog(backlog))


def test_status_axes_require_disjoint_full_coverage_and_terminal_receipts() -> None:
    backlog = _pr119_intake_payload()
    info = validate_backlog(backlog)
    status = _pr119_status(backlog)

    overlapping = copy.deepcopy(status)
    overlapping["pending"].append("PR-159")
    with pytest.raises(ValueError, match="overlap"):
        validate_long_horizon_rescue_slice(backlog, info, status=overlapping)

    missing = copy.deepcopy(status)
    # PR-120..123 left `pending` as they completed (PR-124 preflight repair:
    # pick a card actually still pending instead of the hardcoded PR-120).
    assert missing["pending"], "status must have at least one pending card"
    missing["pending"].remove(missing["pending"][0])
    with pytest.raises(ValueError, match="coverage missing"):
        validate_long_horizon_rescue_slice(backlog, info, status=missing)

    terminal_without_receipt = copy.deepcopy(status)
    if terminal_without_receipt.get("in_progress") == "PR-119":
        terminal_without_receipt["in_progress"] = None
        terminal_without_receipt["completed"].append("PR-119")
    terminal_without_receipt["execution_resolutions"].pop("PR-119", None)
    with pytest.raises(ValueError, match="require execution resolution receipts"):
        validate_long_horizon_rescue_slice(
            backlog, info, status=terminal_without_receipt
        )


def test_status_terminal_buckets_have_exact_resolution_mapping_and_receipt_pointer() -> None:
    backlog = _pr119_intake_payload()
    info = validate_backlog(backlog)
    status = _pr119_status(backlog)

    completed_mismatch = copy.deepcopy(status)
    completed_mismatch["execution_resolutions"]["PR-119"]["resolution"] = (
        "BLOCKED_WITH_RECEIPT"
    )
    with pytest.raises(ValueError, match="requires one of.*COMPLETED_SUCCESS"):
        validate_long_horizon_rescue_slice(backlog, info, status=completed_mismatch)

    blocked_mismatch = copy.deepcopy(status)
    blocked_mismatch["completed"].remove("PR-119")
    blocked_mismatch["blocked"].append("PR-119")
    with pytest.raises(
        ValueError,
        match="requires one of.*BLOCKED_WITH_RECEIPT.*COMPLETED_FAILED_WITH_RECEIPT",
    ):
        validate_long_horizon_rescue_slice(backlog, info, status=blocked_mismatch)

    skipped_mismatch = copy.deepcopy(status)
    skipped_mismatch["completed"].remove("PR-119")
    skipped_mismatch["skipped"] = ["PR-119"]
    with pytest.raises(ValueError, match="requires one of.*ABANDONED_WITH_RECEIPT"):
        validate_long_horizon_rescue_slice(backlog, info, status=skipped_mismatch)

    empty_receipt = copy.deepcopy(status)
    empty_receipt["execution_resolutions"]["PR-119"]["receipt"] = "  "
    with pytest.raises(ValueError, match="receipt pointer must be nonempty"):
        validate_long_horizon_rescue_slice(backlog, info, status=empty_receipt)

    blocked_valid = copy.deepcopy(status)
    blocked_valid["completed"].remove("PR-119")
    blocked_valid["blocked"].append("PR-119")
    blocked_valid["execution_resolutions"]["PR-119"]["resolution"] = (
        "BLOCKED_WITH_RECEIPT"
    )
    validate_long_horizon_rescue_slice(backlog, info, status=blocked_valid)

    completed_failed_valid = copy.deepcopy(blocked_valid)
    completed_failed_valid["execution_resolutions"]["PR-119"]["resolution"] = (
        "COMPLETED_FAILED_WITH_RECEIPT"
    )
    validate_long_horizon_rescue_slice(backlog, info, status=completed_failed_valid)


def test_registry_bootstrap_is_bounded_default_deny_and_cannot_promote_science() -> None:
    registry = _yaml(REGISTRY)

    assert registry["default_deny"] is True
    assert registry["maximum_status_without_verified_external_authority"] == (
        "ADJUDICATION_PENDING"
    )
    assert registry["external_scientific_adjudicators"] == []
    assert {role for principal in registry["principals"] for role in principal["allowed_roles"]} == {
        "author",
        "adjudicator",
    }
    assert all(
        principal["can_promote_scientific_status"] is False
        for principal in registry["principals"]
    )
    assert all(principal["valid_until"] for principal in registry["principals"])
