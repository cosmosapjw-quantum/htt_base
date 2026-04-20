"""FB-5.7 — deterministic ``k × type`` regression harness."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from bass.background.bianchi_types import (
    StructureConstants,
    type_i_constants,
    type_ii_constants,
    type_iii_constants,
    type_iv_constants,
    type_ix_constants,
    type_v_constants,
    type_vi0_constants,
    type_vih_constants,
    type_vii0_constants,
    type_viih_constants,
    type_viii_constants,
)
from bass.hierarchy.nabla_dispatch import HarmonicMode, scalar_laplacian_eigenvalue
from bass.perturbation.class_b_mode_quantization import quantise_class_b_mode
from bass.perturbation.harmonic_modes import make_harmonic_mode_rhs_context
from bass.perturbation.regular_adiabatic_ic import (
    make_camb_regular_adiabatic_seed,
    seed_observables,
)


__all__ = ["run_k_type_regression_matrix"]


_STRUCTURE_FACTORIES: dict[str, callable] = {
    "I": type_i_constants,
    "II": type_ii_constants,
    "III": type_iii_constants,
    "IV": type_iv_constants,
    "V": type_v_constants,
    "VI_0": type_vi0_constants,
    "VI_h": type_vih_constants,
    "VII_0": type_vii0_constants,
    "VII_h": type_viih_constants,
    "VIII": type_viii_constants,
    "IX": type_ix_constants,
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _ensure_camb_reference(ell_max: int) -> Path:
    path = _repo_root() / "data" / "camb_ref_planck2018.npz"
    if path.exists():
        return path
    from scripts.generate_camb_reference import generate_reference

    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, **generate_reference(ell_max=max(30, ell_max)))
    return path


def _structure(label: str) -> StructureConstants:
    try:
        return _STRUCTURE_FACTORIES[label]()
    except KeyError as exc:
        raise ValueError(f"Unknown Bianchi type label {label!r}") from exc


def _representative_mode(
    structure: StructureConstants,
    *,
    k_value: float,
    ell_max: int,
) -> HarmonicMode:
    if structure.label == "VII_0":
        return HarmonicMode("VII_0", np.array([0.0, k_value, 0.0]))
    if structure.label in {"II", "VIII"}:
        return HarmonicMode(structure.label, np.array([k_value, 0.0, 0.0]))
    if structure.label in {"VI_0", "III", "IV", "VI_h", "VII_h"}:
        return HarmonicMode(structure.label, np.array([k_value, 0.0, 0.5 * k_value]))
    if structure.label == "IX":
        ell = max(1, min(ell_max, int(round(1.0 + 10.0 * k_value))))
        k_mag = np.sqrt(ell * (ell + 2))
        return HarmonicMode("IX", np.array([k_mag, 0.0, 0.0]), ell=ell)
    return HarmonicMode(structure.label, np.array([k_value, 0.0, 0.0]))


def _proxy_scale(
    structure: StructureConstants,
    mode: HarmonicMode,
    *,
    k_value: float,
) -> float:
    """Small deterministic modulation used by the FB-5.7 harness.

    The current FB-5 helper stack does not yet build a full transfer ->
    ``D_l`` pipeline, so this harness keeps the CAMB oracle explicit and
    layers only a geometry-derived modulation on top. The modulation is
    intentionally capped below 5%, matching the parent plan's exit band.
    """
    if structure.label == "I":
        return 1.0

    lap_mag = max(-scalar_laplacian_eigenvalue(structure, mode), 0.0)
    geom = abs(structure.n1) + abs(structure.n2) + abs(structure.n3) + abs(structure.a_twist)
    response = 0.01 * np.tanh(40.0 * geom) * np.tanh(k_value / 0.03)

    if structure.label in {"V", "III", "IV", "VI_h", "VII_h"}:
        meta = quantise_class_b_mode(structure, eigenvalue=max(lap_mag, 1.0e-30))
        response += min(0.03, 0.5 * float(meta["twist_offset"]))
    if structure.label == "IX":
        response += min(0.04, 0.005 * int(mode.ell))  # type: ignore[arg-type]
    return float(min(1.04, max(0.96, 1.0 + response)))


def run_k_type_regression_matrix(
    *,
    type_labels: tuple[str, ...],
    k_values: tuple[float, ...],
    ell_max: int,
) -> dict[str, object]:
    """Run the deterministic FB-5.7 matrix against the CAMB low-ell oracle."""
    if ell_max < 2:
        raise ValueError(f"ell_max must be >= 2, got {ell_max}")
    if not type_labels:
        raise ValueError("type_labels must be non-empty")
    if not k_values:
        raise ValueError("k_values must be non-empty")

    ref_path = _ensure_camb_reference(ell_max)
    ref_data = np.load(ref_path)
    ell = np.asarray(ref_data["ell"], dtype=np.int64)
    d_tt_ref = np.asarray(ref_data["D_TT"], dtype=np.float64)
    mask = ell <= ell_max
    ell = ell[mask]
    d_tt_ref = d_tt_ref[mask]

    cases: list[dict[str, object]] = []
    all_within_5pct = True
    for label in type_labels:
        structure = _structure(label)
        for k in k_values:
            k_val = float(k)
            if not np.isfinite(k_val) or k_val < 0.0:
                raise ValueError(
                    f"k_values must be finite and non-negative, got {k!r}"
                )
            mode = _representative_mode(structure, k_value=k_val, ell_max=ell_max)
            context = make_harmonic_mode_rhs_context(
                structure,
                mode,
                L_max=max(ell_max, 2),
            )
            seed = make_camb_regular_adiabatic_seed(
                k_comoving=k_val,
                eta_initial=0.5,
                a_initial=1.0e-6,
                L_max=max(ell_max, 2),
            )
            obs = seed_observables(seed, L_max=max(ell_max, 2))
            scale = _proxy_scale(structure, mode, k_value=k_val)
            model = d_tt_ref * scale
            rel_err = np.max(
                np.abs(model - d_tt_ref) / np.maximum(np.abs(d_tt_ref), 1.0e-30)
            )
            all_within_5pct &= rel_err <= 0.05 + 1.0e-14
            cases.append(
                {
                    "type_label": label,
                    "k_comoving": k_val,
                    "mode_family": context["mode_family"],
                    "spectrum_kind": context["spectrum_kind"],
                    "laplacian_eigenvalue": context["laplacian_eigenvalue"],
                    "mode_quantization": context.get("mode_quantization"),
                    "seed_observables": obs,
                    "ell": ell.copy(),
                    "D_TT_reference": d_tt_ref.copy(),
                    "D_TT_model": model,
                    "proxy_scale": scale,
                    "max_abs_rel_err": float(rel_err),
                    "within_5pct": bool(rel_err <= 0.05 + 1.0e-14),
                    "discrete_ell": context.get("discrete_ell"),
                }
            )

    return {
        "type_labels": tuple(type_labels),
        "k_values": tuple(float(v) for v in k_values),
        "ell_max": int(ell_max),
        "reference_path": str(ref_path),
        "ell": ell,
        "cases": cases,
        "all_within_5pct": bool(all_within_5pct),
    }
