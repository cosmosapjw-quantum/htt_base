#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


RESCUE_FIRST_PR = 119
RESCUE_LAST_PR = 166
ADVOCATE_FIRST_PR = 167
ADVOCATE_LAST_PR = 183
RESCUE_CARD_COUNT = RESCUE_LAST_PR - RESCUE_FIRST_PR + 1
RESCUE_TOTAL_CARD_COUNT = 113
RESCUE_REQUIRED_FIELDS = {
    "id",
    "wave",
    "title",
    "owner",
    "contributors",
    "adjudicator_role",
    "implementation_scopes",
    "depends",
    "dependency_contracts",
    "targets",
    "files",
    "tests",
    "dod",
    "kill",
    "cost",
    "claim_tier_ceiling",
    "claim_level",
    "forbidden",
    "anti_drift",
    "roadmap_anchor",
    "activation_state",
    "scientific_status_on_intake",
}
RESCUE_ACTIVE_OWNERS = {"COMMON", "HTT", "MIO", "BASS", "OBSSTAT"}
RESCUE_FORBIDDEN_OWNERS = {"TSC", "TSC_LEGACY", "TEFF", "MANUSCRIPT", "BASS_PY"}
RESCUE_IMPLEMENTATION_SCOPES = {
    "common",
    "htt",
    "mio",
    "bass_py",
    "canonical_BASS",
    "obsstat",
}
RESCUE_EDGE_MODES = {
    "requires_success",
    "requires_terminal_receipt",
    "requires_adjudicated_claim_set",
}
RESCUE_CLAIM_LEVELS = {
    "roadmap_rescue_v1": {f"C{index}" for index in range(7)},
    "not_applicable_governance_v1": {"NOT_APPLICABLE"},
}
RESCUE_EXECUTION_RESOLUTIONS = {
    "COMPLETED_SUCCESS",
    "COMPLETED_FAILED_WITH_RECEIPT",
    "BLOCKED_WITH_RECEIPT",
    "ABANDONED_WITH_RECEIPT",
}
RESCUE_SEMANTIC_CLAIM_FIELDS = (
    "title",
    "targets",
    "dod",
    "kill",
    "claim_impact",
    "forbidden",
    "anti_drift",
)
BARE_ACTIVE_CLAIM_LEVEL_RE = re.compile(
    r"(?<![A-Za-z0-9_:])C([0-6])(?!-[A-Za-z0-9])\b"
)
PR150_EXECUTION_CONSTRAINT = {
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
PR150_FORBIDDEN = [
    "PR4/NPIPE 데이터는 full-frequency, component-separated, single-channel, subset-stream, partial-range 등 어떤 형태로도 다운로드하지 않는다. 기존 또는 외부 PR4 payload도 intake·reduction·cache·analysis에 사용하지 않는다. PR4/NPIPE numeric result, table, figure, p-value, method comparison, PR3+PR4 combined output을 생성하지 않는다. 허용되는 PR4 산출물은 비수치 SKIPPED_BY_USER_SCOPE receipt뿐이다."
]
PR150_SEMANTIC_CONTRACT = {
    "dod": [
        "PR3/FFP10 E2E 입력은 다운로드 완료 상태로 intake하고 PR-149에서 freeze한 동일 mask/transfer/statistic/max-scan 경로로 exchangeable pooled-rank calibration을 수행한다. PR4/NPIPE는 full-frequency, component-separated, single-channel, subset-stream, partial-range를 포함한 어떤 데이터도 다운로드하지 않고 reduction·분석도 전부 실행하지 않는다.",
        "PR3 input license/hash manifest, observed/null byte-equivalent runner, finite-rank intervals, method-wise/global scan, Tier-1/Tier-2 retention receipt와 faithful-cache gate. PR4 관련 산출물은 비수치 SKIPPED_BY_USER_SCOPE receipt만 만들고 PR4/NPIPE 수치·표·그림·p-value·method comparison·PR3+PR4 결합 결과를 생성하지 않는다.",
    ],
    "kill": (
        "PR3 E2E input/support가 없거나 observed/null path가 다르면 scientific status는 "
        "BLOCKED로 유지한다. PR4/NPIPE payload를 종류·채널·subset·부분 범위와 무관하게 "
        "다운로드하거나 reduction/분석에 사용하거나, PR4 수치·표·그림·결합 산출물을 만들거나, "
        "PR4가 없는 상태를 joint PR3+PR4 calibration으로 대체하거나 original "
        "roadmap_rescue_v1:C3 gate 통과로 기록하면 실패다. PR3 raw는 faithful-cache gate "
        "GREEN 전 삭제하지 않는다."
    ),
    "claim_impact": (
        "PR3/FFP10-E2E-conditional morphology diagnostic roadmap_rescue_v1:C2 only; "
        "PR4/NPIPE systematics comparison and original joint roadmap_rescue_v1:C3 claim "
        "remain unavailable."
    ),
    "forbidden": PR150_FORBIDDEN,
    "anti_drift": [
        "원 로드맵은 PR4를 필수 추가분석으로 정의하지만 2026-07-15 사용자 지시에 따라 PR4/NPIPE의 모든 다운로드·reduction·데이터 분석과 수치·표·그림·결합 산출물을 전부 스킵한다. 이 scope reduction은 PR4를 optional evidence로 재해석하지 않으며, PR4 의존 결론은 BLOCKED/미판정으로 남긴다."
    ],
}


@dataclass(frozen=True)
class DagInfo:
    prs: tuple[dict[str, Any], ...]
    ids: tuple[str, ...]
    order: tuple[str, ...]
    prereqs: dict[str, tuple[str, ...]]
    children: dict[str, tuple[str, ...]]

    @property
    def edge_count(self) -> int:
        return sum(len(deps) for deps in self.prereqs.values())


def load_yaml(path: str | Path) -> dict[str, Any]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("backlog YAML must contain a mapping")
    return payload


def _duplicate_values(values: list[str]) -> list[str]:
    return sorted({value for value in values if values.count(value) > 1})


def _stable_topological_order(ids: list[str], prereqs: dict[str, list[str]]) -> list[str]:
    indeg = {pr_id: 0 for pr_id in ids}
    children: dict[str, list[str]] = defaultdict(list)
    for pr_id in ids:
        for dep in prereqs[pr_id]:
            children[dep].append(pr_id)
            indeg[pr_id] += 1

    q = deque([pr_id for pr_id in ids if indeg[pr_id] == 0])
    order: list[str] = []
    while q:
        current = q.popleft()
        order.append(current)
        for child in children[current]:
            indeg[child] -= 1
            if indeg[child] == 0:
                q.append(child)

    if len(order) != len(ids):
        cycle = [pr_id for pr_id, degree in indeg.items() if degree > 0]
        raise ValueError(f"cycle detected involving: {cycle}")
    return order


def _validate_policy_order(
    policy_order: list[str],
    ids: list[str],
    prereqs: dict[str, list[str]],
) -> list[str]:
    if len(policy_order) != len(set(policy_order)):
        raise ValueError(
            f"duplicate policy.topological_order ids: {_duplicate_values(policy_order)}"
        )

    idset = set(ids)
    policy_set = set(policy_order)
    missing = sorted(idset - policy_set)
    unknown = sorted(policy_set - idset)
    if missing or unknown:
        parts = []
        if missing:
            parts.append(f"missing ids: {missing}")
        if unknown:
            parts.append(f"unknown ids: {unknown}")
        raise ValueError("policy.topological_order coverage mismatch: " + "; ".join(parts))

    rank = {pr_id: index for index, pr_id in enumerate(policy_order)}
    violations = [
        f"{dep}->{pr_id}"
        for pr_id, deps in prereqs.items()
        for dep in deps
        if rank[dep] >= rank[pr_id]
    ]
    if violations:
        raise ValueError(
            "policy.topological_order violates dependency order: "
            + ", ".join(violations)
        )
    return policy_order


def validate_backlog(data: dict[str, Any]) -> DagInfo:
    prs_obj = data.get("prs", [])
    if not isinstance(prs_obj, list):
        raise ValueError("prs must be a list")
    prs = []
    for index, pr in enumerate(prs_obj):
        if not isinstance(pr, dict):
            raise ValueError(f"prs[{index}] must be a mapping")
        if not isinstance(pr.get("id"), str) or not pr["id"]:
            raise ValueError(f"prs[{index}] missing string id")
        depends = pr.get("depends", [])
        if depends is None:
            depends = []
        if not isinstance(depends, list) or not all(isinstance(d, str) for d in depends):
            raise ValueError(f"{pr['id']} depends must be a list of strings")
        if len(depends) != len(set(depends)):
            raise ValueError(
                f"{pr['id']} duplicate dependency ids: {_duplicate_values(depends)}"
            )
        prs.append(pr)

    ids = [pr["id"] for pr in prs]
    duplicate_ids = _duplicate_values(ids)
    if duplicate_ids:
        raise ValueError(f"duplicate PR ids: {duplicate_ids}")

    idset = set(ids)
    prereqs = {pr["id"]: list(pr.get("depends") or []) for pr in prs}
    missing_deps = sorted({dep for deps in prereqs.values() for dep in deps if dep not in idset})
    if missing_deps:
        raise ValueError(f"missing dependency ids: {missing_deps}")

    computed_order = _stable_topological_order(ids, prereqs)
    policy_raw = data.get("policy")
    if policy_raw is not None and not isinstance(policy_raw, dict):
        raise ValueError("policy must be a mapping")
    policy = policy_raw or {}
    policy_order = policy.get("topological_order")
    if policy_order is not None:
        if not isinstance(policy_order, list) or not all(
            isinstance(pr_id, str) for pr_id in policy_order
        ):
            raise ValueError("policy.topological_order must be a list of PR ids")
        order = _validate_policy_order(policy_order, ids, prereqs)
    else:
        order = computed_order

    children: dict[str, list[str]] = {pr_id: [] for pr_id in ids}
    for pr_id, deps in prereqs.items():
        for dep in deps:
            children[dep].append(pr_id)

    return DagInfo(
        prs=tuple(prs),
        ids=tuple(ids),
        order=tuple(order),
        prereqs={pr_id: tuple(deps) for pr_id, deps in prereqs.items()},
        children={pr_id: tuple(children[pr_id]) for pr_id in ids},
    )


def _pr_range(first: int, last: int) -> list[str]:
    return [f"PR-{number:03d}" for number in range(first, last + 1)]


def _require_string_list(card: dict[str, Any], field: str) -> list[str]:
    value = card.get(field)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{card['id']} {field} must be a list of strings")
    return value


def _iter_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _iter_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_strings(item)


def _validate_rescue_status(status: dict[str, Any], info: DagInfo) -> None:
    list_fields = (
        "completed",
        "blocked",
        "skipped",
        "pending",
        "dormant_external",
    )
    states: dict[str, list[str]] = {}
    for field in list_fields:
        value = status.get(field, []) or []
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ValueError(f"status {field} must be a list of PR ids")
        if len(value) != len(set(value)):
            raise ValueError(f"status {field} contains duplicate PR ids")
        states[field] = value

    in_progress = status.get("in_progress")
    if in_progress is not None and not isinstance(in_progress, str):
        raise ValueError("status in_progress must be a PR id or null")

    membership: dict[str, list[str]] = defaultdict(list)
    for field, values in states.items():
        for pr_id in values:
            membership[pr_id].append(field)
    if in_progress is not None:
        membership[in_progress].append("in_progress")

    unknown = sorted(set(membership) - set(info.ids))
    if unknown:
        raise ValueError(f"status contains unknown PR ids: {unknown}")
    overlap = {pr_id: fields for pr_id, fields in membership.items() if len(fields) != 1}
    if overlap:
        raise ValueError(f"status orchestration states overlap: {overlap}")
    missing = sorted(set(info.ids) - set(membership))
    if missing:
        raise ValueError(f"status orchestration coverage missing PR ids: {missing}")

    dormant_expected = set(_pr_range(159, 166))
    dormant_actual = set(states["dormant_external"])
    if not dormant_actual <= dormant_expected:
        raise ValueError(
            "only PR-159..PR-166 may be dormant_external: "
            f"{sorted(dormant_actual - dormant_expected)}"
        )

    resolutions = status.get("execution_resolutions", {}) or {}
    if not isinstance(resolutions, dict):
        raise ValueError("status execution_resolutions must be a mapping")
    rescue_ids = set(_pr_range(RESCUE_FIRST_PR, RESCUE_LAST_PR))
    terminal = set(states["completed"]) | set(states["blocked"]) | set(states["skipped"])
    expected_resolutions_by_bucket = {
        **{pr_id: {"COMPLETED_SUCCESS"} for pr_id in states["completed"]},
        **{
            pr_id: {"BLOCKED_WITH_RECEIPT", "COMPLETED_FAILED_WITH_RECEIPT"}
            for pr_id in states["blocked"]
        },
        **{pr_id: {"ABANDONED_WITH_RECEIPT"} for pr_id in states["skipped"]},
    }
    for pr_id, receipt in resolutions.items():
        if pr_id not in rescue_ids:
            raise ValueError(f"execution resolution is restricted to rescue cards: {pr_id}")
        if pr_id not in terminal:
            raise ValueError(f"non-terminal PR has execution resolution: {pr_id}")
        if not isinstance(receipt, dict):
            raise ValueError(f"execution resolution for {pr_id} must be a mapping")
        resolution = receipt.get("resolution")
        if resolution not in RESCUE_EXECUTION_RESOLUTIONS:
            raise ValueError(f"invalid execution resolution for {pr_id}: {resolution!r}")
        expected_resolutions = expected_resolutions_by_bucket[pr_id]
        if resolution not in expected_resolutions:
            raise ValueError(
                f"{pr_id} terminal bucket requires one of "
                f"{sorted(expected_resolutions)}, "
                f"found {resolution!r}"
            )
        receipt_pointer = receipt.get("receipt")
        if not isinstance(receipt_pointer, str) or not receipt_pointer.strip():
            raise ValueError(f"{pr_id} execution resolution receipt pointer must be nonempty")
    terminal_rescue = terminal & rescue_ids
    missing_receipts = sorted(terminal_rescue - set(resolutions))
    if missing_receipts:
        raise ValueError(
            "terminal rescue cards require execution resolution receipts: "
            f"{missing_receipts}"
        )


def validate_long_horizon_rescue_slice(
    data: dict[str, Any],
    info: DagInfo,
    *,
    status: dict[str, Any] | None = None,
) -> None:
    """Validate the PR-119..166 intake without treating DAG state as science."""

    expected_ids = set(_pr_range(RESCUE_FIRST_PR, RESCUE_LAST_PR))
    advocate_ids = set(_pr_range(ADVOCATE_FIRST_PR, ADVOCATE_LAST_PR))
    actual_ids = set(info.ids)
    actual_rescue_ids = actual_ids & expected_ids
    if actual_rescue_ids != expected_ids:
        raise ValueError(
            "strict rescue slice must contain exactly PR-119..PR-166; "
            f"missing={sorted(expected_ids - actual_rescue_ids)}"
        )
    leaked_advocate = sorted(actual_ids & advocate_ids)
    if leaked_advocate:
        raise ValueError(f"PR-167 owns advocate intake; premature cards: {leaked_advocate}")
    if len(info.ids) != RESCUE_TOTAL_CARD_COUNT:
        raise ValueError(
            f"strict rescue slice expects {RESCUE_TOTAL_CARD_COUNT} total cards, "
            f"found {len(info.ids)}"
        )

    cards = {card["id"]: card for card in info.prs}
    for pr_id in _pr_range(RESCUE_FIRST_PR, RESCUE_LAST_PR):
        card = cards[pr_id]
        missing_fields = sorted(RESCUE_REQUIRED_FIELDS - set(card))
        if missing_fields:
            raise ValueError(f"{pr_id} missing rescue-card fields: {missing_fields}")
        owner = card.get("owner")
        if owner in RESCUE_FORBIDDEN_OWNERS or owner not in RESCUE_ACTIVE_OWNERS:
            raise ValueError(f"{pr_id} has forbidden or unknown active owner: {owner!r}")
        contributors = _require_string_list(card, "contributors")
        invalid_contributors = sorted(set(contributors) - RESCUE_ACTIVE_OWNERS)
        if invalid_contributors:
            raise ValueError(f"{pr_id} has invalid contributors: {invalid_contributors}")
        scopes = _require_string_list(card, "implementation_scopes")
        if not scopes or set(scopes) - RESCUE_IMPLEMENTATION_SCOPES:
            raise ValueError(f"{pr_id} has invalid implementation scopes: {scopes}")

        depends = _require_string_list(card, "depends")
        contracts = card.get("dependency_contracts")
        if not isinstance(contracts, list) or not all(
            isinstance(contract, dict) for contract in contracts
        ):
            raise ValueError(f"{pr_id} dependency_contracts must be a list of mappings")
        upstreams = [contract.get("upstream_id") for contract in contracts]
        if upstreams != depends:
            raise ValueError(
                f"{pr_id} typed dependency projection must exactly match depends: "
                f"{upstreams!r} != {depends!r}"
            )
        for contract in contracts:
            if set(contract) != {"upstream_id", "mode"}:
                raise ValueError(f"{pr_id} dependency contract has unknown fields: {contract}")
            if contract["mode"] not in RESCUE_EDGE_MODES:
                raise ValueError(f"{pr_id} has invalid dependency mode: {contract['mode']!r}")

        claim_level = card.get("claim_level")
        if not isinstance(claim_level, dict) or set(claim_level) != {"scheme", "level"}:
            raise ValueError(f"{pr_id} claim_level must contain explicit scheme and level")
        scheme = claim_level.get("scheme")
        level = claim_level.get("level")
        if scheme not in RESCUE_CLAIM_LEVELS or level not in RESCUE_CLAIM_LEVELS[scheme]:
            raise ValueError(f"{pr_id} has invalid versioned claim level: {claim_level}")
        if card.get("scientific_status_on_intake") != "OPEN":
            raise ValueError(f"{pr_id} scientific status must remain OPEN on intake")
        expected_activation = "DORMANT_EXTERNAL" if int(pr_id[-3:]) >= 159 else "PENDING"
        if card.get("activation_state") != expected_activation:
            raise ValueError(
                f"{pr_id} activation_state must be {expected_activation}, "
                f"found {card.get('activation_state')!r}"
            )
        for field in RESCUE_SEMANTIC_CLAIM_FIELDS:
            if field not in card:
                raise ValueError(f"{pr_id} missing semantic claim field: {field}")
            for prose in _iter_strings(card[field]):
                match = BARE_ACTIVE_CLAIM_LEVEL_RE.search(prose)
                if match:
                    raise ValueError(
                        f"{pr_id} {field} contains unqualified roadmap claim level "
                        f"{match.group(0)!r}"
                    )

    terminal_receipt_cards = {
        pr_id
        for pr_id in expected_ids
        if any(
            contract["mode"] == "requires_terminal_receipt"
            for contract in cards[pr_id]["dependency_contracts"]
        )
    }
    if terminal_receipt_cards != {"PR-157"}:
        raise ValueError(
            "requires_terminal_receipt is aggregation-only and restricted to PR-157; "
            f"found {sorted(terminal_receipt_cards)}"
        )
    adjudicated_cards = {
        pr_id
        for pr_id in expected_ids
        if any(
            contract["mode"] == "requires_adjudicated_claim_set"
            for contract in cards[pr_id]["dependency_contracts"]
        )
    }
    if adjudicated_cards != {"PR-158", "PR-166"}:
        raise ValueError(
            "adjudicated-claim edges must be restricted to PR-158 and PR-166; "
            f"found {sorted(adjudicated_cards)}"
        )
    external = cards["PR-159"].get("external_dependency_contracts")
    if external != [
        {
            "upstream_id": "AUTHENTICATED_NATIVE_DELIVERY",
            "mode": "requires_authenticated_external_receipt",
            "scope": "native_low_ell_delivery",
        }
    ]:
        raise ValueError(
            "PR-159 must retain the authenticated native-delivery gate with exact "
            "native_low_ell_delivery scope"
        )

    pr150_constraint = cards["PR-150"].get("execution_constraints")
    if pr150_constraint != PR150_EXECUTION_CONSTRAINT:
        raise ValueError("PR-150 must preserve the explicit PR3-complete/PR4-skip constraint")
    for field, expected in PR150_SEMANTIC_CONTRACT.items():
        if cards["PR-150"].get(field) != expected:
            raise ValueError(
                "PR-150 must unconditionally forbid all PR4/NPIPE download, reduction, "
                "analysis, and numeric/figure/combined outputs; canonical semantic "
                f"field drifted: {field}"
            )
    if cards["PR-150"].get("claim_level") != {
        "scheme": "roadmap_rescue_v1",
        "level": "C2",
    }:
        raise ValueError("PR-150 cannot retain the original joint PR3+PR4 C3 ceiling")

    if status is not None:
        _validate_rescue_status(status, info)


def render_mermaid(info: DagInfo) -> str:
    titles = {pr["id"]: str(pr.get("title", "")) for pr in info.prs}
    lines = ["flowchart TD"]
    for pr_id in info.order:
        node_id = pr_id.replace("-", "_")
        title = html.escape(titles.get(pr_id, ""), quote=True)
        lines.append(f'  {node_id}["{pr_id}<br/>{title}"]')
    for pr_id in info.order:
        for dep in info.prereqs[pr_id]:
            lines.append(f"  {dep.replace('-', '_')} --> {pr_id.replace('-', '_')}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("backlog")
    parser.add_argument("--status", metavar="PATH")
    parser.add_argument("--strict-rescue-slice", action="store_true")
    parser.add_argument("--write-mermaid", metavar="PATH")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        data = load_yaml(args.backlog)
        info = validate_backlog(data)
        if args.strict_rescue_slice:
            status = load_yaml(args.status) if args.status else None
            validate_long_horizon_rescue_slice(data, info, status=status)
        if args.write_mermaid:
            Path(args.write_mermaid).write_text(render_mermaid(info), encoding="utf-8")
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(
            json.dumps(
                {
                    "total": len(info.ids),
                    "edges": info.edge_count,
                    "topological_order": list(info.order),
                },
                indent=2,
            )
        )
    else:
        print(f"OK: {len(info.ids)} PRs, DAG valid")
        print("topological_order=" + ",".join(info.order))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
