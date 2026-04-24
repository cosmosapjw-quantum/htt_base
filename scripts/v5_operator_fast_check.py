"""Fast V5 operator spectrum check — bypasses the full Tier-B runtime.

Builds `A_right` via direct call to `build_reduced_joint_affine_operator(...)`
with a minimal synthetic Bianchi-I background, then checks:

    (a) Eigenvalue spectrum at γ_T = 0 (post-recombination regime) — should
        be purely imaginary, i.e. max Re(λ) < 1e-10.
    (b) Weighted skew-adjointness `W A_ch + A_ch^T W = 0` with
        `W_ell = (2 ell + 1)/d_ell` for each channel — the invariant
        derived in audit Q1/Q2 that forces Re(λ) ≤ 0.
    (c) Eigenvalue spectrum at γ_T > 0 (recombination regime) to probe
        whether the Thomson term's sign is physically correct.

Takes < 5 s total on a standard workstation.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "htt" / "src"))
sys.path.insert(0, str(_REPO / "htt"))

import numpy as np

from bass.hierarchy.ver3_layout_protocol import (
    build_hierarchy_layout,
    build_reduced_joint_affine_operator,
)
from bass.los.family_backend_protocol import build_backend


def _synthetic_bg(*, gamma_t: float, geom_scale_override: float | None = None) -> dict:
    """Minimal Bianchi-I background dict that build_reduced_joint_affine_operator needs."""
    bg: dict = {
        "opacity_data": {"Gamma_T": float(gamma_t)},
        "source_tables": {
            "visibility_amplitude": 0.0,       # quiescent: pure operator test
            "polarization_source": 0.0,
            "doppler_source": 0.0,
        },
        "sigma_tensor": np.zeros((3, 3), dtype=np.float64),
        "a": 1.0e-3,         # some reasonable value during matter era
        "H": 1.0e-4,
        "k": 1.0e-4,
    }
    return bg


def _build_A(L_max: int, gamma_t: float) -> tuple[np.ndarray, int, int, int]:
    """Return (A_dense, local_dof, harmonic_dof, source_dof)."""
    truncation = {"ell_max": L_max}
    backend = build_backend(family_spec="I", truncation=truncation)
    layout = build_hierarchy_layout(
        backend, truncation=truncation, sector_order=("baryon", "cdm", "src"),
    )
    bg = _synthetic_bg(gamma_t=gamma_t)

    residual_mode_labels = tuple(
        str(mu) for mu in layout.mode_labels if str(mu) != "m0"
    ) or (str(layout.mode_labels[0]),)

    width = (L_max + 1) ** 2
    photon_zeros = {str(mu): np.zeros(width, dtype=np.float64) for mu in layout.mode_labels}
    baryon_width = int(layout.sector_local_dofs["baryon"])
    baryon_zeros = {str(mu): np.zeros(baryon_width, dtype=np.float64) for mu in layout.mode_labels}

    affine = build_reduced_joint_affine_operator(
        layout, bg, backend,
        residual_mode_labels=residual_mode_labels,
        photon_T_by_mode_label=photon_zeros,
        photon_E_by_mode_label=photon_zeros,
        photon_B_by_mode_label=photon_zeros,
        neutrino_by_mode_label=photon_zeros,
        baryon_by_mode_label=baryon_zeros,
    )
    A = np.asarray(affine.matrix.toarray(), dtype=np.float64)
    return A, affine.local_dof, affine.harmonic_dof, affine.source_dof


def _eigs_max_real(A: np.ndarray) -> tuple[float, np.ndarray]:
    evals = np.linalg.eigvals(A)
    idx = int(np.argmax(np.real(evals)))
    return float(np.real(evals[idx])), evals


def _eig_localize(A: np.ndarray, local_dof: int, harmonic_dof: int, L_max: int) -> dict:
    """Localize the top-real-part eigenvector into local/T/E/B/ν/source blocks."""
    evals, evecs = np.linalg.eig(A)
    idx = int(np.argmax(np.real(evals)))
    v = evecs[:, idx]
    v2 = np.abs(v) ** 2
    total = float(np.sum(v2)) or 1.0
    width = (L_max + 1) ** 2
    out: dict[str, float] = {
        "local_frac": float(np.sum(v2[:local_dof])) / total,
        "source_frac": float(np.sum(v2[local_dof + harmonic_dof:])) / total,
    }
    if harmonic_dof > 0:
        block_size = 4 * width
        for residual_idx in range(harmonic_dof // block_size):
            base = local_dof + residual_idx * block_size
            for name, ch in (("T", 0), ("E", 1), ("B", 2), ("nu", 3)):
                key = f"{name}_frac" if residual_idx == 0 else f"{name}_frac_res{residual_idx}"
                out[key] = float(np.sum(v2[base + ch * width : base + (ch + 1) * width])) / total
    return {"lambda_real": float(np.real(evals[idx])), "lambda_imag": float(np.imag(evals[idx])), **out}


def _weighted_skew_check(A_dense: np.ndarray, local_dof: int, harmonic_dof: int, L_max: int) -> dict:
    """Verify W A_ch + A_ch^T W = 0 per channel at gamma_t = 0.

    The weight W_ell = (2 ell + 1)/d_ell with d_ell = inv_channel from the
    operator's row-scaling. We infer d_ell directly from the assembled
    matrix via the streaming coefficient ratio, which avoids needing to
    rebuild _operator_scales.
    """
    width = (L_max + 1) ** 2
    # Block structure within the harmonic portion of A: for each residual μ,
    # [T | E | B | ν] each of width `width`, total block size = 4*width.
    A_hh = A_dense[local_dof : local_dof + harmonic_dof, local_dof : local_dof + harmonic_dof]
    results: dict = {}
    # For FLRW single residual mode, block_size == harmonic_dof.
    block_size = harmonic_dof
    n_residual = harmonic_dof // block_size if block_size > 0 else 0
    t_off, e_off, b_off, nu_off = 0, width, 2 * width, 3 * width
    ell_by_slot = np.zeros(width, dtype=np.int64)
    offset = 0
    for ell in range(L_max + 1):
        for _m in range(-ell, ell + 1):
            ell_by_slot[offset] = ell
            offset += 1

    for ch_name, ch_off in (("T", t_off), ("E", e_off), ("B", b_off), ("nu", nu_off)):
        ch = A_hh[ch_off : ch_off + width, ch_off : ch_off + width]
        # Extract d_ell by looking at A[slot_ell, slot_{ell+1}] for m=0 slots.
        # Off-diag (ℓ, ℓ+1) at m=0: -d_ℓ · geom · sqrt((ℓ+1)²)/(2ℓ+1) = -d_ℓ · geom · (ℓ+1)/(2ℓ+1)
        # We just need ratio W_ℓ/W_{ℓ'} which equals (2ℓ+1)/d_ℓ · d_{ℓ'}/(2ℓ'+1).
        # For the check WA + A^T W = 0, we solve: set W[0]=1, then
        #     W[ℓ+1] = -W[ℓ] · A[ℓ_slot, (ℓ+1)_slot] / A[(ℓ+1)_slot, ℓ_slot]
        # and verify consistency.
        slots_m0 = [int(np.where(ell_by_slot == ell)[0][ell]) for ell in range(L_max + 1)]  # (ell,0) slot
        W = np.zeros(width, dtype=np.float64)
        W[slots_m0[0]] = 1.0
        consistent = True
        for ell in range(L_max):
            i, j = slots_m0[ell], slots_m0[ell + 1]
            Aij, Aji = ch[i, j], ch[j, i]
            if abs(Aij) < 1e-30 or abs(Aji) < 1e-30:
                consistent = False
                break
            ratio = -Aji / Aij  # = W[i]/W[j] for skew-adjoint case
            if ratio <= 0:
                consistent = False
                break
            W[j] = W[i] / ratio
        # Propagate W[ell,m] = W[ell,0] for fixed ell (all m share d_ell)
        if consistent:
            for ell in range(L_max + 1):
                w_ell = W[slots_m0[ell]]
                for slot_in_ell in np.where(ell_by_slot == ell)[0]:
                    W[slot_in_ell] = w_ell

            resid = W[:, None] * ch + (ch.T) * W[None, :]
            fro_WA = float(np.linalg.norm(W[:, None] * ch, ord="fro"))
            fro_resid = float(np.linalg.norm(resid, ord="fro"))
            rel = fro_resid / max(fro_WA, 1e-30)
            results[ch_name] = {
                "weighted_skew_consistent": True,
                "||W A + A^T W||_F": fro_resid,
                "||W A||_F": fro_WA,
                "relative": rel,
                "W_spread": (float(W.min()), float(W.max())),
            }
        else:
            results[ch_name] = {"weighted_skew_consistent": False}
    return results


def main() -> int:
    print("=" * 70)
    print("Fast V5 operator check — direct assembly, no full-solver pipeline.")
    print("=" * 70)

    for L_max in (4, 6, 8, 12, 16):
        print(f"\n── L_max = {L_max} ───────────────────────────────")

        # --- (a) γ_T = 0: post-recombination regime ---
        A0, rl, rh, rs = _build_A(L_max=L_max, gamma_t=0.0)
        lam_max_0, _ = _eigs_max_real(A0)
        print(f"  γ_T = 0:   n={A0.shape[0]}  (local={rl}, harmonic={rh}, source={rs})")
        print(f"    max Re(λ) = {lam_max_0:+.3e}   "
              f"{'✓' if abs(lam_max_0) < 1e-10 else '✗  EXPECTED ≤ 1e-10'}")

        # --- (b) weighted skew-adjoint check at γ_T = 0 ---
        ws = _weighted_skew_check(A0, rl, rh, L_max)
        print("    weighted skew-adjointness  W A_ch + A_ch^T W = 0:")
        for ch, r in ws.items():
            if r["weighted_skew_consistent"]:
                print(f"      {ch:2s}: ||W A + A^T W||_F / ||W A||_F = {r['relative']:.3e}  "
                      f"{'✓' if r['relative'] < 1e-10 else '✗'}")
            else:
                print(f"      {ch:2s}: NOT weighted-skew-adjoint for any positive diagonal W")

        # --- (c) γ_T = 1.0: probe Thomson-term sign ---
        A_recomb, rl1, rh1, _ = _build_A(L_max=L_max, gamma_t=1.0)
        lam_max_recomb, _ = _eigs_max_real(A_recomb)
        delta = lam_max_recomb - lam_max_0
        sign = "damping" if delta < -1e-6 else ("growth" if delta > 1e-6 else "negligible")
        print(f"  γ_T = 1:   max Re(λ) = {lam_max_recomb:+.3e}   "
              f"Δ(γ_T) = {delta:+.3e}  ({sign})")
        if L_max == 8 and lam_max_recomb > 1e-10:
            loc = _eig_localize(A_recomb, rl1, rh1, L_max)
            print(f"    localize λ_max (L_max=8): "
                  f"local={loc['local_frac']:.3f}  T={loc.get('T_frac', 0):.3f}  "
                  f"E={loc.get('E_frac', 0):.3f}  B={loc.get('B_frac', 0):.3f}  "
                  f"ν={loc.get('nu_frac', 0):.3f}  source={loc['source_frac']:.3f}")

    print("\n" + "=" * 70)
    print("Summary:")
    print("  (a) γ_T=0 should give Re(λ_max) ≈ 0 (purely imaginary spectrum)")
    print("  (b) W A + A^T W ≈ 0 confirms weighted skew-adjoint (audit Q2 invariant)")
    print("  (c) γ_T>0 should give MORE negative Re(λ_max)  → Thomson is dissipative")
    print("      γ_T>0 giving MORE positive Re(λ_max)  → Thomson sign error")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
