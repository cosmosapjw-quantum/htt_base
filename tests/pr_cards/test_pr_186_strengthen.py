"""Live W2 convention regression after retirement of the PR-186 report card."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.w2_convention import (  # noqa: E402
    ceiling_conversion_symbolic,
    scan_active_sources,
    vorticity_tensor_vector_identity,
)

def test_tensor_vector_identity() -> None:
    r = vorticity_tensor_vector_identity(100_000)
    assert r["ok"] and r["max_abs_error"] < 1e-12


def test_symbolic_convention_and_ceiling() -> None:
    s = ceiling_conversion_symbolic()
    assert s["tensor_vector_forms_equal"] is True
    assert s["W2_registered"] == "wa2/(3*H**2)"
    assert s["wrong_over_right_ratio"] == "3"
    assert s["ceiling_is_three_halves_Bsq"] is True


def test_active_sources_clean() -> None:
    scan = scan_active_sources(REPO)
    assert scan["clean"], scan["active_bad_pattern_hits"][:5]
    assert scan["n_hits"] == 0


def test_read_only_check_does_not_recreate_the_retired_card() -> None:
    retired = REPO / "docs/generated/pr186_result_card.json"
    assert not retired.exists()
    proc = subprocess.run(
        [sys.executable, "-B",
         str(REPO / "scripts/codex_harness/run_pr186_w2_convention.py"), "--check"],
        cwd=REPO, capture_output=True, text=True, timeout=600,
        env={"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin"},
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["ok"] is True
    assert payload["read_only"] is True
    assert payload["claim_promotion"] is False
    assert not retired.exists()
