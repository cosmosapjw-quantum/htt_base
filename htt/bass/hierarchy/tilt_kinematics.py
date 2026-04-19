"""bass/hierarchy/tilt_kinematics.py (FB-3.2) — species-level tilt
adapters that feed ``hierarchy_rhs_photon``'s ``accel_vector`` /
``vorticity_vector`` kwargs.

FB-2.4 structurally pinned the ``accel_vector`` and ``vorticity_vector``
kwargs on ``hierarchy_rhs_photon`` (and by forward
``hierarchy_rhs_neutrino``) — but every call site so far supplied
``None`` (zeros), keeping T4/T5/T6 identically zero. FB-3.2 closes the
loop: it exposes two small adapters that convert a
``TiltedSpeciesBackground(β, v̂_e)`` (the FB-3.1 wrapper) plus the
Bianchi ``StructureConstants`` of the spatial 3-space into the two
rank-1 vectors the driver already consumes, so callers can now route
**substantive** tilt content into T4, T5 and T6 via the existing driver
surface without re-opening FB-2.4 signatures.

The adapters guarantee a single non-negotiable invariant: **β = 0
returns ``np.zeros(3)`` bit-for-bit, regardless of ``v̂_e`` or the
structure constants**. That short-circuit is what preserves the FB-2.4
11-type regression anchor (commit ``d7d25da``) as the new adapter chain
comes live — a caller wiring ``accel_vector = accel_from_tilt(...)`` on
a β=0 species produces exactly the same dy/dη as the prior caller that
passed ``accel_vector=None``.

Kinematic content (FB-3.2 scope)
--------------------------------
For a tilted fluid with 4-velocity ``u^a = γ(n^a + v^a)`` in the
Bianchi ``n^a`` frame (King-Ellis 1973 §3; Ellis-Maartens-MacCallum
2012 §5.4), the full tilt 4-acceleration carried by the species frame
is

    A^a = γ² [v̇^a + (Θ/3) v^a + σ^a_b v^b]          (EMM eq 5.17)

and the tilt-induced spatial vorticity at background is

    ω^a = (1/2) ε^{abc} ∇̃_b v_c  + (structure-constant induced piece)
        → (1/2) ε^{abc} a_b v_c   for Class B (Pontzen-Challinor 2009 §2)

FB-3.2 emits only the **species-specific leading kinematic 3-vectors**
of these decompositions — the pieces that depend on ``(β, v̂_e)`` and
the *local* structure constants of the spatial 3-space, but *not* on
the background shear ``σ_ab(η)`` or the expansion scalar ``Θ(η)``.
The latter two depend on the Einstein + tilt coupling that FB-3.3
closes; mixing them in here would either (i) silently duplicate FB-3.3
plumbing or (ii) reach outside the adapter's contract and hit private
attributes on ``SpeciesBackground``. Neither is acceptable under the
FB-3.2 non-goals. So the adapters emit

    A^a_FB32 := γ² v^a                                   (EMM eq 5.14
                                                          flux-density
                                                          direction /
                                                          King-Ellis §3
                                                          species-specific
                                                          piece)

    ω^a_FB32 := (1/2) ε^{abc} a_b v_c                    (Class B only;
                                                          Class A →
                                                          zeros)

with the understanding that FB-3.3 will *extend* (never replace) these
two expressions by adding the ``Θ/3 · v^a`` and ``σ^a_b v^b`` pieces to
``accel_from_tilt`` and the shear-induced vorticity piece to
``vorticity_from_tilt`` once the Einstein-frame σ/Θ surface is wired
through. Bit-identity on the β=0 path will remain the anchor through
FB-3.3 — every extra piece of that series is proportional to ``v^a``
and vanishes whenever β = 0.

P2 overlap (FB-3.1 carried, resolved in this rotation)
------------------------------------------------------
``bass.tilt.species_tilt.TiltedSpeciesParams`` carries an independent
Y-Block surface that takes a 3-vector ``v`` directly (no β + v̂_e
split). The two APIs map onto each other via the composition rule

    TiltedSpeciesParams(v = β · v̂_e)  ↔  TiltedSpeciesBackground(β, v̂_e)

and both ship unchanged from FB-3.1; the hierarchy driver side
(FB-3.2) consumes the LB-1-native ``TiltedSpeciesBackground`` form,
while the Y-Block full-decomposition ``decompose_tilted_species``
continues to serve ``q̃^a`` / ``π̃^ab`` callers that need the complete
``(μ, q, p, π)`` quartet. Callers mixing both must use the composition
rule exactly (see ``test_tilt_kinematics::test_K15_overlap_*``). The
formal unification audit (single-API target) is scheduled for FB-3.5
β-gate reparametrisation.

References
----------
- King & Ellis 1973, *CMP* 31, 209 §3-§4 (tilted 4-velocity +
  species-specific induced acceleration).
- Ellis, Maartens & MacCallum 2012, *Relativistic Cosmology* §5.3-§5.4
  eqs (5.14), (5.17) (exact tilt kinematics; no small-β linearisation).
- Pontzen & Challinor 2009, *MNRAS* 395 §2 (Class B vorticity from
  a_α × v leading piece).
- ``docs/lowell_bianchi/lowell_bianchi_solver_reference.md §7`` (tilt
  SSOT).
- ``docs/lowell_bianchi/00_conventions.md §2`` (v̂_e default; frame
  split rule).
- ``bass.hierarchy.hierarchy_rhs.hierarchy_rhs_photon`` (FB-2.4 ``accel_vector`` /
  ``vorticity_vector`` consumer).
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from bass.species.tilted import TiltedSpeciesBackground


__all__ = [
    "accel_from_tilt",
    "vorticity_from_tilt",
]


_ZERO3 = np.zeros(3, dtype=np.float64)
"""Module-local zeros(3) prototype for the β = 0 short-circuit. A fresh
copy is handed back on every call so callers may freely mutate without
leaking state across invocations."""


def accel_from_tilt(
    tilted: TiltedSpeciesBackground,
    eta: float,
    *,
    bg_table: Optional[object] = None,
    tetrad_state: Optional[object] = None,
) -> np.ndarray:
    """Species-specific tilt 4-acceleration piece for T4 / T5.

    Returns the ``(3,)`` vector that ``hierarchy_rhs_photon`` routes to
    ``T4_accel_divergence`` and ``T5_accel_gradient`` via its
    ``accel_vector`` kwarg.

    FB-3.2 surface (no kwargs): returns the species-specific leading
    placeholder ``A^a_FB32 = γ² v^a`` — a dimensionally-representative
    term whose β=0 limit is exactly zero. This is the path every
    caller that predates FB-3.3 has exercised and its value is
    anchored byte-for-byte by the FB-3.2 regression (commit
    ``fdb1d86``).

    FB-3.3 extension (optional ``bg_table`` and ``tetrad_state``
    kwargs): additively appends the Ellis-Maartens-MacCallum 2012
    eq (5.17) kinematic pieces to the FB-3.2 placeholder, giving

        A^a_FB33 = γ² v^a + γ² (Θ/3) v^a + γ² σ^a_b v^b

    where Θ(η) comes from ``bg_table.interp_Theta(eta)`` and σ_ab(η)
    comes from ``proper_shear_at_eta(eta, tetrad_state, a(η))`` (the
    proper-time shear; LB-2a audit F1 convention). The background
    pieces are additive so the FB-3.2 byte anchor survives whenever a
    caller passes neither kwarg (the else-branch is unreached).

    Each extra piece is proportional to ``v^a`` and therefore vanishes
    at β = 0 regardless of the kwargs — so the FB-2.4 driver anchor
    (β = 0 on 12 structure-constant labels) remains byte-identical
    along the extended path.

    Kwargs policy
    -------------
    ``bg_table=None, tetrad_state=None`` — FB-3.2 backward-compatible
      path. Returns ``γ² v^a``.
    ``bg_table!=None, tetrad_state=None`` — adds the Θ/3 piece only.
    ``bg_table=None, tetrad_state!=None`` — raises ``ValueError``:
      ``proper_shear_at_eta`` needs ``a(η)`` from the ``bg_table`` to
      convert the tetrad state's conformal Σ_ab to proper-time σ_ab.
    ``bg_table!=None, tetrad_state!=None`` — full EMM eq (5.17)
      additive form.

    Parameters
    ----------
    tilted : TiltedSpeciesBackground
        Species-level tilt wrapper (FB-3.1). Only ``tilted.beta`` and
        ``tilted.v_vector(eta)`` are consulted; the thermodynamic
        surface is untouched.
    eta : float
        Conformal time [Mpc] at which to evaluate ``v^a``, ``Θ``, ``σ``.
    bg_table : FLRWBackgroundTable or None
        Optional FB-3.3 kwarg. Supplies ``interp_Theta(eta)`` and
        ``interp_a(eta)``.
    tetrad_state : TetradBackgroundState or None
        Optional FB-3.3 kwarg. Supplies the conformal-Σ_ab history;
        consumed via ``proper_shear_at_eta`` (cached spline per
        tetrad_state instance).

    Returns
    -------
    ndarray of shape ``(3,)``, float64
        Species-specific tilt acceleration 3-vector in the orthonormal
        tetrad basis. At β = 0 strictly zero (fresh copy) on every
        kwargs path.

    Raises
    ------
    ValueError
        If ``tetrad_state`` is supplied without ``bg_table``, or if
        ``v_vector`` returns a non-(3,) shape.

    Reference: King & Ellis 1973 §3-§4; EMM 2012 §5.4 eq (5.14), eq
    (5.17); lowell §7; LB-2a audit F1 (σ convention);
    FB-3.3 audit §FB-3.3 (additive policy rationale).
    """
    if tilted.beta == 0.0:
        return _ZERO3.copy()
    v = np.asarray(tilted.v_vector(float(eta)), dtype=np.float64)
    if v.shape != (3,):
        raise ValueError(
            f"TiltedSpeciesBackground.v_vector must return shape (3,) at "
            f"scalar η; got {v.shape}"
        )
    gamma_sq = tilted.gamma_sq
    accel = gamma_sq * v

    if tetrad_state is not None and bg_table is None:
        raise ValueError(
            "accel_from_tilt: tetrad_state requires bg_table (a(η) is "
            "needed for the conformal→proper σ conversion). Pass "
            "bg_table alongside tetrad_state, or leave both None for "
            "the FB-3.2 backward-compatible path."
        )

    if bg_table is not None:
        Theta = float(bg_table.interp_Theta(float(eta)))
        accel = accel + gamma_sq * (Theta / 3.0) * v

    if tetrad_state is not None:
        # proper-time σ_ab via the same helper hierarchy_rhs_photon uses.
        from bass.hierarchy.hierarchy_rhs import proper_shear_at_eta
        a_val = float(bg_table.interp_a(float(eta)))
        sigma = proper_shear_at_eta(float(eta), tetrad_state, a_val)
        accel = accel + gamma_sq * (sigma @ v)

    return accel


def vorticity_from_tilt(
    tilted: TiltedSpeciesBackground,
    eta: float,
    structure: Optional[object] = None,
    *,
    bg_table: Optional[object] = None,
) -> np.ndarray:
    """Tilt-induced vorticity 3-vector for T6.

    Returns the ``(3,)`` vector that ``hierarchy_rhs_photon`` routes to
    ``T6_vorticity`` via its ``vorticity_vector`` kwarg.

    FB-3.2 surface (``bg_table=None``): returns the Pontzen-Challinor
    §2 leading static piece

        ω^a_FB32 = (1/2) ε^{abc} a_b v_c

    with ``a_b = (0, a_twist, 0)`` per the Ellis-MacCallum
    ``(n^{ab}, a_α)`` split convention. At β = 0 or Class A
    (``a_twist = 0``) returns a fresh zero vector.

    FB-3.4 extension (``bg_table`` supplied): multiplies the FB-3.2
    static piece by the conformal-time dilution factor
    ``(a(η_today) / a(η))²`` — the EMM §6.4 leading-order vorticity
    propagation
    ``ω × a² = const`` on the background (vorticity is diluted by
    expansion). This makes the vector explicitly η-dependent
    (*dynamic* rather than purely *structural*): a caller running the
    hierarchy forward now sees T6 contribute a time-varying source
    into the ℓ = 1 multipole with the correct dilution scaling.
    FB-3.2 backward compatibility is preserved byte-for-byte when
    ``bg_table`` is left as ``None``.

    Parameters
    ----------
    tilted : TiltedSpeciesBackground
        Species-level tilt wrapper (FB-3.1).
    eta : float
        Conformal time [Mpc] at which to evaluate ``v^a`` and the
        dilution factor.
    structure : StructureConstants or None, optional
        Bianchi structure constants. Only ``structure.a_twist`` is
        read; other attributes are ignored. If ``None`` or
        ``a_twist = 0`` (Class A, FLRW, or Type I), returns zeros.
    bg_table : FLRWBackgroundTable or None, optional
        FB-3.4 kwarg. Supplies ``interp_a(eta)`` so the
        ``(a_today / a(η))²`` dilution factor can be applied.
        Default ``None`` preserves FB-3.2 surface byte-for-byte.

    Returns
    -------
    ndarray of shape ``(3,)``, float64
        Tilt-induced vorticity axial vector in the orthonormal tetrad
        basis. At β = 0, Class A, or ``structure is None`` strictly
        zero (fresh copy) on every kwargs path.

    Reference: Pontzen & Challinor 2009 §2; EMM 2012 §5.4, §6.4
    (vorticity propagation `ω̇ = −(2/3) Θ ω + …` integrates to
    `ω × a² = const` at leading order); ``00_conventions §3``;
    ``bass.background.bianchi_types`` (Ellis-MacCallum split
    ``a_α = (0, a_twist, 0)``).
    """
    if tilted.beta == 0.0:
        return _ZERO3.copy()
    if structure is None:
        return _ZERO3.copy()
    a_twist = float(getattr(structure, "a_twist", 0.0))
    if a_twist == 0.0:
        return _ZERO3.copy()
    v = np.asarray(tilted.v_vector(float(eta)), dtype=np.float64)
    if v.shape != (3,):
        raise ValueError(
            f"TiltedSpeciesBackground.v_vector must return shape (3,) at "
            f"scalar η; got {v.shape}"
        )
    a_vec = np.array([0.0, a_twist, 0.0], dtype=np.float64)
    # ω^a = (1/2) ε^{abc} a_b v_c = (1/2) a × v (right-handed cross).
    base = 0.5 * np.cross(a_vec, v)

    if bg_table is None:
        return base

    # FB-3.4 dynamic dilution: ω × a² = const (EMM §6.4 leading order)
    a_today = float(bg_table.interp_a(float(bg_table.eta_today)))
    a_at_eta = float(bg_table.interp_a(float(eta)))
    if a_at_eta <= 0.0:
        raise ValueError(
            f"bg_table.interp_a returned non-positive a(η)={a_at_eta!r} at "
            f"η={eta!r}; cannot apply (a_today/a)^2 dilution."
        )
    damping = (a_today / a_at_eta) ** 2
    return base * damping
