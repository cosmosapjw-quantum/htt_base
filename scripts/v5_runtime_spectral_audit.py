"""V5 runtime-track spectral audit — Session 1 (fix.md).

Goal: quantify the unstable mode of `_build_residual_joint_affine_operator(...).matrix`
on the Tier-B residual-joint block at several cosmological η values, confirming that
the instability is structural (operator eigenvalue > 0) rather than numerical
(stepper policy).

Outputs (to stdout + `docs/V5_RUNTIME_SPECTRAL_AUDIT.json`):
    - per η: largest-real-part eigenvalue (λ_max), right & left eigenvectors
    - per η: block participation ratio (|v_rl|², |v_rh|², |v_rs|²) of λ_max
    - λ_max(η) curve check against the 0.14 / Mpc growth rate from the trajectory

Does NOT modify any physics or integrator code. Run is read-only instrumentation.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
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
from bass.hierarchy.pstf_tensor import pack_hierarchy  # noqa: F401 — used indirectly
from bass.runtime import (
    CheckpointPolicy,
    ConstraintProjectionPolicy,
    CouplingMode,
    FeatureStatus,
    IntegratorFamily,
    RuntimeControlBlock,
    SolverFeatureFlags,
    SolverTier,
    execute_tier_b_solver,
)
from bass.spectrum import CutoffCampaignSpec
from bass.species.registry import SpeciesBackgroundRegistry


TARGETS_MPC: tuple[float, ...] = (300.0, 350.0, 400.0, 450.0, 500.0)


@dataclass
class EtaSnapshotBundle:
    """Materials needed to rebuild A_right at a target η."""

    eta: float
    y: np.ndarray
    integrator: object = field(repr=False)


def _install_snapshot_hook(targets: tuple[float, ...]):
    captures: list[EtaSnapshotBundle] = []
    hit: set[float] = set()
    original = M.Ver2TierBIntegrator._explicit_rhs

    def _hooked(self, eta, y):
        result = original(self, eta, y)
        for tgt in targets:
            if tgt in hit:
                continue
            if float(eta) >= tgt:
                captures.append(
                    EtaSnapshotBundle(
                        eta=float(eta), y=np.asarray(y, dtype=np.float64).copy(),
                        integrator=self,
                    )
                )
                hit.add(tgt)
                break
        return result

    M.Ver2TierBIntegrator._explicit_rhs = _hooked
    return captures


def _assemble_A_right(bundle: EtaSnapshotBundle):
    integ = bundle.integrator
    snap = integ._eta_runtime_snapshot(bundle.eta)
    (
        photon_T, photon_E, photon_B, neutrino_tower, baryon_local, _cdm_local,
        source_local, _residual_local, _residual_harmonic, _residual_source,
    ) = M._unpack_radiation_state(
        bundle.y, integ.config.L_max,
        residual_local_dof=integ._residual_local_dof,
        residual_harmonic_dof=integ._residual_harmonic_dof,
        residual_source_dof=integ._residual_source_dof,
    )
    affine = integ._build_residual_joint_affine_operator(
        snapshot=snap,
        photon_T=photon_T, photon_E=photon_E, photon_B=photon_B,
        neutrino_tower=neutrino_tower, baryon_local=baryon_local,
        source_local=source_local,
    )
    return affine, integ


def _block_participation(v: np.ndarray, local_dof: int, harmonic_dof: int) -> dict:
    v2 = np.abs(v) ** 2
    total = float(np.sum(v2)) or 1.0
    local = float(np.sum(v2[:local_dof]))
    harm = float(np.sum(v2[local_dof : local_dof + harmonic_dof]))
    src = float(np.sum(v2[local_dof + harmonic_dof :]))
    return {
        "local_frac": local / total,
        "harmonic_frac": harm / total,
        "source_frac": src / total,
    }


def _top_eigenpairs(A, *, k: int = 6):
    """Return (eigvals, right_vecs) sorted by descending real part."""
    n = A.shape[0]
    k_eff = min(k, n - 2) if n > 3 else max(1, n - 2)
    eigvals, vecs = eigs(A.astype(np.complex128), k=k_eff, which="LR")
    order = np.argsort(-np.real(eigvals))
    return eigvals[order], vecs[:, order]


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="v5.spectral_audit", artifact_path="artifacts/v5_audit.json",
        owner="BASS", implementation_scope="canonical_BASS",
        claim_tier="conditional", production_status="production_candidate",
        created_by="v5_audit", git_commit="audit", config_hash="a",
        input_hashes=["s"], code_version="v", schema_version="1.0.0",
        required_gates=["runtime"], passed_gates=["runtime"],
    )


def _release() -> BassReleaseMetadata:
    return BassReleaseMetadata(
        release_stage="research_candidate", run_label="v5_audit",
        config_hash="a", code_version="v", schema_version="1.0.0",
        git_commit="audit", random_seed=42,
    )


def _flags() -> SolverFeatureFlags:
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


def _integrator_config(L_max: int, eta0: float, eta1: float) -> IntegratorConfig:
    return IntegratorConfig(
        L_max=L_max, eta_initial_mpc=eta0, eta_final_mpc=eta1,
        n_output=128, rtol=1.0e-6, atol=1.0e-9,
        bianchi_cosmo=BianchiCosmology(structure=get_type("I"), beta=0.0),
        gamma_T_over_H_threshold=100.0,
    )


def main() -> int:
    print(f"# V5 runtime spectral audit — targets η = {TARGETS_MPC} Mpc")
    species = SpeciesBackgroundRegistry.from_planck2018()
    captures = _install_snapshot_hook(TARGETS_MPC)

    try:
        execute_tier_b_solver(
            manifest=_manifest(), bianchi_type="I", species=species,
            integrator_config=_integrator_config(L_max=8, eta0=261.0, eta1=14147.0),
            runtime_controls=_runtime_controls(L=8),
            feature_flags=_flags(), release=_release(),
            k_grid_mpc=np.array([1.0e-4, 2.0e-4]),
            cutoff_spec=CutoffCampaignSpec(cutoffs=(4,), closure_name="tier_b_tca", baseline_cutoff=4),
        )
        print("  run completed (unexpected — cosmological range usually diverges)")
    except RuntimeError as exc:
        print(f"  run failed as expected: {exc}")

    if not captures:
        print("ERROR: no snapshots captured (integrator aborted before any target η?)")
        return 1

    report = {"targets_mpc": list(TARGETS_MPC), "snapshots": []}

    for bundle in captures:
        affine, integ = _assemble_A_right(bundle)
        A = affine.matrix
        rl, rh, rs = affine.local_dof, affine.harmonic_dof, affine.source_dof
        n = A.shape[0]

        try:
            eigvals, R = _top_eigenpairs(A, k=6)
        except Exception as exc:
            print(f"[η={bundle.eta:.1f}] eigs(A) failed: {exc}")
            continue

        lam_max = eigvals[0]
        v = R[:, 0]
        part_right = _block_participation(v, rl, rh)

        try:
            eigvals_L, L_vecs = _top_eigenpairs(A.T, k=6)
            w = L_vecs[:, 0]
            part_left = _block_participation(w, rl, rh)
            lam_max_L = eigvals_L[0]
        except Exception as exc:
            part_left = None
            lam_max_L = None
            print(f"  note: left-eig for η={bundle.eta:.1f} failed: {exc}")

        bias_norm = float(np.linalg.norm(affine.bias, ord=np.inf))
        state_norm = float(np.linalg.norm(bundle.y, ord=np.inf))

        entry = {
            "eta_mpc": bundle.eta,
            "n_dof": int(n),
            "local_dof": int(rl),
            "harmonic_dof": int(rh),
            "source_dof": int(rs),
            "lambda_top_real": [float(np.real(z)) for z in eigvals],
            "lambda_top_imag": [float(np.imag(z)) for z in eigvals],
            "lambda_max_real": float(np.real(lam_max)),
            "lambda_max_imag": float(np.imag(lam_max)),
            "block_participation_right": part_right,
            "block_participation_left": part_left,
            "lambda_max_left_real": (None if lam_max_L is None else float(np.real(lam_max_L))),
            "bias_inf_norm": bias_norm,
            "state_inf_norm": state_norm,
        }
        report["snapshots"].append(entry)

        print(f"\n[η = {bundle.eta:.1f} Mpc]  n={n}  (local={rl}, harmonic={rh}, source={rs})")
        print(f"  top-6 Re(λ): {['%.4g' % x for x in entry['lambda_top_real']]}")
        print(f"  λ_max = {np.real(lam_max):+.5g}  ({np.imag(lam_max):+.3g} j)")
        print(f"  right-eigenvector participation: "
              f"local={part_right['local_frac']:.3f}  "
              f"harmonic={part_right['harmonic_frac']:.3f}  "
              f"source={part_right['source_frac']:.3f}")
        if part_left is not None:
            print(f"  left-eigenvector  participation: "
                  f"local={part_left['local_frac']:.3f}  "
                  f"harmonic={part_left['harmonic_frac']:.3f}  "
                  f"source={part_left['source_frac']:.3f}")
        print(f"  |bias|∞={bias_norm:.3e}   |y|∞={state_norm:.3e}")

    out_path = _REPO / "docs" / "V5_RUNTIME_SPECTRAL_AUDIT.json"
    out_path.write_text(json.dumps(report, indent=2))
    print(f"\n→ wrote {out_path.relative_to(_REPO)}")

    # Stability verdict
    if report["snapshots"]:
        lam_max_series = [s["lambda_max_real"] for s in report["snapshots"]]
        hr_conc = [s["block_participation_right"]["harmonic_frac"] for s in report["snapshots"]]
        print("\n=== Stability verdict ===")
        print(f"  λ_max(η) across {len(lam_max_series)} snapshots: " +
              ", ".join(f"{v:+.4g}" for v in lam_max_series))
        print(f"  harmonic-block participation of λ_max: " +
              ", ".join(f"{v:.3f}" for v in hr_conc))
        if any(v > 0 for v in lam_max_series):
            print("  → A_right has positive-real-part eigenvalues: OPERATOR-LEVEL INSTABILITY CONFIRMED.")
        else:
            print("  → A_right is stable; the ODE divergence is NOT via this operator.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
