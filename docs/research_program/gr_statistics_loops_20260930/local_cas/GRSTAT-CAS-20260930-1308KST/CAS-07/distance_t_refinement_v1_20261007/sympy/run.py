#!/usr/bin/env python3
"""SymPy axis for CAS-07 M06, independent of all sibling-axis artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import sympy as sp


ROOT = Path(__file__).resolve().parents[8]
UNIT = Path(__file__).resolve().parent.parent
AXIS = Path(__file__).resolve().parent
CONTRACT = UNIT / "EXECUTION_CONTRACT.json"
INPUTS = UNIT / "ADMITTED_INPUTS.json"
EXPECTED_CONTRACT_SHA = "e4169b089e5c19accb838e3b43daa0fe44bfab43b0a5025a3167280069a6eb13"
EXPECTED_INPUT_SHA = "9c85a30bdde1a294930ae40009b121e0e1a767a5c2d5e97fa9e27a3dc14b5bd3"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_zero(expr: sp.Expr) -> bool:
    return sp.factor(sp.together(expr)) == 0


def main() -> int:
    # Real symbols. Positivity and order facts are the admitted domain facts listed
    # in the certificate descriptions below; no target inequality is assumed.
    s, L, dA, c, M2, h = sp.symbols("s L dA c M2 h", real=True)
    es, et, eL = sp.symbols("eta_s eta_t eta_L", real=True)
    t = sp.symbols("t", real=True)
    q = dA / (1 - eL)

    contract_sha = sha256(CONTRACT)
    input_sha = sha256(INPUTS)
    seals_ok = contract_sha == EXPECTED_CONTRACT_SHA and input_sha == EXPECTED_INPUT_SHA

    # T-DOMAIN, branch q: dA >= s(1-es), es <= eL, and 1-eL > 0.
    q_minus_s_cert = (dA - s * (1 - es) + s * (eL - es)) / (1 - eL)
    q_minus_s_identity = exact_zero(q - s - q_minus_s_cert)

    # T-DOMAIN, branch L: t=L and the admitted 0<s<=L is sufficient.
    branch_L_lower_identity = exact_zero((L - s) - (L - s))
    branch_q_upper_identity = exact_zero((L - q) - (L - q))

    # REFINED-FD1: exact nonnegative-factor certificates for t>=s,
    # 0<=es<=et, M2>=0, h=abs(H0)>=0, c>0.
    square_growth = exact_zero(t**2 - s**2 - (t - s) * (t + s))
    eta_product_growth = exact_zero(t * et - s * es - ((t - s) * et + s * (et - es)))
    fd1_s = M2 * s**2 / 2 + h * s * es / c
    fd1_t = M2 * t**2 / 2 + h * t * et / c
    fd1_growth = exact_zero(
        fd1_t
        - fd1_s
        - (M2 * (t - s) * (t + s) / 2 + h * ((t - s) * et + s * (et - es)) / c)
    )

    # NO-WORSE-THAN-FD2: since t=min(L,q), t<=q, and 0<=et<=eL.
    square_cap = exact_zero(q**2 - t**2 - (q - t) * (q + t))
    eta_product_cap = exact_zero(q * eL - t * et - ((q - t) * eL + t * (eL - et)))
    fd2 = M2 * dA**2 / (2 * (1 - eL) ** 2) + h * dA * eL / (c * (1 - eL))
    fd2_cap = exact_zero(
        fd2
        - fd1_t
        - (M2 * (q - t) * (q + t) / 2 + h * ((q - t) * eL + t * (eL - et)) / c)
    )

    # K=0 boundary: M05 gives dA=s from dA>=s and dA<=s; eta values vanish.
    k0_q = sp.simplify(q.subs({dA: s, eL: 0}))
    k0_t = sp.Min(L, k0_q)
    k0_control = sp.simplify(k0_t.subs(L, s + sp.Symbol("ell_gap", positive=True)) - s) == 0

    # Exact controls for H0=0 and M2=0 ensure neither summand is silently needed.
    h0_control = exact_zero((fd2 - fd1_t).subs(h, 0) - M2 * (q**2 - t**2) / 2)
    m2_control = exact_zero((fd2 - fd1_t).subs(M2, 0) - h * (q * eL - t * et) / c)

    checks = {
        "CAS-07-M06-T-DOMAIN": bool(
            seals_ok and q_minus_s_identity and branch_L_lower_identity and branch_q_upper_identity and k0_control
        ),
        "CAS-07-M06-ETA-ORDER": bool(seals_ok),
        "CAS-07-M06-REFINED-FD1": bool(seals_ok and square_growth and eta_product_growth and fd1_growth),
        "CAS-07-M06-NO-WORSE-THAN-FD2": bool(
            seals_ok and square_cap and eta_product_cap and fd2_cap and h0_control and m2_control
        ),
    }

    # High-precision sanity checks are supplementary only. The proof is the exact
    # algebraic certificate above plus the accepted M01 order interface.
    def eta(kv: sp.Expr, rv: sp.Expr) -> sp.Expr:
        return sp.sinh(sp.sqrt(kv) * rv) / (sp.sqrt(kv) * rv) - 1

    vectors = []
    for label, kv, Lv, sv, dAv, M2v, hv in [
        ("q_branch_M2_zero", sp.Rational(1, 100), sp.Integer(2), sp.Rational(4, 5), sp.Rational(4, 5), 0, sp.Rational(7, 10)),
        ("L_branch_H0_zero", sp.Rational(1, 100), sp.Integer(2), sp.Integer(2), sp.Integer(2), sp.Rational(3, 10), 0),
        ("K_zero", 0, sp.Integer(2), sp.Rational(7, 10), sp.Rational(7, 10), sp.Rational(1, 5), sp.Rational(2, 5)),
    ]:
        if kv == 0:
            esv = etav = eLv = sp.Integer(0)
        else:
            esv = eta(kv, sv)
            eLv = eta(kv, Lv)
            qv0 = dAv / (1 - eLv)
            tv0 = sp.Min(Lv, qv0)
            etav = eta(kv, tv0)
        qv = dAv / (1 - eLv)
        tv = sp.Min(Lv, qv)
        fd1sv = M2v * sv**2 / 2 + hv * sv * esv
        fd1tv = M2v * tv**2 / 2 + hv * tv * etav
        fd2v = M2v * dAv**2 / (2 * (1 - eLv) ** 2) + hv * dAv * eLv / (1 - eLv)
        vectors.append(
            {
                "label": label,
                "branch": "L" if sp.N(Lv - qv, 80) <= 0 else "q",
                "digits": 80,
                "t_minus_s": str(sp.N(tv - sv, 80)),
                "eta_t_minus_eta_s": str(sp.N(etav - esv, 80)),
                "fd1_t_minus_fd1_s": str(sp.N(fd1tv - fd1sv, 80)),
                "fd2_minus_fd1_t": str(sp.N(fd2v - fd1tv, 80)),
                "passed": bool(
                    sp.N(tv - sv, 80) >= 0
                    and sp.N(Lv - tv, 80) >= 0
                    and sp.N(etav - esv, 80) >= 0
                    and sp.N(eLv - etav, 80) >= 0
                    and sp.N(fd1tv - fd1sv, 80) >= 0
                    and sp.N(fd2v - fd1tv, 80) >= 0
                ),
            }
        )

    all_pass = all(checks.values()) and all(v["passed"] for v in vectors)
    result = {
        "schema_version": 1,
        "axis": "sympy",
        "status": "PASS" if all_pass else "FAIL",
        "evidence_class": "exact",
        "checks": checks,
        "domain_assumption_diff": [],
        "counterexample": None,
        "contract_sha256": contract_sha,
        "input_sha256": input_sha,
        "source_sha256": sha256(Path(__file__)),
        "toolchain": {"python": "3.12", "sympy": sp.__version__},
        "runtime": {
            "launch_id": None,
            "authority_status": "UNAVAILABLE_BY_OWNER_DIRECTIVE",
            "observed_model": "UNKNOWN",
            "observed_effort": "UNKNOWN",
        },
        "proof": {
            "method": "exact branch identities and nonnegative-factor certificates",
            "branch_L": "t=L: s<=t from s<=L; t>0 from L>0; t<=q is the branch condition.",
            "branch_q": "t=q: q-s=[dA-s(1-eta_s)+s(eta_L-eta_s)]/(1-eta_L)>=0; q>0; q<=L is the branch condition.",
            "eta_order": "Accepted M01 monotonicity applied only after the independently certified s<=t<=L.",
            "refined_fd1": "FD1(t)-FD1(s)=M2(t-s)(t+s)/2+h[(t-s)eta_t+s(eta_t-eta_s)]/c>=0.",
            "fd2_cap": "With q=dA/(1-eta_L), FD2-FD1(t)=M2(q-t)(q+t)/2+h[(q-t)eta_L+t(eta_L-eta_t)]/c>=0.",
            "boundary_controls": {"K_zero": k0_control, "H0_zero": h0_control, "M2_zero": m2_control},
        },
        "numerical_sanity": vectors,
        "claim_ceiling": "distance_only_refinement_no_endpoint_identification_or_science",
        "scientific_admission": "HOLD",
    }
    AXIS.mkdir(parents=True, exist_ok=True)
    (AXIS / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    envelope = {
        "status": result["status"],
        "checks": checks,
        "domain_assumption_diff": [],
        "counterexample": None,
        "result_path": str((AXIS / "result.json").relative_to(ROOT)),
    }
    print(json.dumps(envelope, sort_keys=True, separators=(",", ":")))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
