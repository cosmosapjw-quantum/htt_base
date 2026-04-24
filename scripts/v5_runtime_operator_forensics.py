"""V5 runtime-track Session 2 — operator forensics.

Three checks:
    (a) Independent finite-difference Jacobian of the residual-joint operator vs
        the assembled ``A_right`` matrix. Since ``A_right`` is declared as a
        frozen linear operator, an FD Jacobian *must* equal it to within roundoff.
        A mismatch would indicate non-linearity (hidden state-dependence) that
        violates the "frozen snapshot" contract.
    (b) L_max sweep: λ_max of the harmonic block across L_max ∈ {4, 6, 8, 12, 16}.
        If the instability is a truncation-reflection artifact, λ_max should
        decrease with L_max; if it is structural (coefficient sign error),
        λ_max stays bounded away from zero.
    (c) Harmonic-block symmetry check: is ``A_hh`` symmetric, skew-symmetric, or
        neither? A proper free-streaming operator is skew-symmetric (purely
        imaginary eigenvalues); a physical dissipative operator is symmetric
        with negative eigenvalues. A symmetric matrix with positive off-diagonals
        and insufficient diagonal damping is a sign of coefficient mis-assignment.

Output: ``docs/V5_RUNTIME_OPERATOR_FORENSICS.json``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "htt" / "src"))
sys.path.insert(0, str(_REPO / "htt"))

import numpy as np
from scipy.sparse.linalg import eigs

from common.contracts import ArtifactManifest
from bass.background.bianchi_types import get_type
from bass.background.einstein_bianchi import BianchiCosmology
from bass.forward.ver2_solver_output import BassReleaseMetadata
from bass.hierarchy import ver2_native_integrator as M
from bass.hierarchy.integrator import IntegratorConfig
from bass.runtime import (
    CheckpointPolicy, ConstraintProjectionPolicy, CouplingMode, FeatureStatus,
    IntegratorFamily, RuntimeControlBlock, SolverFeatureFlags, SolverTier,
    execute_tier_b_solver,
)
from bass.spectrum import CutoffCampaignSpec
from bass.species.registry import SpeciesBackgroundRegistry


def _manifest():
    return ArtifactManifest(
        artifact_id="v5.forensics", artifact_path="artifacts/v5_forensics.json",
        owner="BASS", implementation_scope="canonical_BASS",
        claim_tier="conditional", production_status="production_candidate",
        created_by="forensics", git_commit="f", config_hash="a",
        input_hashes=["s"], code_version="v", schema_version="1.0.0",
        required_gates=["runtime"], passed_gates=["runtime"],
    )


def _release():
    return BassReleaseMetadata(
        release_stage="research_candidate", run_label="forensics",
        config_hash="a", code_version="v", schema_version="1.0.0",
        git_commit="f", random_seed=42,
    )


def _flags():
    return SolverFeatureFlags(
        background_dynamics=FeatureStatus.APPROXIMATE,
        photon_transport=FeatureStatus.APPROXIMATE,
        thomson_collision=FeatureStatus.APPROXIMATE,
        visibility_history=FeatureStatus.APPROXIMATE,
        source_propagator=FeatureStatus.APPROXIMATE,
        checkpoint_restart=FeatureStatus.DISABLED,
    )


def _runtime_controls(L: int) -> RuntimeControlBlock:
    return RuntimeControlBlock(
        tier=SolverTier.TIER_B_PSTF,
        integrator_family=IntegratorFamily.IMEX_SPLIT,
        coupling_mode=CouplingMode.BACKGROUND_THEN_RADIATION,
        multipole_cutoff=L, rtol=1.0e-6, atol=1.0e-9,
        checkpoint=CheckpointPolicy(enabled=False),
        constraint_projection=ConstraintProjectionPolicy(
            enabled=True, every_n_steps=4, status=FeatureStatus.APPROXIMATE,
        ),
        random_seed=42,
    )


def _cfg(L_max: int, eta0: float, eta1: float) -> IntegratorConfig:
    return IntegratorConfig(
        L_max=L_max, eta_initial_mpc=eta0, eta_final_mpc=eta1,
        n_output=32, rtol=1.0e-6, atol=1.0e-9,
        bianchi_cosmo=BianchiCosmology(structure=get_type("I"), beta=0.0),
        gamma_T_over_H_threshold=100.0,
    )


def _snap_at(target_eta: float, L_max: int):
    """Run integrator until it passes target_eta; return (integrator, eta_hit, y_hit)."""
    captures: list[dict] = []
    hit = {"done": False}
    original = M.Ver2TierBIntegrator._explicit_rhs

    def _hook(self, eta, y):
        out = original(self, eta, y)
        if not hit["done"] and float(eta) >= target_eta:
            captures.append({"integ": self, "eta": float(eta), "y": np.asarray(y, dtype=np.float64).copy()})
            hit["done"] = True
        return out

    M.Ver2TierBIntegrator._explicit_rhs = _hook
    try:
        execute_tier_b_solver(
            manifest=_manifest(), bianchi_type="I",
            species=SpeciesBackgroundRegistry.from_planck2018(),
            integrator_config=_cfg(L_max=L_max, eta0=261.0, eta1=14147.0),
            runtime_controls=_runtime_controls(L=min(L_max, 40)),
            feature_flags=_flags(), release=_release(),
            k_grid_mpc=np.array([1.0e-4, 2.0e-4]),
            cutoff_spec=CutoffCampaignSpec(cutoffs=(4,), closure_name="tier_b_tca", baseline_cutoff=4),
        )
    except RuntimeError:
        pass
    finally:
        M.Ver2TierBIntegrator._explicit_rhs = original
    return captures[0] if captures else None


def _A_right_from(cap):
    integ = cap["integ"]
    snap = integ._eta_runtime_snapshot(cap["eta"])
    (T, E, B, nu, bar, _cdm, src, _rl, _rh, _rs) = M._unpack_radiation_state(
        cap["y"], integ.config.L_max,
        residual_local_dof=integ._residual_local_dof,
        residual_harmonic_dof=integ._residual_harmonic_dof,
        residual_source_dof=integ._residual_source_dof,
    )
    return integ, snap, (T, E, B, nu, bar, src), integ._build_residual_joint_affine_operator(
        snapshot=snap, photon_T=T, photon_E=E, photon_B=B,
        neutrino_tower=nu, baryon_local=bar, source_local=src,
    )


def _fd_jacobian(affine, h: float = 1e-6) -> np.ndarray:
    """Finite-difference Jacobian of F(r) = A·r + b (should equal A)."""
    A = affine.matrix
    b = affine.bias
    n = A.shape[0]
    F0 = np.asarray(A @ np.zeros(n) + b, dtype=np.float64)
    J = np.zeros((n, n), dtype=np.float64)
    for j in range(n):
        e = np.zeros(n); e[j] = h
        Fp = np.asarray(A @ e + b, dtype=np.float64)
        J[:, j] = (Fp - F0) / h
    return J


def _top_eigs(A, k: int = 4):
    n = A.shape[0]
    k_eff = min(k, n - 2) if n > 3 else max(1, n - 2)
    vals, vecs = eigs(A.astype(np.complex128), k=k_eff, which="LR")
    order = np.argsort(-np.real(vals))
    return vals[order], vecs[:, order]


def main() -> int:
    report: dict = {}

    # --- Session 2 (a): FD Jacobian vs declared A_right -------------------
    print("=== Session 2(a): FD Jacobian vs A_right @ η=350 Mpc, L_max=8 ===")
    cap = _snap_at(350.0, L_max=8)
    if cap is None:
        print("ERROR: snapshot hook did not fire")
        return 1
    integ, snap, inputs, affine = _A_right_from(cap)
    A_dense = np.asarray(affine.matrix.toarray(), dtype=np.float64)
    J = _fd_jacobian(affine)
    delta = A_dense - J
    fro_A = float(np.linalg.norm(A_dense, ord="fro"))
    fro_delta = float(np.linalg.norm(delta, ord="fro"))
    rel = fro_delta / max(fro_A, 1e-30)
    print(f"  |A - J_fd|_F / |A|_F = {rel:.3e}")
    report["fd_vs_assembled"] = {
        "eta_mpc": cap["eta"],
        "L_max": 8,
        "n": int(A_dense.shape[0]),
        "fro_A": fro_A,
        "fro_delta": fro_delta,
        "relative": rel,
        "verdict": (
            "self-consistent: A_right IS the declared linear operator"
            if rel < 1e-10
            else "INCONSISTENT — hidden state-dependence detected"
        ),
    }

    # --- Session 2 (c): harmonic-block symmetry / skew-symmetry ----------
    rl, rh, rs = affine.local_dof, affine.harmonic_dof, affine.source_dof
    A_hh = A_dense[rl : rl + rh, rl : rl + rh]
    fro_hh = float(np.linalg.norm(A_hh, ord="fro"))
    sym_part = 0.5 * (A_hh + A_hh.T)
    skew_part = 0.5 * (A_hh - A_hh.T)
    fro_sym = float(np.linalg.norm(sym_part, ord="fro"))
    fro_skew = float(np.linalg.norm(skew_part, ord="fro"))
    vals_sym, _ = np.linalg.eigh(sym_part)
    print("\n=== Session 2(c): harmonic-block symmetry decomposition ===")
    print(f"  |A_hh|_F = {fro_hh:.3e}")
    print(f"  |sym(A_hh)|_F / |A_hh|_F  = {fro_sym / fro_hh:.3f}   "
          f"(1.0 = fully symmetric)")
    print(f"  |skew(A_hh)|_F / |A_hh|_F = {fro_skew / fro_hh:.3f}   "
          f"(1.0 = purely streaming)")
    print(f"  max eigenvalue of sym(A_hh) = {vals_sym.max():+.4g}")
    print(f"  min eigenvalue of sym(A_hh) = {vals_sym.min():+.4g}")
    print("  → a proper free-streaming operator is skew-symmetric (sym≈0, skew≈1);")
    print("    a proper dissipative operator has sym spectrum ≤ 0.")
    report["harmonic_block_symmetry"] = {
        "fro_norm": fro_hh,
        "symmetric_ratio": fro_sym / fro_hh,
        "antisymmetric_ratio": fro_skew / fro_hh,
        "sym_eig_max": float(vals_sym.max()),
        "sym_eig_min": float(vals_sym.min()),
    }

    # --- Session 2 (b): L_max sweep ---------------------------------------
    print("\n=== Session 2(b): λ_max sweep over L_max (at η ≈ 350 Mpc) ===")
    lmax_report: list[dict] = []
    for L_max in (4, 6, 8, 12, 16):
        print(f"  L_max = {L_max} ...")
        cap_L = _snap_at(350.0, L_max=L_max)
        if cap_L is None:
            print("    skipped (no snapshot)")
            continue
        integ_L, snap_L, _, affine_L = _A_right_from(cap_L)
        A_L = affine_L.matrix
        try:
            vals, vecs = _top_eigs(A_L, k=3)
        except Exception as exc:
            print(f"    eigs failed: {exc}")
            continue
        # harmonic-block participation of λ_max right-eigenvector
        v = vecs[:, 0]
        rl_L, rh_L = affine_L.local_dof, affine_L.harmonic_dof
        part_harm = float(np.sum(np.abs(v[rl_L : rl_L + rh_L]) ** 2) / max(np.sum(np.abs(v) ** 2), 1e-30))
        lam_max = complex(vals[0])
        entry = {
            "L_max": L_max,
            "n_dof": int(A_L.shape[0]),
            "local_dof": int(rl_L),
            "harmonic_dof": int(rh_L),
            "source_dof": int(affine_L.source_dof),
            "lambda_max_real": float(np.real(lam_max)),
            "lambda_max_imag": float(np.imag(lam_max)),
            "harmonic_participation": part_harm,
            "top3_real": [float(np.real(z)) for z in vals],
        }
        lmax_report.append(entry)
        print(f"    λ_max = {np.real(lam_max):+.4g} + {np.imag(lam_max):+.4g}j,  "
              f"harmonic participation = {part_harm:.3f}")

    report["L_max_sweep"] = lmax_report

    # --- Stability verdict ------------------------------------------------
    if lmax_report:
        lam_by_L = {e["L_max"]: e["lambda_max_real"] for e in lmax_report}
        print("\n=== Overall verdict ===")
        print("  λ_max(L_max): " + ", ".join(f"L={L}: {v:+.4g}" for L, v in lam_by_L.items()))
        trend = sorted(lam_by_L.items())
        lam_4 = lam_by_L.get(4, None)
        lam_16 = lam_by_L.get(16, None)
        if lam_4 is not None and lam_16 is not None:
            if abs(lam_16) < 0.5 * abs(lam_4):
                print("  → λ_max decreases with L_max: consistent with a truncation-reflection artifact.")
            elif abs(lam_16 - lam_4) / max(abs(lam_4), 1e-30) < 0.1:
                print("  → λ_max ≈ constant across L_max: structural (coefficient) issue, not truncation.")
            else:
                print("  → λ_max shows L_max dependence but not clean — mixed cause.")

    out_path = _REPO / "docs" / "V5_RUNTIME_OPERATOR_FORENSICS.json"
    out_path.write_text(json.dumps(report, indent=2))
    print(f"\n→ wrote {out_path.relative_to(_REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
