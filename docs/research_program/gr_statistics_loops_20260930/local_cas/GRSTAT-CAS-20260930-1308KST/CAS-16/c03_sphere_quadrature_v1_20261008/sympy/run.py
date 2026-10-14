#!/usr/bin/env python3
"""Independent finite CAS-16-C03 SymPy certificate, with ancillary numerics."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from math import comb
from pathlib import Path

import mpmath as mp
import sympy as sp


ROOT = Path(__file__).resolve().parents[8]
COMPONENT = Path(__file__).resolve().parent.parent
CONTRACT = COMPONENT / "EXECUTION_CONTRACT.json"
INPUTS = COMPONENT / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
EXPECTED_HASHES = {
    CONTRACT: "d36ffedcbeb64c201671e78e42be41ea9b6d160d148d7aadf51134a9dfbe068c",
    INPUTS: "6c536bf89687f6f4f8aaeec90154e1c9cf20b994870e789faa3cff5d5735ac82",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fourier_coefficients(a: int, b: int) -> dict[int, sp.Expr]:
    """Expand cos(phi)^a sin(phi)^b in e^(im phi) exactly."""
    out: dict[int, sp.Expr] = {}
    scale = 2 ** (a + b) * sp.I**b
    for k in range(a + 1):
        for ell in range(b + 1):
            m = a + b - 2 * (k + ell)
            out[m] = out.get(m, sp.S.Zero) + sp.Rational(
                comb(a, k) * comb(b, ell) * (-1) ** ell, 2 ** (a + b)
            ) / sp.I**b
    return {m: sp.simplify(v) for m, v in out.items() if v != 0}


def main() -> int:
    failures: list[str] = []
    hashes: dict[str, str] = {}
    for path, expected in EXPECTED_HASHES.items():
        actual = sha256(path)
        hashes[str(path.relative_to(ROOT))] = actual
        if actual != expected:
            failures.append(f"FROZEN_INPUT_HASH_MISMATCH {path}: {actual} != {expected}")
    contract = json.loads(CONTRACT.read_text())
    admitted = json.loads(INPUTS.read_text())
    if contract["identity"]["contract_id"] != "GRSTAT-20260930-CAS-16-C03-SPHERE-QUADRATURE-V1":
        failures.append("contract identity mismatch")
    if admitted["schema"] != "htt.cas16.c03.admitted-inputs.v1":
        failures.append("admitted input schema mismatch")
    print("SymPy CAS-16-C03 exact finite certificate", file=sys.stderr)
    print(f"Python {sys.version.split()[0]}; SymPy {sp.__version__}; mpmath {mp.__version__}", file=sys.stderr)
    for key, value in hashes.items():
        print(f"INPUT_SHA256 {value} {key}", file=sys.stderr)

    s7 = sp.sqrt(sp.Rational(10, 7))
    u = sp.sqrt(5 - 2 * s7) / 3
    v = sp.sqrt(5 + 2 * s7) / 3
    wu = (322 + 13 * sp.sqrt(70)) / 900
    wv = (322 - 13 * sp.sqrt(70)) / 900
    nodes = [sp.S.Zero, u, -u, v, -v]
    weights = [sp.Rational(128, 225), wu, wu, wv, wv]
    radial_moments = []
    for k in range(9):
        value = sp.simplify(sum(w * x**k for x, w in zip(nodes, weights)))
        target = sp.Rational(2, k + 1) if k % 2 == 0 else sp.S.Zero
        residual = sp.simplify(value - target)
        radial_moments.append(value)
        if residual != 0:
            failures.append(f"GL5_MOMENT degree={k} residual={residual}")
        print(f"GL5_MOMENT {k} value={value} target={target} residual={residual}", file=sys.stderr)

    cases = []
    max_mode = 0
    for a in range(9):
        for b in range(9 - a):
            for c in range(9 - a - b):
                coeff = fourier_coefficients(a, b)
                max_mode = max(max_mode, *(abs(m) for m in coeff))
                discrete = sp.simplify(sum(v for m, v in coeff.items() if m % 9 == 0))
                continuous = sp.simplify(coeff.get(0, sp.S.Zero))
                angular_residual = sp.simplify(discrete - continuous)
                if angular_residual != 0:
                    failures.append(f"AZIMUTH a={a} b={b} c={c} residual={angular_residual}")
                if continuous == 0:
                    grid = sp.S.Zero
                    sphere = sp.S.Zero
                else:
                    # All nonzero constant Fourier coefficients have even a,b,
                    # so the remaining radial factor is a polynomial.
                    if (a + b) % 2:
                        failures.append(f"NONPOLYNOMIAL_ANGULAR_CONSTANT a={a} b={b}")
                        continue
                    p = (a + b) // 2
                    grid_radial = sp.simplify(sum(
                        (-1) ** h * sp.binomial(p, h) * radial_moments[c + 2 * h]
                        for h in range(p + 1)
                    ))
                    sphere_radial = sp.simplify(sum(
                        (-1) ** h * sp.binomial(p, h)
                        * (sp.Rational(2, c + 2 * h + 1) if (c + 2 * h) % 2 == 0 else 0)
                        for h in range(p + 1)
                    ))
                    grid = sp.simplify(discrete * grid_radial / 2)
                    sphere = sp.simplify(continuous * sphere_radial / 2)
                residual = sp.simplify(grid - sphere)
                if residual != 0:
                    failures.append(f"MONOMIAL a={a} b={b} c={c} residual={residual}")
                cases.append({"exponents": [a, b, c], "grid": str(grid), "sphere": str(sphere), "residual": str(residual)})
                print(f"MONOMIAL {a},{b},{c} Q={grid} target={sphere} residual={residual}", file=sys.stderr)
    if len(cases) != 165:
        failures.append(f"FAMILY_CARDINALITY {len(cases)} != 165")
    if max_mode > 8:
        failures.append(f"FOURIER_MODE_BOUND {max_mode} > 8")

    # Standard GL4 rule, deliberately independent of the GL5 table.
    t4 = sp.sqrt(sp.Rational(6, 5))
    lo4 = sp.sqrt((3 - 2 * t4) / 7)
    hi4 = sp.sqrt((3 + 2 * t4) / 7)
    wlo4 = (18 + sp.sqrt(30)) / 36
    whi4 = (18 - sp.sqrt(30)) / 36
    gl4_diff = sp.simplify(2 * wlo4 * lo4**8 + 2 * whi4 * hi4**8 - sp.Rational(2, 9))
    if gl4_diff != -sp.Rational(128, 11025):
        failures.append(f"GL4_WITNESS {gl4_diff}")
    c8 = fourier_coefficients(8, 0)
    n8_diff = sp.simplify(sum(v for m, v in c8.items() if m % 8 == 0) - c8[0])
    if n8_diff != sp.Rational(1, 128):
        failures.append(f"NPHI8_WITNESS {n8_diff}")
    print(f"GL4_WITNESS unnormalized_difference={gl4_diff} normalized_difference={gl4_diff/2}", file=sys.stderr)
    print(f"NPHI8_WITNESS normalized_difference={n8_diff}", file=sys.stderr)

    # Direct high-precision grid evaluations are diagnostics, never the exact proof.
    mp.mp.dps = 80
    mm = mp.mpf
    mpu = mp.sqrt(5 - 2 * mp.sqrt(mm(10) / 7)) / 3
    mpv = mp.sqrt(5 + 2 * mp.sqrt(mm(10) / 7)) / 3
    mp_nodes = [mm(0), mpu, -mpu, mpv, -mpv]
    mp_weights = [mm(128) / 225, (322 + 13 * mp.sqrt(70)) / 900,
                  (322 + 13 * mp.sqrt(70)) / 900,
                  (322 - 13 * mp.sqrt(70)) / 900,
                  (322 - 13 * mp.sqrt(70)) / 900]
    maximum_error = mm(0)
    numeric_failures = []
    for row in cases:
        a, b, c = row["exponents"]
        total = mm(0)
        for mu, weight in zip(mp_nodes, mp_weights):
            rho = mp.sqrt(1 - mu**2)
            for j in range(9):
                phi = 2 * mp.pi * j / 9
                total += weight * (rho * mp.cos(phi))**a * (rho * mp.sin(phi))**b * mu**c / 18
        target = mp.mpf(row["sphere"])
        err = abs(total - target)
        maximum_error = max(maximum_error, err)
        if err > mm("1e-50") + mm("1e-40") * abs(target):
            numeric_failures.append({"exponents": [a, b, c], "error": mp.nstr(err, 20)})
    if numeric_failures:
        failures.append(f"80_DIGIT_DIAGNOSTIC_FAILURES count={len(numeric_failures)}")
    print(f"NUMERIC_80D max_abs_error={mp.nstr(maximum_error, 25)} failures={len(numeric_failures)}", file=sys.stderr)
    for failure in failures:
        print(f"FIRST_OR_SUBSEQUENT_FAILURE {failure}", file=sys.stderr)

    status = "PASS" if not failures else "FAIL"
    command = "python3 -B docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-16/c03_sphere_quadrature_v1_20261008/sympy/run.py"
    result = {
        "schema_version": 2,
        "axis": "sympy",
        "status": status,
        "contract_id": contract["identity"]["contract_id"],
        "contract_sha256": hashes[str(CONTRACT.relative_to(ROOT))],
        "input_sha256": hashes,
        "evidence_class": "exact",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "commands": [{"cmd": command, "exit": 0 if not failures else 1}],
        "tool_versions": {"python": sys.version.split()[0], "sympy": sp.__version__, "mpmath": mp.__version__},
        "executable_artifacts": [{"path": str(Path(__file__).relative_to(ROOT)), "sha256": sha256(Path(__file__))}],
        "raw_logs": ["sympy/raw.stdout.log", "sympy/raw.stderr.log"],
        "domain_alignment": {
            "mu": "real [-1,1]", "phi": "real [0,2*pi)",
            "sphere_map": "x=sqrt(1-mu^2) cos(phi), y=sqrt(1-mu^2) sin(phi), z=mu",
            "square_root_branch": "nonnegative real", "measure": "dmu dphi",
            "grid_normalization": "(1/2) GL5 weight times (1/9) azimuth weight",
            "target_normalization": "1/(4*pi) sphere integral",
            "exponents": "natural, total degree <=8", "units": "dimensionless",
        },
        "proof_method": "Exact finite Fourier expansion; 9th-root average selects modes divisible by 9, integral selects zero mode; maximum mode 8. Exact GL5 moments through degree 8 reduce each nonzero angular case to a polynomial radial integral.",
        "exact_checks": {"monomial_count": len(cases), "maximum_fourier_mode": max_mode,
                         "gl5_moments": [str(v) for v in radial_moments],
                         "gl4_mu8_unnormalized_difference": str(gl4_diff),
                         "gl4_mu8_normalized_difference": str(gl4_diff / 2),
                         "nphi8_cos8_normalized_difference": str(n8_diff),
                         "cases": cases},
        "ancillary_numeric": {"precision_digits": 80, "absolute_tolerance": "1e-50",
                              "relative_tolerance": "1e-40", "max_abs_error": mp.nstr(maximum_error, 25),
                              "failures": numeric_failures},
        "failures": failures,
        "claim_ceiling": "CAS-16-C03 finite scalar monomial product quadrature only; no C01/C02, general theorem, collision norm, DP06, or scientific admission",
        "launch_id": None, "global_harness_used": False,
        "observed_model": "UNKNOWN", "observed_effort": "UNKNOWN",
    }
    result["lifecycle_status"] = "BLOCKED_NO_GLOBAL_REGISTERED_LAUNCH"
    (Path(__file__).parent / "axis_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    gate_payload = {
        "checks": {"CAS-16-C03": not failures},
        "domain_assumption_diff": [],
        "counterexample": failures[0] if failures else None,
    }
    print(json.dumps(gate_payload, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
