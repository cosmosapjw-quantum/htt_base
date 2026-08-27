from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]


def test_coordinate_audit_emits_objective_outputs_and_factorial(tmp_path: Path) -> None:
    output = tmp_path / "audit"
    subprocess.run(
        [
            sys.executable,
            "scripts/observed_runs/run_planck_mes_coordinate_audit.py",
            "--output-dir",
            str(output),
        ],
        cwd=ROOT,
        check=True,
    )
    required = {
        "result.json", "replay.json", "terminal.json", "factorial_table.csv",
        "tail_table.csv", "tie_dependence_table.csv", "epsilon1_sensitivity.csv",
        "figure_factorial_ladder.pdf", "figure_reducer_comparison.pdf",
        "figure_epsilon1_sensitivity.pdf", "plot_audit.json",
    }
    assert {path.name for path in output.iterdir()} == required
    result = json.loads((output / "result.json").read_text())
    assert result["row_count"] == 301
    assert set(result["factorial_cells"]) == {
        "LEGACY_ABSOLUTE_MEDIAN_V1", "LOO_ECDF_MIDRANK_V1"
    }
    for reducer_cells in result["factorial_cells"].values():
        assert set(reducer_cells) == {
            "EPS_LINEAR", "SQUARE_ONLY", "CARRIER_ONLY", "MES_SQUARED"
        }
    for reducer_contrasts in result["contrasts"].values():
        assert set(reducer_contrasts) == {
            "square_without_mix", "square_with_mix", "mix_linear",
            "mix_squared", "interaction",
        }
    assert result["frozen_baseline"]["MES_SQUARED_legacy_rank"] == "98/301"
    assert result["claim_tier"] == "methods_diagnostic"
    assert result["raw_maps_reopened"] is False


def test_committed_coordinate_audit_replay() -> None:
    subprocess.run(
        [sys.executable, "scripts/observed_runs/run_planck_mes_coordinate_audit.py", "--replay-committed"],
        cwd=ROOT,
        check=True,
    )
