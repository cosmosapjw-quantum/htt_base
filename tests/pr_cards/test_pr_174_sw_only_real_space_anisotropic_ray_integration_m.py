"""PR-174 card gates: SW-only anisotropic ray-integration mechanics.

Encodes the backlog DoD: (1) preregistered SW-only ray-integration
mechanics compared with an independent analytic fixture under a
no-likelihood firewall; (2) SW-only internal mechanics only — never a
native/external transfer or Boltzmann solution. Kill semantics: an
analytic mismatch blocks WITHOUT selecting the physically correct side;
any transfer registration, likelihood, or production consumer is a hard
failure.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt" / "src"))
sys.path.insert(0, str(REPO / "scripts" / "codex_harness"))

from common.pr174_sw_ray_tracer import (  # noqa: E402
    MUTATIONS,
    TERMINAL_CONSISTENT,
    TERMINAL_MISMATCH,
    Pr174Config,
    closed_form_ray_energy,
    direction_grid,
    linear_quadrupole_prediction,
    project_alm,
    real_harmonics,
    rk4_ray_energy,
    run_mechanics,
)
from run_pr174_sw_ray_tracer import firewall_scan  # noqa: E402

SPEC = REPO / "docs/research_program/long_horizon_rescue/pr174_spec.yaml"
RESULT_CARD = REPO / "docs/generated/pr174_result_card.json"
MUTATION_CARD = REPO / "docs/generated/pr174_mutation_report.json"
ENV = {
    "PYTHONHASHSEED": "0",
    "OPENBLAS_NUM_THREADS": "1",
    "OMP_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "PATH": "/usr/bin:/bin",
}


def _card() -> dict:
    return json.loads(RESULT_CARD.read_text())


def _mutation_card() -> dict:
    return json.loads(MUTATION_CARD.read_text())


def test_spec_is_frozen_and_card_binds_spec_hash() -> None:
    spec_sha = hashlib.sha256(SPEC.read_bytes()).hexdigest()
    card = _card()
    assert card["metadata"]["spec_sha256"] == spec_sha
    assert card["metadata"]["config_hash"] == Pr174Config().config_hash()
    assert "frozen_before_result: true" in SPEC.read_text()


def test_hypothesis_only_gates_and_forbidden_claims() -> None:
    for payload in (_card(), _mutation_card()):
        meta = payload["metadata"]
        assert meta["scientific_artifact_mode"] == "hypothesis_only"
        assert meta["public_use"] is False
        assert meta["transfer_source"] == "none"
        assert meta["claim_level"] == {
            "scheme": "roadmap_rescue_v1",
            "level": "C1",
        }
    reaffirmed = " ".join(_card()["forbidden_claims_reaffirmed"])
    for token in ("likelihood", "transfer", "Bessel", "C1"):
        assert token in reaffirmed


def test_firewall_clean_and_scan_detects_injected_violations(
    tmp_path: Path,
) -> None:
    live = firewall_scan()
    assert live["pass"] is True
    assert live["forbidden_import_hits"] == []
    assert live["production_consumers"] == []
    assert live["consumer_scan_scope"] == "repository_wide_minus_excluded_parts"

    bad_module = tmp_path / "bad_module.py"
    bad_module.write_text("from bass.los import anything\n")
    hit = firewall_scan(module=bad_module)
    assert hit["forbidden_import_hits"], "import scan must detect bass.los"
    assert hit["pass"] is False

    fake_root = tmp_path / "prod"
    fake_root.mkdir()
    (fake_root / "consumer.py").write_text(
        "from common.pr174_sw_ray_tracer import run_mechanics\n"
    )
    hit2 = firewall_scan(scan_roots=(fake_root,))
    assert hit2["production_consumers"], "consumer scan must detect imports"
    assert hit2["pass"] is False


def test_firewall_ast_scan_catches_evasive_imports(tmp_path: Path) -> None:
    """Line-continuation, dynamic, and non-whitelisted imports all hit."""
    cases = {
        "continuation.py": "import \\\n    healpy\n",
        "dunder.py": "mod = __import__('healpy')\n",
        "importlib_call.py": (
            "import importlib\nmod = importlib.import_module('healpy')\n"
        ),
        "whitelist.py": "import scipy\n",
    }
    for name, source in cases.items():
        bad = tmp_path / name
        bad.write_text(source)
        result = firewall_scan(module=bad)
        assert result["forbidden_import_hits"], f"scan missed {name}"
        assert result["pass"] is False


def test_config_validate_rejects_trace_violation_and_step_mismatch() -> None:
    import dataclasses

    import pytest as _pytest

    broken_trace = dataclasses.replace(
        Pr174Config(), b_vector=(2.0e-6, -0.5e-6, -1.0e-6)
    )
    with _pytest.raises(ValueError, match="trace condition"):
        broken_trace.validate()
    broken_steps = dataclasses.replace(Pr174Config(), steps_primary=512)
    with _pytest.raises(ValueError, match="steps_primary"):
        broken_steps.validate()


def test_docstring_mentions_are_not_import_hits() -> None:
    """Words like 'likelihood' in prose must not trip the import scan."""
    module = REPO / "htt/src/common/pr174_sw_ray_tracer.py"
    text = module.read_text().lower()
    assert "likelihood" in text  # present in prose by design
    assert firewall_scan()["forbidden_import_hits"] == []


def test_ray_level_matches_closed_form_and_rk4_order() -> None:
    config = Pr174Config()
    probe = np.array([0.6, -0.48, 0.64])
    probe = probe / math.sqrt(float(np.dot(probe, probe)))
    e_exact = closed_form_ray_energy(probe, config)
    errors = []
    for n_steps in config.steps_convergence:
        e_num = rk4_ray_energy(probe, config, n_steps)
        errors.append(abs(e_num - e_exact) / e_exact)
    assert errors[-1] <= config.ray_level_relative_energy_error_max
    order = math.log(errors[0] / errors[1]) / math.log(
        config.steps_convergence[1] / config.steps_convergence[0]
    )
    lo, hi = config.rk4_convergence_order_window
    assert lo <= order <= hi


def test_harmonic_table_is_orthonormal() -> None:
    config = Pr174Config()
    dirs, weights = direction_grid(config)
    table = real_harmonics(dirs, config.ell_max)
    keys = sorted(table)
    gram = np.array(
        [
            [float(np.sum(weights * table[a] * table[b])) for b in keys]
            for a in keys
        ]
    )
    assert np.max(np.abs(gram - np.eye(len(keys)))) < 1.0e-13


def test_linear_pattern_projection_reproduces_closed_form_coefficients() -> None:
    """Quadrature of the linear pattern must match the analytic a_2m."""
    config = Pr174Config()
    dirs, weights = direction_grid(config)
    delta_beta = np.array(
        [b * (1.0 - config.t_emit_over_t0) for b in config.b_vector]
    )
    pattern = -(dirs**2 - 1.0 / 3.0) @ delta_beta
    alm = project_alm(pattern, dirs, weights, 2)
    predicted = linear_quadrupole_prediction(config)
    scale = max(abs(v) for v in predicted.values())
    for key, value in predicted.items():
        assert abs(alm[key] - value) / scale < 1.0e-12


def test_result_card_terminal_and_tolerances() -> None:
    card = _card()
    mech = card["mechanics"]
    assert mech["terminal"] == TERMINAL_CONSISTENT
    assert all(mech["checks"].values())
    config = Pr174Config()
    assert (
        mech["max_ray_relative_energy_error"]
        <= config.ray_level_relative_energy_error_max
    )
    assert (
        mech["max_quadrupole_relative_error"]
        <= config.quadrupole_relative_match_max
    )
    assert mech["odd_ell_relative_power"] <= config.odd_ell_relative_power_max
    assert (
        mech["monopole_dipole_residual_relative_power"]
        <= config.monopole_dipole_residual_relative_max
    )


def test_mismatch_terminal_is_unattributed() -> None:
    assert "UNATTRIBUTED" in TERMINAL_MISMATCH
    interpretation = _card()["mechanics"]["interpretation"]
    assert "never selects" in interpretation


def test_mutation_report_all_killed_on_registered_guards() -> None:
    battery = _mutation_card()["battery"]
    assert battery["all_killed"] is True
    assert set(battery["mutations"]) == set(MUTATIONS)
    for row in battery["mutations"].values():
        assert row["killed"] is True
        assert row["guard_check_failed"] is True
        assert row["terminal"] == TERMINAL_MISMATCH


def test_single_mutation_demonstrated_live() -> None:
    """One mutant exercised in-process (not only via the stored card)."""
    config = Pr174Config()
    entry = MUTATIONS["MUT-174-PARITY"]
    result = run_mechanics(config, **entry["kwargs"])
    assert result["checks"]["odd_ell_parity"] is False
    assert result["terminal"] == TERMINAL_MISMATCH


def test_status_not_pending_and_lane_is_hypothesis_only() -> None:
    status = (REPO / "docs/codex_handoff/pr_status.yaml").read_text()
    pending_block = status.split("pending:")[1].split("dormant_external:")[0]
    assert "PR-174" not in pending_block
    assert "PR-174: hypothesis_only" in status


def test_result_pack_is_byte_current_under_read_only_check() -> None:
    proc = subprocess.run(
        [
            str(REPO / "venv/bin/python"),
            "-B",
            str(REPO / "scripts/codex_harness/run_pr174_sw_ray_tracer.py"),
            "--check",
        ],
        cwd=REPO,
        env=ENV,
        capture_output=True,
        text=True,
        timeout=900,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["ok"] is True
    assert payload["read_only"] is True
    assert payload["terminal"] == TERMINAL_CONSISTENT
