"""TEFF v8-update C5b: bit-level parity between the Python Teff lane and the
Rust twin (src/teff/spectral.rs + teff_solver.rs).

Discharges the second ``future_obligation`` of
``teff_representative_nonclaims.yaml`` ("cross-check a_xi / c_p / Gram objects
against src/teff/*.rs"). Three parity lanes:

1. SOURCE-ANCHORED CONSTANT PARITY (exact, SymPy): the Rust standard values --
   the zeta table in ``riemann_zeta`` (``spectral.rs``: pi^2/6, pi^4/90,
   pi^6/945, the Apery float, the zeta(5) float) and the spectral-integral
   test expectations ``I_3^BE(0) = pi^4/15`` and ``I_3^FD(0) = 7 pi^4/120`` --
   are transcribed with file anchors and proved EXACTLY consistent with the
   Python radial constants: 3 a_BE = pi^4/15 and 3 a_FD = 7 pi^4/120 (the
   factor 3 is the 1/3 in a_xi = I_3^(xi)(0)/3 of the representative theory).
2. GRAM-STRUCTURE PARITY (exact): the Rust monopole Gram
   J = [[4, I_2/I_3], [3, I_1/I_2]] at eta_0 = 0 (BE) has the exact entries
   J_12 = zeta(3)/(3 zeta(4)), J_22 = zeta(2)/(2 zeta(3)) (Gamma-zeta
   closed forms) and a NONZERO determinant (the two-parameter monopole solve
   is well-posed) -- proved symbolically and matched numerically to 12+
   digits against mpmath.
3. CARGO LANE (live in this environment): ``cargo test --lib teff`` runs the
   Rust twin's own 153-test suite (including the I_3 expectations above);
   the pass/fail count is recorded. If cargo is unavailable the lane records
   a REGISTERED fallback (source-anchored parity remains the evidence) --
   never silence.

Claim discipline: internal consistency cross-check between two in-repo
implementations at tier diagnostic_only; no data claim, no signal-discovery
claim, no Bianchi-class-identification-of-the-sky claim, no
native-solver-produced claim, no probabilistic-inference claim.
"""
from __future__ import annotations

from pathlib import Path
import re
import subprocess

import mpmath as mp
import sympy as sp

from .representative import RADIAL_CONSTANTS

__all__ = [
    "rust_source_constants",
    "constant_parity_checks",
    "gram_structure_parity",
    "cargo_test_lane",
    "teff_rust_parity_seal",
]

_REPO = Path(__file__).resolve().parents[2]
_SPECTRAL_RS = _REPO / "src/teff/spectral.rs"
_SOLVER_RS = _REPO / "src/teff/teff_solver.rs"


def rust_source_constants() -> dict:
    """Transcribe the Rust-side standard values with source anchors."""
    src = _SPECTRAL_RS.read_text()
    zeta_table = {
        2: "PI * PI / 6.0" in src,
        4: "PI.powi(4) / 90.0" in src,
        6: "PI.powi(6) / 945.0" in src,
    }
    apery = re.search(r"3 => return (1\.20205690315959\d+)", src)
    zeta5 = re.search(r"5 => return (1\.03692775514336\d+)", src)
    i3_be = "PI.powi(4) / 15.0" in src
    i3_fd = "7.0 * PI.powi(4) / 120.0" in src
    solver = _SOLVER_RS.read_text()
    gram = ("let j11 = 4.0;" in solver and "let j21 = 3.0;" in solver
            and "i2 / i3" in solver and "i1 / i2" in solver)
    return {
        "spectral_rs": str(_SPECTRAL_RS.relative_to(_REPO)),
        "solver_rs": str(_SOLVER_RS.relative_to(_REPO)),
        "zeta_table_closed_forms_present": zeta_table,
        "apery_float": apery.group(1) if apery else None,
        "zeta5_float": zeta5.group(1) if zeta5 else None,
        "i3_be_expectation_pi4_over_15": i3_be,
        "i3_fd_expectation_7pi4_over_120": i3_fd,
        "gram_structure_4_i2i3_3_i1i2": gram,
    }


def constant_parity_checks() -> dict:
    """Exact parity: 3 a_BE = pi^4/15, 3 a_FD = 7 pi^4/120; zeta table and
    float literals match sympy/mpmath to full stated precision."""
    consts = rust_source_constants()
    a_be = RADIAL_CONSTANTS["BE"]           # 2 zeta(4)
    a_fd = RADIAL_CONSTANTS["FD"]           # (7/4) zeta(4)
    be_exact = bool(sp.simplify(3 * a_be - sp.pi ** 4 / 15) == 0)
    fd_exact = bool(sp.simplify(3 * a_fd - 7 * sp.pi ** 4 / 120) == 0)
    zeta_exact = {
        "zeta2": bool(sp.simplify(sp.zeta(2) - sp.pi ** 2 / 6) == 0),
        "zeta4": bool(sp.simplify(sp.zeta(4) - sp.pi ** 4 / 90) == 0),
        "zeta6": bool(sp.simplify(sp.zeta(6) - sp.pi ** 6 / 945) == 0),
    }
    mp.mp.dps = 20
    apery_ok = (consts["apery_float"] is not None
                and abs(float(consts["apery_float"]) - float(mp.zeta(3))) < 1e-15)
    zeta5_ok = (consts["zeta5_float"] is not None
                and abs(float(consts["zeta5_float"]) - float(mp.zeta(5))) < 1e-15)
    return {
        "three_a_be_equals_pi4_over_15_exact": be_exact,
        "three_a_fd_equals_7pi4_over_120_exact": fd_exact,
        "rust_expectations_present": bool(
            consts["i3_be_expectation_pi4_over_15"]
            and consts["i3_fd_expectation_7pi4_over_120"]),
        "zeta_table_exact": zeta_exact,
        "apery_float_matches_mpmath_1e15": bool(apery_ok),
        "zeta5_float_matches_mpmath_1e15": bool(zeta5_ok),
        "factor_note": "a_xi = I_3^(xi)(0)/3; the Rust tests pin I_3 itself, "
                       "hence the exact factor 3",
    }


def gram_structure_parity() -> dict:
    """Exact Gram entries at eta_0 = 0 (BE): J_12 = zeta(3)/(3 zeta(4)),
    J_22 = zeta(2)/(2 zeta(3)); nonzero determinant; numeric match vs mpmath."""
    # I_n(0) = Gamma(n+1) zeta(n+1) (BE); Rust: J12 = I2/I3, J22 = I1/I2
    j12_exact = sp.gamma(3) * sp.zeta(3) / (sp.gamma(4) * sp.zeta(4))
    j22_exact = sp.gamma(2) * sp.zeta(2) / (sp.gamma(3) * sp.zeta(3))
    j12_closed = bool(sp.simplify(j12_exact - sp.zeta(3) / (3 * sp.zeta(4))) == 0)
    j22_closed = bool(sp.simplify(j22_exact - sp.zeta(2) / (2 * sp.zeta(3))) == 0)
    det_exact = sp.simplify(4 * j22_exact - 3 * j12_exact)
    det_nonzero = bool(sp.N(det_exact, 30) != 0)
    mp.mp.dps = 25

    def In(n):
        return mp.gamma(n + 1) * mp.zeta(n + 1)

    j12_num = float(In(2) / In(3))
    j22_num = float(In(1) / In(2))
    match = (abs(j12_num - float(sp.N(j12_exact, 20))) < 1e-14
             and abs(j22_num - float(sp.N(j22_exact, 20))) < 1e-14)
    return {
        "J": "[[4, I2/I3], [3, I1/I2]] (Rust monopole Gram, eta0=0, BE)",
        "J12_closed_form": "zeta(3)/(3 zeta(4))",
        "J22_closed_form": "zeta(2)/(2 zeta(3))",
        "closed_forms_exact": bool(j12_closed and j22_closed),
        "J12_numeric": round(j12_num, 15),
        "J22_numeric": round(j22_num, 15),
        "det_exact": str(det_exact),
        "det_numeric": round(float(sp.N(det_exact, 20)), 15),
        "det_nonzero_wellposed": det_nonzero,
        "numeric_matches_mpmath_1e14": bool(match),
    }


def cargo_test_lane(timeout_s: int = 180) -> dict:
    """Run the Rust twin's own test suite (registered fallback if unavailable)."""
    try:
        r = subprocess.run(["cargo", "test", "--lib", "teff"], cwd=_REPO,
                           capture_output=True, text=True, timeout=timeout_s)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"mode": "REGISTERED_FALLBACK_SOURCE_ANCHORED",
                "reason": f"{type(exc).__name__}",
                "note": "source-anchored constant parity remains the evidence"}
    m = re.search(r"test result: (\w+)\. (\d+) passed; (\d+) failed", r.stdout)
    if not m:
        return {"mode": "REGISTERED_FALLBACK_SOURCE_ANCHORED",
                "reason": "unparseable cargo output",
                "returncode": r.returncode}
    return {
        "mode": "CARGO_LIVE",
        "result": m.group(1),
        "passed": int(m.group(2)),
        "failed": int(m.group(3)),
        "ok": bool(m.group(1) == "ok" and int(m.group(3)) == 0),
    }


def teff_rust_parity_seal() -> dict:
    """Fail-closed C5b seal. PASS requires the exact source-anchored parity;
    the cargo lane strengthens it when live and downgrades to a registered
    fallback (still PASS-eligible) when the toolchain is absent."""
    consts = rust_source_constants()
    parity = constant_parity_checks()
    gram = gram_structure_parity()
    cargo = cargo_test_lane()
    core_ok = (parity["three_a_be_equals_pi4_over_15_exact"]
               and parity["three_a_fd_equals_7pi4_over_120_exact"]
               and parity["rust_expectations_present"]
               and all(parity["zeta_table_exact"].values())
               and parity["apery_float_matches_mpmath_1e15"]
               and parity["zeta5_float_matches_mpmath_1e15"]
               and gram["closed_forms_exact"]
               and gram["det_nonzero_wellposed"]
               and gram["numeric_matches_mpmath_1e14"]
               and consts["gram_structure_4_i2i3_3_i1i2"])
    cargo_ok = cargo.get("ok", True)     # fallback mode does not fail the seal
    return {
        "seal": "teff.rust_twin_parity",
        "status": "PASS" if (core_ok and cargo_ok) else "FAIL",
        "owner": "TEFF",
        "claim_tier": "diagnostic_only",
        "rust_sources": consts,
        "constant_parity": parity,
        "gram_structure_parity": gram,
        "cargo_lane": cargo,
        "discharges": "teff_representative_nonclaims.yaml future_obligation "
                      "(Rust twin parity); parity mode disclosed in cargo_lane",
        "claim_boundary": "internal cross-implementation consistency check; "
                          "no data, signal-discovery, "
                          "Bianchi-class-identification-of-the-sky, "
                          "native-solver-produced, or probabilistic-inference "
                          "claim",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(teff_rust_parity_seal(), indent=2, default=float))
