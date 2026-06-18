from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_script(name: str):
    path = REPO_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_canonical_formalism_rows_pass_registry():
    module = _load_script("verify_formalism_figure_labels")
    display_metadata = {
        "requires_sector_profile": True,
        "requires_absolute_component_total": True,
        "requires_cancellation_index": True,
        "requires_magnitude_companion_M": True,
        "interpretation": "near-zero x_C can reflect cancellation, not isotropy",
    }
    rows = [
        {
            "symbol": "x",
            "owner": "MIO",
            "definition": "raw diagnostic departure scalar in the stress payload",
            "display_metadata": display_metadata,
        },
        {
            "symbol": "Q",
            "owner": "MIO",
            "definition": "x divided by explicit denominator policy",
        },
        {
            "symbol": "Pi",
            "owner": "MIO",
            "definition": "exceedance curve over explicit threshold grid for Q samples",
        },
        {
            "symbol": "F",
            "owner": "MIO",
            "definition": "certified filling fraction under sign-clean admissible ceiling",
            "display_metadata": display_metadata,
        },
        {
            "symbol": "G_F",
            "owner": "MIO",
            "definition": "depth-gap diagnostic with depth-bin metadata and null calibration",
        },
        {
            "symbol": "Q-spread",
            "owner": "MIO",
            "definition": "inter-policy spread across current denominator policies",
        },
    ]

    assert module.validate_rows(rows) == []


def test_x_and_f_rows_require_cancellation_display_metadata():
    module = _load_script("verify_formalism_figure_labels")

    rows = [
        {
            "symbol": "x",
            "owner": "MIO",
            "definition": "raw diagnostic departure scalar",
        },
        {
            "symbol": "F",
            "owner": "MIO",
            "definition": "certified filling fraction under sign-clean admissible ceiling",
            "display_metadata": {
                "requires_sector_profile": True,
                "requires_absolute_component_total": True,
                "requires_cancellation_index": True,
                "interpretation": "signed projection fraction",
            },
        },
    ]

    issue_keys = {
        (issue.symbol, issue.issue_type) for issue in module.validate_rows(rows)
    }

    assert ("x", "missing_cancellation_display_metadata") in issue_keys
    assert ("F", "missing_magnitude_companion_metadata") in issue_keys
    assert ("F", "unsafe_cancellation_interpretation") in issue_keys


def test_current_audit_failure_rows_are_rejected():
    module = _load_script("verify_formalism_figure_labels")
    rows = [
        {
            "symbol": "Pi",
            "label": "policy spread",
            "owner": "MIO",
            "definition": "inter-policy spread across current denominator policies",
        },
        {
            "symbol": "F",
            "label": "local-null survival",
            "owner": "HTT",
            "definition": "one minus look-elsewhere adjusted local-null FPR",
        },
        {
            "symbol": "G_F",
            "label": "depth response",
            "owner": "HTT",
            "definition": "normalized log depth-response envelope from null-bank payload",
        },
    ]

    issues = module.validate_rows(rows)
    issue_keys = {(issue.symbol, issue.issue_type) for issue in issues}

    assert ("Pi", "definition_mismatch") in issue_keys
    assert ("F", "owner_mismatch") in issue_keys
    assert ("F", "definition_mismatch") in issue_keys
    assert ("G_F", "owner_mismatch") in issue_keys
    assert ("G_F", "definition_mismatch") in issue_keys


def test_cli_exits_nonzero_for_formalism_label_mismatch(tmp_path: Path):
    payload_path = tmp_path / "payload.json"
    payload_path.write_text(
        json.dumps(
            {
                "semantic_and_vectors": {
                    "semantic_split": [
                        {
                            "symbol": "F",
                            "owner": "HTT",
                            "definition": "one minus look-elsewhere adjusted local-null FPR",
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "verify_formalism_figure_labels.py"),
            str(payload_path),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "owner_mismatch" in combined
    assert "definition_mismatch" in combined


def test_checked_in_current_science_payload_has_no_canonical_label_mismatch():
    module = _load_script("verify_formalism_figure_labels")
    payload = json.loads(
        (REPO_ROOT / "docs" / "generated" / "current_science_plot_payload.json").read_text(
            encoding="utf-8"
        )
    )

    assert module.validate_payload(payload) == []


def test_current_payload_has_r066_departure_display_contract():
    payload = json.loads(
        (REPO_ROOT / "docs" / "generated" / "current_science_plot_payload.json").read_text(
            encoding="utf-8"
        )
    )

    contract = payload["semantic_and_vectors"]["departure_display_contract"]
    assert contract["required_for_symbols"] == ["x", "F"]
    assert contract["requires_sector_profile"] is True
    assert contract["requires_absolute_component_total"] is True
    assert contract["requires_cancellation_index"] is True
    assert contract["requires_magnitude_companion_M"] is True

    counter = payload["semantic_and_vectors"]["cancellation_counterexample"]
    assert counter["x_C"] == pytest.approx(0.0)
    assert counter["absolute_component_total"] > 0.0
    assert counter["cancellation_index"] == pytest.approx(1.0)
    assert counter["M_sector_magnitude"] > 0.0
    assert "not isotropy" in counter["interpretation"]
