from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest


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
        for record in reducer_cells.values():
            assert record["global_rank"] == (
                f"{record['global_rank_numerator']}/{record['rank_denominator']}"
            )
    for reducer_contrasts in result["contrasts"].values():
        assert set(reducer_contrasts) == {
            "square_without_mix", "square_with_mix", "mix_linear",
            "mix_squared", "interaction",
        }
    assert result["frozen_baseline"]["MES_SQUARED_legacy_rank"] == "98/301"
    assert result["claim_tier"] == "methods_diagnostic"
    assert result["raw_maps_reopened"] is False
    assert set(result["dependence_diagnostics"]) == {
        "EPS_LINEAR", "SQUARE_ONLY", "CARRIER_ONLY", "MES_SQUARED"
    }
    with (output / "tie_dependence_table.csv").open(newline="") as handle:
        dependence_rows = list(csv.DictReader(handle))
    assert len(dependence_rows) == 80
    assert {row["diagnostic_kind"] for row in dependence_rows} == {
        "coordinate_duplicate_count", "spearman_eigenvalue"
    }
    for cell, diagnostic in result["dependence_diagnostics"].items():
        rows = [row for row in dependence_rows if row["cell"] == cell]
        tie_rows = [
            row for row in rows
            if row["diagnostic_kind"] == "coordinate_duplicate_count"
        ]
        spectrum_rows = [
            row for row in rows
            if row["diagnostic_kind"] == "spearman_eigenvalue"
        ]
        assert len(tie_rows) == len(spectrum_rows) == 10
        assert all(row["coordinate_index"] and not row["spectrum_index"] for row in tie_rows)
        assert all(row["spectrum_index"] and not row["coordinate_index"] for row in spectrum_rows)
        assert [int(row["duplicate_count"]) for row in tie_rows] == diagnostic[
            "coordinate_duplicate_counts"
        ]
        assert [
            float(row["spearman_eigenvalue_descending"])
            for row in spectrum_rows
        ] == diagnostic["spearman_eigenvalues_descending"]
        eigenvalues = np.asarray(diagnostic["spearman_eigenvalues_descending"])
        expected = float(eigenvalues.sum() ** 2 / np.square(eigenvalues).sum())
        assert diagnostic["spearman_participation_ratio"] == pytest.approx(expected)
    plot_audit = json.loads((output / "plot_audit.json").read_text())
    assert plot_audit["inspection_state"] == "PENDING_EXTERNAL_DIRECT_INSPECTION"
    assert "PASS" not in json.dumps(plot_audit)
    assert set(plot_audit["figures"]) == {
        "figure_factorial_ladder.pdf", "figure_reducer_comparison.pdf",
        "figure_epsilon1_sensitivity.pdf",
    }
    for audit in plot_audit["figures"].values():
        assert audit["single_column_3.3in"]["status"] == "PENDING"
        assert audit["double_column_6.8in"]["status"] == "PENDING"


def test_committed_plot_audit_is_external_and_content_bound() -> None:
    result = json.loads(
        (ROOT / "docs/generated/planck_mes_coordinate_audit/result.json").read_text()
    )
    audit = json.loads(
        (ROOT / "docs/generated/planck_mes_coordinate_audit/plot_audit.json").read_text()
    )
    assert audit["inspection_state"] == "PASSED_EXTERNAL_DIRECT_INSPECTION"
    assert audit["inspection_origin"] == "EXTERNAL_DIRECT_VISUAL_REVIEW"
    assert audit["source"]["result_content_id"] == result["content_id"]
    for figure, record in audit["figures"].items():
        assert len(record["git_blob_sha"]) == 40
        assert record["single_column_3.3in"]["status"] == "PASS"
        assert record["double_column_6.8in"]["status"] == "PASS"
        assert figure.endswith(".pdf")


def test_committed_coordinate_audit_replay() -> None:
    subprocess.run(
        [sys.executable, "scripts/observed_runs/run_planck_mes_coordinate_audit.py", "--replay-committed"],
        cwd=ROOT,
        check=True,
    )
