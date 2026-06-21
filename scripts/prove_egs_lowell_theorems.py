#!/usr/bin/env python3
"""REV-R104: symbolic proofs of new EGS-type low-ell diagnostic theorems.

Proves three EGS-type theorems for the report's diagnostic variables that were
proposed (Conditional) in the external `egs_theorem_program` zip but are not in
the research report:

  NT-A1  Quadrupole-filling EGS identity:  given the free-streaming ell=2 shear
         closure a2 = kappa * Sigma, the shear filling fraction is
         F_shear = a2^2 / (kappa^2 x_max) proportional to D2, with the EGS limit
         F_shear -> 0 as D2 -> 0, and F_shear independent of the tilt rapidity.
  NT-A3  Cosmic-variance Cramer-Rao floor:  because F_shear is linear in the
         quadrupole power C2, the single-sky cosmic variance Var(C2) =
         2 C2^2 / (2l+1) forces an irreducible fractional floor
         sigma(F_shear)/F_shear >= sqrt(2/(2l+1)) = sqrt(2/5) ~ 0.632 at l=2.
  NT-B3  Depth-transport EGS limit:  for a depth-steady shear and no tilt the
         depth gap G_F(z) = F(z)/F(z_ref) is identically 1 (no gap); a
         depth-evolving tilt imprints a nonzero dG_F/dz.

Every theorem is CONDITIONAL on explicit hypotheses (free-streaming linear ell=2
closure; single-sky chi-square quadrupole variance; additive shear+tilt filling)
and is a structural/limit statement, not a detection. Symbolic algebra, limits,
sphere integrals, and the chi-square variance propagation are verified with the
Wolfram Engine via wolframclient.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = REPO_ROOT / "docs/generated/egs_lowell_theorem_proofs.json"
OUT_MD = REPO_ROOT / "docs/generated/egs_lowell_theorem_proofs.md"

# ETM free-streaming ell=2 <-> shear coupling coefficient (12/63 = 4/21).
ETM_KAPPA = "4/21"


def _git_state() -> str:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip()
        dirty = subprocess.run(
            ["git", "status", "--short"], cwd=REPO_ROOT, text=True, capture_output=True
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return f"{commit}+dirty" if dirty else commit


def _prove(session) -> list[dict]:
    from wolframclient.language import wlexpr

    def show(expr: str) -> str:
        """Return the InputForm string of a Wolfram expression."""
        return str(session.evaluate(wlexpr(f"ToString[{expr}, InputForm]")))

    def run(expr: str) -> None:
        session.evaluate(wlexpr(expr))

    def istrue(expr: str) -> bool:
        return str(session.evaluate(wlexpr(f"TrueQ[{expr}]"))) == "True"

    theorems: list[dict] = []

    # ---- NT-A1: quadrupole-filling EGS identity ----------------------------
    run("ClearAll[Sigma, a2, kappa, xmax, cD, D2, beta]")
    run("Fshear = Sigma^2 / xmax")
    run("FshearInA2 = Simplify[Fshear /. Sigma -> a2/kappa]")
    run(
        "FshearInD2 = Simplify[FshearInA2 /. a2 -> Sqrt[D2/cD], "
        "Assumptions -> {D2 >= 0, cD > 0, kappa > 0, xmax > 0}]"
    )
    run("nv = {Sin[t] Cos[p], Sin[t] Sin[p], Cos[t]}")
    run(
        "avgNN = Simplify[Table[Integrate[nv[[i]] nv[[j]] Sin[t], {t,0,Pi},{p,0,2 Pi}]"
        "/(4 Pi), {i,1,3},{j,1,3}]]"
    )
    qed_a1 = (
        istrue("Simplify[FshearInA2 == a2^2/(kappa^2 xmax)]")
        and istrue("Simplify[FshearInD2 == D2/(cD kappa^2 xmax)]")
        and istrue("Limit[FshearInD2, D2 -> 0] == 0")
        and istrue("D[FshearInA2, beta] == 0")
        and istrue("avgNN == (1/3) IdentityMatrix[3]")
    )
    theorems.append(
        {
            "theorem_id": "NT-A1",
            "title": "Quadrupole-filling EGS identity",
            "status": "conditional_proved",
            "proof_status": "symbolically_verified_wolfram",
            "hypotheses": [
                "free-streaming linear ell=2 closure a2 = kappa*Sigma, kappa>0 constant",
                "shear filling F_shear = Sigma^2 / x_max, x_max>0",
                "quadrupole power D2 = cD * a2^2, cD>0",
                "tilt rapidity beta enters the dipole a1 only (a2 independent of beta)",
            ],
            "kappa_closure_value": ETM_KAPPA,
            "steps": {
                "F_shear_in_a2": show("FshearInA2"),
                "F_shear_in_D2": show("FshearInD2"),
                "egs_limit_D2_to_0": show("Limit[FshearInD2, D2 -> 0]"),
                "d_Fshear_d_beta": show("D[FshearInA2, beta]"),
                "sphere_avg_n_a_n_b": show("avgNN"),
            },
            "qed": qed_a1,
            "claim": (
                "F_shear is an EGS-bounded functional of the CMB quadrupole: "
                "F_shear = a2^2/(kappa^2 x_max) proportional to D2, F_shear -> 0 "
                "as D2 -> 0, and F_shear is independent of the tilt rapidity. "
                "Conditional on the stated free-streaming linear closure; not a "
                "detection."
            ),
        }
    )

    # ---- NT-A3: cosmic-variance Cramer-Rao floor ---------------------------
    run("ClearAll[C2, kappa, xmax, l]")
    run("FC = C2/(kappa^2 xmax)")  # F_shear linear in the quadrupole POWER C2
    run("VarC2 = 2 C2^2/(2 l + 1)")
    run("VarF = Simplify[(D[FC, C2])^2 VarC2]")
    run("FracFloor = Simplify[Sqrt[VarF]/FC, Assumptions -> {C2>0, kappa>0, xmax>0, l>=2}]")
    qed_a3 = (
        istrue("Simplify[VarF/FC^2 == 2/(2 l + 1)]")
        and istrue("Simplify[FracFloor^2 == 2/(2 l + 1)]")  # branch-free squared identity
        and istrue("Simplify[(FracFloor /. l -> 2)^2 == 2/5]")
    )
    theorems.append(
        {
            "theorem_id": "NT-A3",
            "title": "Cosmic-variance Cramer-Rao floor on F_shear",
            "status": "proved",
            "proof_status": "symbolically_verified_wolfram",
            "hypotheses": [
                "F_shear = C2/(kappa^2 x_max) is linear in the quadrupole power C2 (NT-A1)",
                "single-sky cosmic variance Var(C2) = 2 C2^2/(2l+1) (chi-square, 2l+1 dof)",
                "shear sources the quadrupole (l=2) only at leading order",
            ],
            "steps": {
                "Var_C2": show("VarC2"),
                "Var_F_shear": show("VarF"),
                "Var_F_over_F2": show("Simplify[VarF/FC^2]"),
                "fractional_floor": show("FracFloor"),
                "fractional_floor_at_l2": show("FracFloor /. l -> 2"),
                "fractional_floor_at_l2_numeric": show("N[FracFloor /. l -> 2, 6]"),
            },
            "qed": qed_a3,
            "claim": (
                "The quadrupole cosmic variance forces an irreducible fractional "
                "floor sigma(F_shear)/F_shear >= sqrt(2/(2l+1)); at l=2 this is "
                "sqrt(2/5) ~ 0.632, so the shear-filling fraction is unmeasurable "
                "below ~63% fractional precision from a single sky."
            ),
        }
    )

    # ---- NT-B3: depth-transport EGS limit ----------------------------------
    run("ClearAll[Fsh, Ft, z, zref, c, q]")
    run("GF[ft_] := (Fsh + ft[z])/(Fsh + ft[zref])")
    run("GFt = GF[Function[u, c u^q]]")
    qed_b3 = (
        istrue("Simplify[GF[(0 &)] == 1]")
        and istrue("Simplify[D[GF[(0 &)], z]] == 0")
        and (not istrue("Simplify[(D[GFt, z] /. {Fsh->1, c->1, q->1, zref->1, z->2})] == 0"))
    )
    theorems.append(
        {
            "theorem_id": "NT-B3",
            "title": "Depth-transport EGS limit for G_F",
            "status": "conditional_proved",
            "proof_status": "symbolically_verified_wolfram",
            "hypotheses": [
                "additive filling F(z) = F_shear(z) + F_tilt(z)",
                "depth gap G_F(z) = F(z)/F(z_ref)",
                "depth-steady shear: F_shear(z) = Fsh constant in z",
            ],
            "steps": {
                "G_F_no_tilt": show("GF[(0 &)]"),
                "dG_F_dz_no_tilt": show("Simplify[D[GF[(0 &)], z]]"),
                "dG_F_dz_power_law_tilt": show(
                    "Simplify[D[GFt, z], Assumptions -> {c>0, q>0, z>0, Fsh>0}]"
                ),
                "dG_F_dz_power_law_tilt_example_value": show(
                    "Simplify[(D[GFt, z] /. {Fsh->1, c->1, q->1, zref->1, z->2})]"
                ),
            },
            "qed": qed_b3,
            "claim": (
                "For a depth-steady shear and no tilt, G_F(z) is identically 1 "
                "(EGS depth limit: no depth gap); a depth-evolving tilt imprints a "
                "nonzero dG_F/dz. Conditional on the additive filling decomposition."
            ),
        }
    )
    return theorems


def build_proofs() -> dict:
    from wolframclient.evaluation import WolframLanguageSession

    session = WolframLanguageSession()
    try:
        version = str(session.evaluate(__import__("wolframclient.language", fromlist=["wlexpr"]).wlexpr("$Version")))
        theorems = _prove(session)
    finally:
        session.terminate()
    return {
        "owner": "BASS",
        "implementation_scope": "bass_py",
        "claim_tier": "program_theorem",
        "schema_version": "egs_lowell_theorem_proofs.v1",
        "transfer_source": "none",
        "engine": "wolfram",
        "wolfram_version": version,
        "source_program": "egs_theorem_program.zip (NT-A1, NT-A3, NT-B3)",
        "git_state": _git_state(),
        "theorems": theorems,
        "caveats": [
            "each theorem is conditional on explicit hypotheses and is a "
            "structural/limit statement, not a detection",
            "kappa = 4/21 is the ETM free-streaming ell=2 coefficient (cited); the "
            "theorems hold for any kappa>0",
            "no native low-ell solver output, HTT evidence, MIO certificate, or "
            "Bianchi family identification is produced",
        ],
    }


def render_markdown(payload: dict) -> str:
    lines = [
        "# EGS-Type Low-ell Diagnostic Theorems: Symbolic Proofs (REV-R104)",
        "",
        f"owner: {payload['owner']}",
        f"implementation_scope: {payload['implementation_scope']}",
        f"claim_tier: {payload['claim_tier']}",
        "transfer_source: none",
        f"engine: {payload['engine']} ({payload['wolfram_version']})",
        f"source_program: {payload['source_program']}",
        f"git_state: {payload['git_state']}",
        "",
    ]
    for thm in payload["theorems"]:
        lines += [
            f"## {thm['theorem_id']} - {thm['title']}",
            "",
            f"status: {thm['status']}; proof: {thm['proof_status']}; "
            f"QED: {str(thm['qed']).lower()}",
            "",
            "Hypotheses:",
            *[f"- {h}" for h in thm["hypotheses"]],
            "",
            "Symbolic steps (Wolfram):",
            *[f"- `{k}` = `{v}`" for k, v in thm["steps"].items()],
            "",
            f"Claim: {thm['claim']}",
            "",
        ]
    lines += ["## Caveats", "", *[f"- {c}" for c in payload["caveats"]], ""]
    return "\n".join(lines)


def main() -> int:
    payload = build_proofs()
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(REPO_ROOT)}")
    print(f"wrote {OUT_MD.relative_to(REPO_ROOT)}")
    for thm in payload["theorems"]:
        print(f"  {thm['theorem_id']}: QED={thm['qed']}")
    return 0 if all(t["qed"] for t in payload["theorems"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
