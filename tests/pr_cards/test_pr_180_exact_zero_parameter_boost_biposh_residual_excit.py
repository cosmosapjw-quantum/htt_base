"""PR-180 card gates: exact zero-parameter boost-BiPoSH residual."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import healpy as hp
import numpy as np

REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from obsstat.boost_biposh_residual import (  # noqa: E402
    BoostBiposhConfig,
    DIPOLE_B_DEG,
    DIPOLE_L_DEG,
    _rotator,
)

SPEC = REPO / "docs/research_program/long_horizon_rescue/pr180_spec.yaml"
CARD = REPO / "docs/generated/pr180_result_card.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _card() -> dict:
    return json.loads(CARD.read_text())


def test_spec_bound_and_gates() -> None:
    card = _card()
    assert card["metadata"]["spec_sha256"] == _sha(SPEC)
    assert card["metadata"]["public_use"] is False
    assert card["metadata"]["claim_level"]["level"] == "C3"
    assert "frozen_before_result: true" in SPEC.read_text()
    assert "boosted_ffp10" in card["metadata"]["null_mock_status"]


def test_terminal_vocabulary_and_boundary_guard() -> None:
    card = _card()
    result = card["result"]
    allowed = {
        "CONSISTENT_WITH_PURE_BOOST_WITHIN_THIS_PIPELINE",
        "NOT_EXPLAINED_BY_THE_FIXED_BOOST_TEMPLATE_WITHIN_THIS_PIPELINE",
        "NUMERICALLY_UNRESOLVED_AT_CURRENT_MC_BUDGET",
        "BLOCKED_INTEGRITY_FAILURE",
    }
    assert card["terminal"] in allowed
    # boundary guard semantics: within one grid step of alpha never
    # resolves.
    p = result["rank_p"]
    step = result["finite_resolution_floor"]
    alpha = result["alpha"]
    if abs(p - alpha) <= step:
        assert card["terminal"] == "NUMERICALLY_UNRESOLVED_AT_CURRENT_MC_BUDGET"


def test_rank_semantics_exact_and_floored() -> None:
    result = _card()["result"]
    n = result["n_sims"]
    b = result["rank_exceedances"]
    assert result["rank_p"] == (1 + b) / (n + 1)
    assert result["rank_p"] >= result["finite_resolution_floor"]
    assert result["finite_resolution_floor"] == 1.0 / (n + 1)


def test_linearity_gate_and_template_resolved() -> None:
    result = _card()["result"]
    assert result["linearity_ok"] is True
    assert abs(result["linearity_ratio_f2h_over_fh"] - 2.0) <= 0.2
    template = result["template_operator_derived"]
    se = result["template_mc_se"]
    assert max(abs(t) / s for t, s in zip(template, se)) > 3.0


def test_identical_treatment_and_boosted_null_disclosed() -> None:
    joined = json.dumps(_card())
    assert "rank-invariant" in joined
    assert "boost" in joined
    assert "Richardson" in joined
    result = _card()["result"]
    assert "non-informative" in json.dumps(result).lower() or "not gated" in (
        result["ensemble_boost_content_note"]
    )


def test_dipole_frame_rotation_places_solar_dipole_on_z_axis() -> None:
    dipole = np.asarray(
        hp.rotator.dir2vec(
            DIPOLE_L_DEG,
            DIPOLE_B_DEG,
            lonlat=True,
        )
    )
    rotated = np.asarray(_rotator()(dipole))
    np.testing.assert_allclose(rotated, [0.0, 0.0, 1.0], atol=1e-14)

    nside = 8
    pixels = np.arange(hp.nside2npix(nside))
    directions = np.asarray(hp.pix2vec(nside, pixels)).T
    pure_dipole = directions @ dipole
    alm = hp.map2alm(pure_dipole, lmax=3, iter=3)
    rotated_alm = _rotator().rotate_alm(alm, lmax=3)
    a10 = rotated_alm[hp.Alm.getidx(3, 1, 0)]
    a11 = rotated_alm[hp.Alm.getidx(3, 1, 1)]
    assert abs(a11) <= 1e-9 * abs(a10)


def test_no_forbidden_claims() -> None:
    joined = json.dumps(_card()).lower()
    for token in ("detection of", "confirms the boost", "family identification",
                  "geometric estimand"):
        idx = 0
        while True:
            idx = joined.find(token, idx)
            if idx == -1:
                break
            prefix = joined[max(0, idx - 40):idx]
            assert "never" in prefix or "no " in prefix, (
                f"affirmative forbidden phrase: {token}"
            )
            idx += len(token)
    reaffirmed = " ".join(_card()["forbidden_claims_reaffirmed"])
    assert "never fitted" in reaffirmed


def test_frozen_card_is_detected_as_stale_after_frame_fix() -> None:
    assert _card()["metadata"]["config_hash"] != BoostBiposhConfig().config_hash()
    proc = subprocess.run(
        [
            str(REPO / "venv/bin/python"),
            "-B",
            str(REPO / "scripts/codex_harness/run_pr180_boost_residual.py"),
            "--check",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=900,
        env={
            "PYTHONHASHSEED": "0",
            "OPENBLAS_NUM_THREADS": "4",
            "PATH": "/usr/bin:/bin",
        },
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload == {
        "mode": "check",
        "ok": False,
        "read_only": True,
        "reason": "config_hash_mismatch",
    }
