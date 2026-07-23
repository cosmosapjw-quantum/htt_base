"""Track-II native gate: synthetic fixture must exit-3 under --require-native."""
from __future__ import annotations
import sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_solver_gate import synthetic_interface_fixture, validate  # noqa: E402

def test_synthetic_requires_native_exit_3():
    r = validate(synthetic_interface_fixture(), require_native=True)
    assert r["exit_code"] == 3 and r["status"] == "EXPECTED_BLOCK"
    assert not r["scientific_track_ii_ready"]

def test_synthetic_interface_only_ok_without_native():
    r = validate(synthetic_interface_fixture(), require_native=False)
    assert r["status"] == "PASS" and r["interface_ok"]

def test_real_native_delivery_would_pass():
    real = synthetic_interface_fixture()
    real.update(native=True, error_model={"validated": True},
                benchmarks={k: True for k in
                            ("flrw_null","bianchi_i_temperature","polarization","independent_oracle")})
    r = validate(real, require_native=True)
    assert r["exit_code"] == 0 and r["scientific_track_ii_ready"]
