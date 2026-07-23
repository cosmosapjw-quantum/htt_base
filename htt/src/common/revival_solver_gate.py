"""Track-II native solver delivery gate (PR-229 opening condition).

Track II (PR-229..242) consumes native Bianchi Boltzmann solver output. Until a
real, content-addressed SolverDeliveryReceipt is supplied, every Track-II
scientific command is BLOCKED (exit 3). The synthetic interface fixture is
intentionally insufficient and MUST return exit 3 under --require-native. Track
II never dilutes Track I's source/covariance/coverage gates.
"""
from __future__ import annotations

REQUIRED = ("schema_version", "release_hash", "source_commit", "environment_hash",
            "native", "benchmarks", "error_model")
REQUIRED_BENCHMARKS = ("flrw_null", "bianchi_i_temperature", "polarization", "independent_oracle")


def validate(card: dict, require_native: bool = False) -> dict:
    missing = [k for k in REQUIRED if k not in card]
    interface_ok = (not missing
                    and all(k in card.get("benchmarks", {}) for k in REQUIRED_BENCHMARKS))
    science_ok = (interface_ok and bool(card.get("native"))
                  and all(card.get("benchmarks", {}).values())
                  and card.get("error_model", {}).get("validated") is True)
    if require_native:
        status = "PASS" if science_ok else ("EXPECTED_BLOCK" if interface_ok else "FAIL")
        exit_code = 0 if science_ok else (3 if interface_ok else 2)
    else:
        status = "PASS" if interface_ok else "FAIL"
        exit_code = 0 if interface_ok else 2
    return {"status": status, "exit_code": exit_code, "interface_ok": interface_ok,
            "scientific_track_ii_ready": science_ok, "missing": missing}


def synthetic_interface_fixture() -> dict:
    """Intentionally insufficient: parses as an interface but native=False."""
    return {
        "schema_version": "1", "release_hash": "synthetic", "source_commit": "none",
        "environment_hash": "none", "native": False,
        "benchmarks": {"flrw_null": False, "bianchi_i_temperature": False,
                       "polarization": False, "independent_oracle": False},
        "error_model": {"validated": False},
    }
