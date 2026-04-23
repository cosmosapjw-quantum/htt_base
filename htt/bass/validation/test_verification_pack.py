"""v5 design-pack verification bundle tests.

Two variants:

* ``@pytest.mark.ci`` — fast, no subprocess, no filesystem writes. Loads
  the three frozen JSONs under ``docs/bianchi_design_pack_v5/verification/``
  and asserts structural + numeric invariants. Safe for every push.
* ``@pytest.mark.slow`` — subprocess-reruns
  ``docs/bianchi_design_pack_v5/verification/run_all_verifications.py``
  and confirms the regenerated bundle still passes. Expected cost: a few
  seconds (sympy + mpmath heavy).

Markers: ``verification``, plus one of ``ci`` or ``slow``.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_V5_VERIFICATION_DIR = _REPO_ROOT / "docs" / "bianchi_design_pack_v5" / "verification"
_CROSSCHECK = _V5_VERIFICATION_DIR / "crosscheck_results.json"
_SYMBOLIC = _V5_VERIFICATION_DIR / "symbolic_results.json"
_NUMERIC = _V5_VERIFICATION_DIR / "numeric_results.json"
_RUN_ALL = _V5_VERIFICATION_DIR / "run_all_verifications.py"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.verification
@pytest.mark.ci
def test_verification_dir_present() -> None:
    assert _V5_VERIFICATION_DIR.is_dir(), (
        f"v5 verification dir missing: {_V5_VERIFICATION_DIR}"
    )
    for p in (_CROSSCHECK, _SYMBOLIC, _NUMERIC, _RUN_ALL):
        assert p.is_file(), f"expected file missing: {p}"


@pytest.mark.verification
@pytest.mark.ci
def test_crosscheck_bundle_shape_and_pass() -> None:
    bundle = _load_json(_CROSSCHECK)
    for required in ("crosscheck_pass", "symbolic_zero_checks", "numeric_bounds"):
        assert required in bundle, f"crosscheck_results.json missing '{required}'"
    assert bundle["crosscheck_pass"] is True, (
        "v5 crosscheck_pass != True — rerun run_all_verifications.py and "
        "investigate which symbolic/numeric check regressed."
    )
    symbolic = bundle["symbolic_zero_checks"]
    assert isinstance(symbolic, dict) and len(symbolic) >= 1
    for key, value in symbolic.items():
        assert value is True, f"symbolic zero check failed: {key}"


@pytest.mark.verification
@pytest.mark.ci
def test_numeric_bounds_within_tolerance() -> None:
    bundle = _load_json(_CROSSCHECK)
    bounds = bundle["numeric_bounds"]
    # Per docs/bianchi_design_pack_v5/verification/README, these are frozen
    # absolute-error ceilings for the symbolic → numeric crosscheck.
    tolerances = {
        "classB_max_abs_err": 1.0e-12,
        "typeVIII_specialcase_max_abs_err": 1.0e-60,
        "fd_max_abs_err": 1.0e-60,
    }
    for key, ceiling in tolerances.items():
        if key not in bounds:
            continue
        assert bounds[key] < ceiling, (
            f"numeric bound '{key}' = {bounds[key]!r} exceeds ceiling {ceiling!r}"
        )
    if "typeVIII_min_val" in bounds:
        assert bounds["typeVIII_min_val"] > 0.0


@pytest.mark.verification
@pytest.mark.ci
def test_symbolic_and_numeric_json_parse() -> None:
    sym = _load_json(_SYMBOLIC)
    num = _load_json(_NUMERIC)
    assert isinstance(sym, dict) and isinstance(num, dict)
    assert len(sym) >= 1
    assert len(num) >= 1


@pytest.mark.verification
@pytest.mark.ci
def test_family_backend_loader_agrees_with_bundle() -> None:
    """The live loader used by family_backend_protocol.py must agree with
    the on-disk bundle. Guards against an import-time copy going stale."""
    from bass.los.family_backend_protocol import _V5_VERIFICATION_BUNDLE

    on_disk = _load_json(_CROSSCHECK)
    assert _V5_VERIFICATION_BUNDLE.get("load_status") == "loaded"
    assert _V5_VERIFICATION_BUNDLE.get("crosscheck_pass") == on_disk["crosscheck_pass"]


@pytest.mark.verification
@pytest.mark.slow
def test_run_all_verifications_subprocess() -> None:
    """Rerun the v5 verification pack end-to-end and assert it still passes.

    This is the only test that regenerates ``run_all_stdout.json`` and the
    three ``*_results.json`` files in-place. Run it locally before tagging
    a release; CI can skip via ``-m 'not slow'``.
    """
    proc = subprocess.run(
        [sys.executable, str(_RUN_ALL)],
        capture_output=True,
        text=True,
        cwd=str(_V5_VERIFICATION_DIR),
        check=False,
    )
    assert proc.returncode == 0, (
        f"run_all_verifications.py exited {proc.returncode}.\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    assert _load_json(_CROSSCHECK)["crosscheck_pass"] is True
