from __future__ import annotations

import json
from pathlib import Path

import pytest

from check_import_boundaries import assess_edges, check_repository


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_current_repository_import_boundaries() -> None:
    result = check_repository(REPO_ROOT)
    assert result["status"] == "PASS", json.dumps(
        result,
        indent=2,
        sort_keys=True,
    )


@pytest.mark.parametrize(
    ("nodes", "edges", "allowed", "baseline_violations", "baseline_sccs", "kind"),
    [
        (
            frozenset({"common", "htt"}),
            frozenset({("common", "htt")}),
            frozenset({("htt", "common")}),
            frozenset(),
            (),
            "new_forbidden_edge",
        ),
        (
            frozenset({"bass", "htt", "mio"}),
            frozenset(
                {
                    ("bass", "htt"),
                    ("htt", "bass"),
                    ("htt", "mio"),
                    ("mio", "bass"),
                }
            ),
            frozenset(
                {
                    ("htt", "bass"),
                    ("htt", "mio"),
                    ("mio", "bass"),
                }
            ),
            frozenset({("bass", "htt")}),
            (frozenset({"bass", "htt"}),),
            "scc_growth",
        ),
    ],
)
def test_boundary_mutations_fail_closed(
    nodes: frozenset[str],
    edges: frozenset[tuple[str, str]],
    allowed: frozenset[tuple[str, str]],
    baseline_violations: frozenset[tuple[str, str]],
    baseline_sccs: tuple[frozenset[str], ...],
    kind: str,
) -> None:
    findings = assess_edges(
        nodes=nodes,
        edges=edges,
        allowed_edges=allowed,
        baseline_violations=baseline_violations,
        baseline_sccs=baseline_sccs,
    )
    assert any(finding["kind"] == kind for finding in findings)


def test_removing_a_grandfathered_edge_is_allowed() -> None:
    findings = assess_edges(
        nodes=frozenset({"bass", "htt"}),
        edges=frozenset({("htt", "bass")}),
        allowed_edges=frozenset({("htt", "bass")}),
        baseline_violations=frozenset({("bass", "htt")}),
        baseline_sccs=(frozenset({"bass", "htt"}),),
    )
    assert findings == []
