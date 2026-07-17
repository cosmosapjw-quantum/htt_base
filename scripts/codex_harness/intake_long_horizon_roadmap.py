#!/usr/bin/env python3
"""Materialize the approved PR-119..PR-166 roadmap slice into the active DAG.

The roadmap is the reviewed planning source.  This script deliberately refuses
to intake PR-167..PR-183: PR-167 owns that later advocate-track transaction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


REPO = Path(__file__).resolve().parents[2]
ROADMAP = REPO / "docs/research_program/LONG_HORIZON_RESCUE_PR_ROADMAP_20260714.md"
SPEC = REPO / "docs/research_program/long_horizon_rescue/pr119_spec.yaml"
BACKLOG_YAML = REPO / "docs/codex_handoff/pr_backlog.yaml"
BACKLOG_JSON = REPO / "docs/codex_handoff/pr_backlog.json"
MACHINE_BACKLOG_YAML = REPO / "machine_readable/pr_backlog.yaml"
MACHINE_BACKLOG_JSON = REPO / "machine_readable/pr_backlog.json"

EXPECTED_BASELINE_SHA256 = (
    "960bb4ebb6a4a262f2f5e3c5b622881f1736bbb93fd0af707876acefb9a18309"
)
# Pin advanced 2026-07-17 by AMENDMENT_01 (four targeted edits; see
# docs/research_program/LONG_HORIZON_RESCUE_PR_ROADMAP_20260714_AMENDMENT_01_20260717.md
# — the amendment doc is the explicit reapproval record this pin requires).
EXPECTED_ROADMAP_SHA256 = (
    "caaab4b7255181e75093a5b662f4febf278330db07dad7cdce65e44c6587b361"
)
FIRST_ID = 119
LAST_ID = 166
FORBIDDEN_FIRST_ID = 167
FORBIDDEN_LAST_ID = 183

CARD_RE = re.compile(r"^### PR-(1(?:19|[2-5]\d|6[0-6])) — (.+)$", re.MULTILINE)
FIELD_RE = re.compile(r"^- \*\*(.+?):\*\* (.+)$", re.MULTILINE)
CANONICAL_OWNERS = {"COMMON", "HTT", "MIO", "BASS", "OBSSTAT"}
OWNER_SCOPE = {
    "COMMON": "common",
    "HTT": "htt",
    "MIO": "mio",
    "BASS": "bass_py",
    "OBSSTAT": "obsstat",
}
SCOPE_ROOTS = {
    "common": ("htt/src/common", "scripts/codex_harness", "tests/contracts"),
    "htt": ("htt/htt", "tests/htt"),
    "mio": ("htt/mio", "tests/mio"),
    "bass_py": ("htt/bass", "tests/bass"),
    "canonical_BASS": ("htt/bass", "tests/bass"),
    "obsstat": ("htt/obsstat", "htt/src/obsstat", "tests/obsstat"),
}

# Claim levels embedded in prose must carry their scheme.  The negative
# lookahead deliberately preserves immutable finding identifiers such as
# ``C1-K5-MV-F1`` while still qualifying ranges such as ``C1--C2``.
BARE_ACTIVE_CLAIM_LEVEL_RE = re.compile(
    r"(?<![A-Za-z0-9_:])C([0-6])(?!-[A-Za-z0-9])\b"
)
SEMANTIC_CLAIM_PROSE_FIELDS = (
    "title",
    "targets",
    "dod",
    "kill",
    "claim_impact",
    "forbidden",
    "anti_drift",
)


def _qualify_claim_level_prose(value: Any) -> Any:
    """Version bare roadmap claim levels without rewriting finding IDs."""

    if isinstance(value, str):
        return BARE_ACTIVE_CLAIM_LEVEL_RE.sub(
            lambda match: f"roadmap_rescue_v1:C{match.group(1)}", value
        )
    if isinstance(value, list):
        return [_qualify_claim_level_prose(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _qualify_claim_level_prose(item) for key, item in value.items()
        }
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_mapping(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.relative_to(REPO)} must contain a mapping")
    return payload


def _field_map(block: str) -> dict[str, str]:
    return {key: value.strip() for key, value in FIELD_RE.findall(block)}


def _expand_pr_refs(text: str) -> list[str]:
    refs: list[str] = []
    for start_raw, end_raw in re.findall(r"PR-(\d+)(?:--(\d+))?", text):
        start = int(start_raw)
        end = int(end_raw) if end_raw else start
        refs.extend(f"PR-{value:03d}" for value in range(start, end + 1))
    return list(dict.fromkeys(refs))


def _wave(pr_number: int) -> int:
    ranges = (
        (119, 123, 13),
        (124, 128, 14),
        (129, 133, 15),
        (134, 138, 16),
        (139, 143, 17),
        (144, 148, 18),
        (149, 153, 19),
        (154, 158, 20),
        (159, 166, 21),
    )
    for start, end, wave in ranges:
        if start <= pr_number <= end:
            return wave
    raise ValueError(f"no wave for PR-{pr_number:03d}")


def _verification_level(wave: int) -> str:
    if wave == 13:
        return "L1"
    if wave in {14, 15}:
        return "L2"
    if wave in {16, 17, 18, 19, 20}:
        return "L3"
    return "L4"


def _owner(owner_line: str) -> str:
    match = re.search(r"`(COMMON|HTT|MIO|BASS|OBSSTAT)`", owner_line)
    if not match:
        raise ValueError(f"cannot parse canonical owner from {owner_line!r}")
    return match.group(1)


def _contributors(owner_line: str, owner: str) -> list[str]:
    values = [
        token
        for token in re.findall(r"`([^`]+)`", owner_line)
        if token in CANONICAL_OWNERS and token != owner
    ]
    return list(dict.fromkeys(values))


def _implementation_scopes(owner_line: str, owner: str) -> list[str]:
    explicit = re.search(r"implementation scope `([^`]+)`", owner_line)
    if explicit:
        scopes = explicit.group(1).split("|")
    else:
        scopes = [OWNER_SCOPE[owner]]
    unknown = sorted(set(scopes) - set(SCOPE_ROOTS))
    if unknown:
        raise ValueError(f"unknown implementation scopes: {unknown}")
    return scopes


def _planned_files(pr_id: str, scopes: list[str]) -> list[str]:
    roots: list[str] = []
    for scope in scopes:
        roots.extend(SCOPE_ROOTS[scope])
    roots.append(f"docs/PR_DELTAS/{pr_id.lower()}.md")
    return list(dict.fromkeys(roots))


def _cost(owner_line: str) -> str:
    return owner_line.rsplit(";", 1)[-1].strip().rstrip(".")


def _claim_level(pr_number: int, maximum_claim: str) -> dict[str, str]:
    if pr_number in {119, 157, 158}:
        return {"scheme": "not_applicable_governance_v1", "level": "NOT_APPLICABLE"}
    levels = [int(value) for value in re.findall(r"\bC([0-6])\b", maximum_claim)]
    if not levels:
        return {"scheme": "not_applicable_governance_v1", "level": "NOT_APPLICABLE"}
    return {"scheme": "roadmap_rescue_v1", "level": f"C{max(levels)}"}


def _claim_tier(pr_number: int, claim_level: dict[str, str], maximum_claim: str) -> str:
    if 159 <= pr_number <= 166:
        return "blocked"
    level = claim_level["level"]
    if level == "NOT_APPLICABLE":
        return "exploratory" if pr_number == 119 else "diagnostic_only"
    number = int(level[1:])
    if "discrimination candidate" in maximum_claim:
        return "conditional"
    return {
        0: "blocked",
        1: "exploratory",
        2: "conditional",
        3: "diagnostic_only",
        4: "conditional",
        5: "conditional",
        6: "blocked",
    }[number]


def _dependency_contracts(pr_number: int, dependencies: list[str]) -> list[dict[str, str]]:
    if pr_number == 157:
        mode = "requires_terminal_receipt"
    elif pr_number in {158, 166}:
        mode = "requires_adjudicated_claim_set"
    else:
        mode = "requires_success"
    return [{"upstream_id": dependency, "mode": mode} for dependency in dependencies]


def _adjudicator_role(pr_number: int, owner_line: str, block: str) -> str:
    combined = f"{owner_line}\n{block}".lower()
    if pr_number in {165, 166} or "external/domain panel" in combined:
        return "external_non_author_panel"
    if pr_number == 163:
        return "independent_blinded_challenge_adjudicator"
    if pr_number == 157:
        return "independent_non_author_finding_panel"
    return "internal_non_author_reviewer"


def _apply_user_execution_constraints(pr_number: int, card: dict[str, Any]) -> None:
    """Apply explicit execution constraints that supersede roadmap defaults."""

    if pr_number != 150:
        return
    card["execution_constraints"] = {
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
    card["dod"] = [
        "PR3/FFP10 E2E 입력은 다운로드 완료 상태로 intake하고 PR-149에서 freeze한 동일 mask/transfer/statistic/max-scan 경로로 exchangeable pooled-rank calibration을 수행한다. PR4/NPIPE는 full-frequency, component-separated, single-channel, subset-stream, partial-range를 포함한 어떤 데이터도 다운로드하지 않고 reduction·분석도 전부 실행하지 않는다.",
        "PR3 input license/hash manifest, observed/null byte-equivalent runner, finite-rank intervals, method-wise/global scan, Tier-1/Tier-2 retention receipt와 faithful-cache gate. PR4 관련 산출물은 비수치 SKIPPED_BY_USER_SCOPE receipt만 만들고 PR4/NPIPE 수치·표·그림·p-value·method comparison·PR3+PR4 결합 결과를 생성하지 않는다.",
    ]
    card["kill"] = (
        "PR3 E2E input/support가 없거나 observed/null path가 다르면 scientific status는 "
        "BLOCKED로 유지한다. PR4/NPIPE payload를 종류·채널·subset·부분 범위와 무관하게 "
        "다운로드하거나 reduction/분석에 사용하거나, PR4 수치·표·그림·결합 산출물을 만들거나, "
        "PR4가 없는 상태를 joint PR3+PR4 calibration으로 대체하거나 original C3 gate 통과로 "
        "기록하면 실패다. PR3 raw는 faithful-cache gate GREEN 전 삭제하지 않는다."
    )
    card["claim_level"] = {"scheme": "roadmap_rescue_v1", "level": "C2"}
    card["claim_tier_ceiling"] = "diagnostic_only"
    card["claim_impact"] = (
        "PR3/FFP10-E2E-conditional morphology diagnostic C2 only; PR4/NPIPE systematics "
        "comparison and original joint C3 claim remain unavailable."
    )
    # Replace, rather than extend, the inherited roadmap clause that allowed a
    # component-separated/single-channel NPIPE subset.
    card["forbidden"] = [
        "PR4/NPIPE 데이터는 full-frequency, component-separated, single-channel, subset-stream, partial-range 등 어떤 형태로도 다운로드하지 않는다. 기존 또는 외부 PR4 payload도 intake·reduction·cache·analysis에 사용하지 않는다. PR4/NPIPE numeric result, table, figure, p-value, method comparison, PR3+PR4 combined output을 생성하지 않는다. 허용되는 PR4 산출물은 비수치 SKIPPED_BY_USER_SCOPE receipt뿐이다."
    ]
    card["anti_drift"] = [
        "원 로드맵은 PR4를 필수 추가분석으로 정의하지만 2026-07-15 사용자 지시에 따라 PR4/NPIPE의 모든 다운로드·reduction·데이터 분석과 수치·표·그림·결합 산출물을 전부 스킵한다. 이 scope reduction은 PR4를 optional evidence로 재해석하지 않으며, PR4 의존 결론은 BLOCKED/미판정으로 남긴다."
    ]


def parse_roadmap_cards(text: str) -> list[dict[str, Any]]:
    matches = list(CARD_RE.finditer(text))
    if len(matches) != LAST_ID - FIRST_ID + 1:
        raise ValueError(f"expected 48 roadmap cards, found {len(matches)}")
    cards: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        pr_number = int(match.group(1))
        expected = FIRST_ID + index
        if pr_number != expected:
            raise ValueError(f"expected PR-{expected:03d}, found PR-{pr_number:03d}")
        end = matches[index + 1].start() if index + 1 < len(matches) else text.find("\n## ", match.end())
        if end < 0:
            end = len(text)
        block = text[match.end() : end]
        fields = _field_map(block)
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
            raise ValueError(f"PR-{pr_number:03d} missing roadmap fields: {missing}")
        pr_id = f"PR-{pr_number:03d}"
        owner_line = fields["Owner / dependencies / cost"]
        owner = _owner(owner_line)
        dependencies = [ref for ref in _expand_pr_refs(owner_line) if ref != pr_id]
        scopes = _implementation_scopes(owner_line, owner)
        claim_level = _claim_level(pr_number, fields["최대 claim"])
        wave = _wave(pr_number)
        test_slug = re.sub(r"[^a-z0-9]+", "_", match.group(2).lower()).strip("_")[:48]
        card: dict[str, Any] = {
            "id": pr_id,
            "wave": wave,
            "title": match.group(2).strip(),
            "owner": owner,
            "contributors": _contributors(owner_line, owner),
            "adjudicator_role": _adjudicator_role(pr_number, owner_line, block),
            "implementation_scopes": scopes,
            "depends": dependencies,
            "dependency_contracts": _dependency_contracts(pr_number, dependencies),
            "targets": [fields.get("Targets", f"Roadmap card {pr_id}: {match.group(2).strip()}")],
            "files": _planned_files(pr_id, scopes),
            "tests": [
                "venv/bin/python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml",
                f"to-be-created:venv/bin/python -B -m pytest -p no:cacheprovider -q tests/pr_cards/test_{pr_id.lower().replace('-', '_')}_{test_slug}.py",
            ],
            "dod": [fields["실제로 할 것"], fields["검증·산출물"]],
            "kill": fields["Exit / kill"],
            "cost": _cost(owner_line),
            "level": _verification_level(wave),
            "scope": "post-native" if pr_number >= 159 else "pre-solver",
            "risk": "high" if "high" in _cost(owner_line) else "medium" if "medium" in _cost(owner_line) else "low",
            "claim_tier_ceiling": _claim_tier(pr_number, claim_level, fields["최대 claim"]),
            "claim_level": claim_level,
            "claim_impact": fields["최대 claim"],
            "forbidden": [fields["하지 말 것"]],
            "anti_drift": [fields["주의·anti-drift"]],
            "roadmap_anchor": f"docs/research_program/LONG_HORIZON_RESCUE_PR_ROADMAP_20260714.md#pr-{pr_number}",
            "activation_state": "DORMANT_EXTERNAL" if pr_number >= 159 else "PENDING",
            "scientific_status_on_intake": "OPEN",
        }
        if pr_number == 159:
            card["external_dependency_contracts"] = [
                {
                    "upstream_id": "AUTHENTICATED_NATIVE_DELIVERY",
                    "mode": "requires_authenticated_external_receipt",
                    "scope": "native_low_ell_delivery",
                }
            ]
        _apply_user_execution_constraints(pr_number, card)
        for field in SEMANTIC_CLAIM_PROSE_FIELDS:
            card[field] = _qualify_claim_level_prose(card[field])
        cards.append(card)
    return cards


def _wave_rows() -> list[dict[str, Any]]:
    return [
        {"wave": 13, "title": "Authority, quarantine, and reproducibility foundation"},
        {"wave": 14, "title": "Theory foundation I: authority and non-identification"},
        {"wave": 15, "title": "Theory foundation II: estimators and local/global separation"},
        {"wave": 16, "title": "Statistics I: estimands, finite nulls, and partial identification"},
        {"wave": 17, "title": "Statistics II: holdout, evidence, abstention, and MIO calibration"},
        {"wave": 18, "title": "CF4 and velocity-field research"},
        {"wave": 19, "title": "Planck, DESI, ACT, and JWST provenance"},
        {"wave": 20, "title": "Hierarchical forecasts, cross-survey tests, and adjudication"},
        {"wave": 21, "title": "Dormant post-native solver and atlas programme"},
    ]


def materialize_payload(existing: dict[str, Any], cards: list[dict[str, Any]]) -> dict[str, Any]:
    old_cards = existing.get("prs")
    if not isinstance(old_cards, list):
        raise ValueError("backlog prs must be a list")
    ids = [card.get("id") for card in old_cards if isinstance(card, dict)]
    if any(f"PR-{value:03d}" in ids for value in range(FORBIDDEN_FIRST_ID, FORBIDDEN_LAST_ID + 1)):
        raise ValueError("forbidden PR-167..PR-183 already present")
    new_ids = {f"PR-{value:03d}" for value in range(FIRST_ID, LAST_ID + 1)}
    present = new_ids & set(ids)
    if present and present != new_ids:
        raise ValueError(f"partial rescue intake already present: {sorted(present)}")
    if not present:
        if len(old_cards) != 65:
            raise ValueError(f"expected frozen 65-card baseline, found {len(old_cards)}")
        existing["prs"] = [*old_cards, *cards]
        policy = existing.setdefault("policy", {})
        order = policy.get("topological_order")
        if not isinstance(order, list) or len(order) != 65:
            raise ValueError("baseline policy.topological_order must contain 65 ids")
        policy["topological_order"] = [*order, *[card["id"] for card in cards]]
        waves = existing.setdefault("waves", [])
        waves.extend(_wave_rows())
        policy["long_horizon_intake"] = {
            "spec": "docs/research_program/long_horizon_rescue/pr119_spec.yaml",
            "active_slice": "PR-119..PR-166",
            "advocate_slice": "deferred_to_PR-167",
            "scientific_rescue_count_on_intake": 0,
        }
    else:
        if len(old_cards) != 113 or [card.get("id") for card in old_cards[65:]] != [
            card["id"] for card in cards
        ]:
            raise ValueError(
                "existing rescue slice must be the contiguous PR-119..PR-166 suffix"
            )
        # Review-driven corrections are a normal part of PR-119.  Replacing the
        # complete suffix makes --write deterministic and idempotent while the
        # frozen first 65 cards remain untouched.
        existing["prs"] = [*old_cards[:65], *cards]
        policy = existing.setdefault("policy", {})
        current_order = policy.get("topological_order")
        if not isinstance(current_order, list) or len(current_order) != 113:
            raise ValueError("existing policy.topological_order must contain 113 ids")
        policy["topological_order"] = [
            *current_order[:65],
            *[card["id"] for card in cards],
        ]
        policy["long_horizon_intake"] = {
            "spec": "docs/research_program/long_horizon_rescue/pr119_spec.yaml",
            "active_slice": "PR-119..PR-166",
            "advocate_slice": "deferred_to_PR-167",
            "scientific_rescue_count_on_intake": 0,
        }
        waves = existing.get("waves")
        if (
            not isinstance(waves, list)
            or len(waves) < 13
            or [row.get("wave") for row in waves[:13] if isinstance(row, dict)]
            != list(range(13))
        ):
            raise ValueError("frozen wave 0..12 metadata is malformed")
        existing["waves"] = [*waves[:13], *_wave_rows()]
    return existing


def _yaml_text(payload: dict[str, Any]) -> str:
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=100)


def _json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def _preserving_yaml_text(existing_text: str, cards: list[dict[str, Any]]) -> str:
    """Append the new slice without reformatting the frozen 65-card YAML text."""

    existing_slice_marker = "\n- id: PR-119\n"
    if existing_slice_marker in existing_text:
        if existing_text.count(existing_slice_marker) != 1:
            raise ValueError("cannot locate unique existing PR-119 slice marker")
        order_start = "  topological_order:\n"
        order_end = "  checkpoint_every_completed_prs:"
        if existing_text.count(order_start) != 1 or existing_text.count(order_end) != 1:
            raise ValueError("cannot locate unique policy topological-order block")
        start = existing_text.index(order_start)
        end = existing_text.index(order_end, start)
        # Use the canonical policy order from the generated cards while
        # preserving the already-frozen legacy order text before PR-119.
        legacy_order_text = existing_text[start:end]
        pr119_order_marker = "  - PR-119\n"
        if legacy_order_text.count(pr119_order_marker) != 1:
            raise ValueError("cannot locate unique PR-119 policy-order marker")
        legacy_order_prefix = legacy_order_text[: legacy_order_text.index(pr119_order_marker)]
        order_text = legacy_order_prefix + "".join(
            f"  - {card['id']}\n" for card in cards
        )
        existing_text = existing_text[:start] + order_text + existing_text[end:]

        policy_start = "  long_horizon_intake:\n"
        waves_start = "waves:\n"
        if existing_text.count(policy_start) != 1 or existing_text.count(waves_start) != 1:
            raise ValueError("cannot locate unique long-horizon policy block")
        start = existing_text.index(policy_start)
        end = existing_text.index(waves_start, start)
        policy_text = (
            "  long_horizon_intake:\n"
            "    spec: docs/research_program/long_horizon_rescue/pr119_spec.yaml\n"
            "    active_slice: PR-119..PR-166\n"
            "    advocate_slice: deferred_to_PR-167\n"
            "    scientific_rescue_count_on_intake: 0\n"
        )
        existing_text = existing_text[:start] + policy_text + existing_text[end:]

        wave_start = "- wave: 13\n"
        prs_start = "prs:\n"
        if existing_text.count(wave_start) != 1 or existing_text.count(prs_start) != 1:
            raise ValueError("cannot locate unique rescue-wave block")
        start = existing_text.index(wave_start)
        end = existing_text.index(prs_start, start)
        wave_text = yaml.safe_dump(
            {"waves": _wave_rows()}, sort_keys=False, allow_unicode=True, width=100
        ).removeprefix("waves:\n")
        existing_text = existing_text[:start] + wave_text + existing_text[end:]

        slice_start = existing_text.index(existing_slice_marker) + 1
        frozen_prefix = existing_text[:slice_start]
        card_text = yaml.safe_dump(
            {"prs": cards}, sort_keys=False, allow_unicode=True, width=100
        ).removeprefix("prs:\n")
        return frozen_prefix + card_text
    order_marker = "  - PR-118\n  checkpoint_every_completed_prs: 5\n"
    if existing_text.count(order_marker) != 1:
        raise ValueError("cannot locate unique PR-118 policy-order marker")
    order_rows = "".join(f"  - {card['id']}\n" for card in cards)
    existing_text = existing_text.replace(
        order_marker,
        f"  - PR-118\n{order_rows}  checkpoint_every_completed_prs: 5\n",
    )
    waves_marker = "waves:\n"
    if existing_text.count(waves_marker) != 1:
        raise ValueError("cannot locate unique waves marker")
    policy_rows = (
        "  long_horizon_intake:\n"
        "    spec: docs/research_program/long_horizon_rescue/pr119_spec.yaml\n"
        "    active_slice: PR-119..PR-166\n"
        "    advocate_slice: deferred_to_PR-167\n"
        "    scientific_rescue_count_on_intake: 0\n"
    )
    existing_text = existing_text.replace(waves_marker, f"{policy_rows}{waves_marker}")
    prs_marker = "prs:\n"
    if existing_text.count(prs_marker) != 1:
        raise ValueError("cannot locate unique prs marker")
    wave_text = yaml.safe_dump(
        {"waves": _wave_rows()}, sort_keys=False, allow_unicode=True, width=100
    ).removeprefix("waves:\n")
    existing_text = existing_text.replace(prs_marker, f"{wave_text}{prs_marker}")
    card_text = yaml.safe_dump(
        {"prs": cards}, sort_keys=False, allow_unicode=True, width=100
    ).removeprefix("prs:\n")
    return existing_text.rstrip() + "\n" + card_text


def write_materialized(payload: dict[str, Any], cards: list[dict[str, Any]]) -> None:
    original_text = BACKLOG_YAML.read_text(encoding="utf-8")
    yaml_text = _preserving_yaml_text(original_text, cards)
    parsed = yaml.safe_load(yaml_text)
    if parsed != payload:
        raise ValueError("preserving YAML materialization differs from semantic payload")
    json_text = _json_text(payload)
    BACKLOG_YAML.write_text(yaml_text, encoding="utf-8")
    MACHINE_BACKLOG_YAML.write_text(yaml_text, encoding="utf-8")
    BACKLOG_JSON.write_text(json_text, encoding="utf-8")
    MACHINE_BACKLOG_JSON.write_text(json_text, encoding="utf-8")


def check_materialized(payload: dict[str, Any], cards: list[dict[str, Any]]) -> None:
    expected = materialize_payload(payload, cards)
    if BACKLOG_YAML.read_text(encoding="utf-8") != MACHINE_BACKLOG_YAML.read_text(encoding="utf-8"):
        raise ValueError("YAML backlog mirrors differ")
    docs_json = json.loads(BACKLOG_JSON.read_text(encoding="utf-8"))
    machine_json = json.loads(MACHINE_BACKLOG_JSON.read_text(encoding="utf-8"))
    if docs_json != machine_json or docs_json != expected:
        raise ValueError("JSON backlog mirrors are not semantically equal to canonical YAML")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        if sha256_file(ROADMAP) != EXPECTED_ROADMAP_SHA256:
            raise ValueError("roadmap hash drift; revise and reapprove the PR-119 SPEC")
        spec = _load_mapping(SPEC)
        if spec.get("spec_status") != "approved_for_implementation":
            raise ValueError("PR-119 SPEC is not approved for implementation")
        text = ROADMAP.read_text(encoding="utf-8")
        cards = parse_roadmap_cards(text)
        payload = _load_mapping(BACKLOG_YAML)
        ids = {card.get("id") for card in payload.get("prs", []) if isinstance(card, dict)}
        if not any(f"PR-{value:03d}" in ids for value in range(FIRST_ID, LAST_ID + 1)):
            if sha256_file(BACKLOG_YAML) != EXPECTED_BASELINE_SHA256:
                raise ValueError("canonical backlog baseline hash drift")
        if args.write:
            write_materialized(materialize_payload(payload, cards), cards)
        else:
            check_materialized(payload, cards)
    except (OSError, ValueError, yaml.YAMLError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"OK: PR-{FIRST_ID}..PR-{LAST_ID} long-horizon intake {'written' if args.write else 'verified'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
