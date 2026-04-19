"""
bass/tilt/baryon_only_policy.py  (Week 1 Day 4)
================================================

Species registry enforcing the baryon-only tilt architecture.

Architecture (VER04 production decision)
----------------------------------------
In the multi-fluid Bianchi framework, tilt is the relative velocity of matter
relative to the geometry frame. The BASS-py production architecture enforces:

    v_cdm      = 0        (geometry-frame comoving)
    v_gamma    = 0        (geometry-frame comoving at background)
    v_nu       = 0        (geometry-frame comoving; free-streaming)
    v_baryon   = β̄ ê      (global tilt)
    v_electron = v_baryon (tight-coupling, electron-frame Thomson)

Rationale
---------
1. Baryons are the species primarily traced by matter-dipole observations
   (CatWISE quasars, NVSS/RACS radio sources, CF4 galaxies → all trace
   baryonic mass).
2. CDM has no electromagnetic interaction; it is "invisible" to the matter
   dipole observables and remains in the geometry frame.
3. Photons participate in tilt only through Thomson scattering off baryon
   electrons, which introduces TT+EE signatures rather than a direct
   background velocity.
4. Neutrinos free-stream after decoupling; their velocity is pinned to the
   initial (geometry-frame) frame.

Observational consequence
-------------------------
- Global β̄ (cosmological, pre-recombination): affects BOTH TT and EE
  through Thomson-coupled baryon velocity
- Local v_loc (observer patch, post-recombination): affects only TT
  (Doppler boost of observed spectrum, no EE contribution)

The local patch is implemented Day 5 via `channel_routing.py`; the global
baryon-tilt architecture is implemented here.

Paper I connection
------------------
Each species has its own Teff manifold (Paper I §VI.A). The registry
carries metadata about:
  - Species statistics ξ ∈ {+1 (BE), 0 (MB), -1 (FD)}
  - Teff representation type (one-field / two-field / none)
  - Thomson coupling participation

This metadata feeds into:
  - `bass/teff/species_tangency.py` (Week 3): per-species D_{s,≥2} diagnostic
  - `bass/tilt/channel_routing.py` (Day 5): global-vs-local routing
  - `bass/solver/tilted_electron_frame.py` (existing): electron-frame Thomson

References
----------
  ch03_framework.tex §sec:multi-fluid, §sec:species-resolved
  ch09_discussion.tex §sec:disc-local-patch (TT-vs-EE separation)
  Paper I (Park-Cheoun-Park 2026) §VI.A (per-ray exponential family)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import numpy as np


# ═══════════════════════════════════════════════════════════════
# §1 — Species enumeration and metadata
# ═══════════════════════════════════════════════════════════════

class Species(Enum):
    """Cosmological species tracked by BASS.

    The standard cosmological matter content comprises:
      - photons (γ): Bose-Einstein
      - four neutrino flavours (ν_e, ν̄_e, ν_x, ν̄_x): Fermi-Dirac
      - cold dark matter (CDM): effectively classical, pressureless
      - baryons: classical, pressureless at recombination
      - electrons: classical, tightly coupled to baryons pre-recombination
    """
    GAMMA = "gamma"
    NU_E = "nu_e"
    NU_E_BAR = "nu_e_bar"
    NU_X = "nu_x"
    NU_X_BAR = "nu_x_bar"
    CDM = "cdm"
    BARYON = "baryon"
    ELECTRON = "electron"


class TeffRepresentation(Enum):
    """Paper I Teff manifold representation per species."""
    ONE_FIELD = "one_field"      # Θ only (photons, μ=0)
    TWO_FIELD = "two_field"      # (Θ, η) — Paper II extension (neutrinos)
    NONE = "none"                # no Teff (CDM, baryons — pressureless)


class Statistics(Enum):
    """Quantum statistics parameter ξ (Paper I Eq. 12)."""
    BE = +1   # Bose-Einstein
    FD = -1   # Fermi-Dirac
    MB = 0    # Maxwell-Boltzmann (classical limit)


@dataclass(frozen=True)
class SpeciesMetadata:
    """Static metadata per species."""
    species: Species
    statistics: Statistics
    teff_type: TeffRepresentation
    has_thomson_coupling: bool       # participates in γ-e Thomson scattering
    can_carry_tilt: bool             # whether tilt is allowed on this species
    description: str = ""

    @property
    def xi(self) -> int:
        return self.statistics.value


# Canonical species metadata registry — the single source of truth
SPECIES_METADATA: Dict[Species, SpeciesMetadata] = {
    Species.GAMMA: SpeciesMetadata(
        species=Species.GAMMA,
        statistics=Statistics.BE,
        teff_type=TeffRepresentation.ONE_FIELD,
        has_thomson_coupling=True,
        can_carry_tilt=False,    # no background tilt (only perturbative via Thomson)
        description="CMB photons (BE, Paper I scope)",
    ),
    Species.NU_E: SpeciesMetadata(
        species=Species.NU_E,
        statistics=Statistics.FD,
        teff_type=TeffRepresentation.TWO_FIELD,
        has_thomson_coupling=False,
        can_carry_tilt=False,    # free-streaming, geometry-frame comoving
        description="electron neutrinos (FD, Paper II 2-field)",
    ),
    Species.NU_E_BAR: SpeciesMetadata(
        species=Species.NU_E_BAR,
        statistics=Statistics.FD,
        teff_type=TeffRepresentation.TWO_FIELD,
        has_thomson_coupling=False,
        can_carry_tilt=False,
        description="electron antineutrinos",
    ),
    Species.NU_X: SpeciesMetadata(
        species=Species.NU_X,
        statistics=Statistics.FD,
        teff_type=TeffRepresentation.TWO_FIELD,
        has_thomson_coupling=False,
        can_carry_tilt=False,
        description="muon/tau neutrinos",
    ),
    Species.NU_X_BAR: SpeciesMetadata(
        species=Species.NU_X_BAR,
        statistics=Statistics.FD,
        teff_type=TeffRepresentation.TWO_FIELD,
        has_thomson_coupling=False,
        can_carry_tilt=False,
        description="muon/tau antineutrinos",
    ),
    Species.CDM: SpeciesMetadata(
        species=Species.CDM,
        statistics=Statistics.MB,
        teff_type=TeffRepresentation.NONE,
        has_thomson_coupling=False,
        can_carry_tilt=False,    # geometry-frame comoving (no EM interaction)
        description="cold dark matter (no EM, no Teff)",
    ),
    Species.BARYON: SpeciesMetadata(
        species=Species.BARYON,
        statistics=Statistics.MB,
        teff_type=TeffRepresentation.NONE,
        has_thomson_coupling=False,   # direct Thomson via electrons, not baryons
        can_carry_tilt=True,     # the species that carries the tilt
        description="baryons (primary tilt-carrier)",
    ),
    Species.ELECTRON: SpeciesMetadata(
        species=Species.ELECTRON,
        statistics=Statistics.MB,
        teff_type=TeffRepresentation.NONE,
        has_thomson_coupling=True,    # tight-coupled to baryons pre-recombination
        can_carry_tilt=True,     # via tight-coupling to baryons
        description="free electrons (tight-coupled to baryons)",
    ),
}


# ═══════════════════════════════════════════════════════════════
# §2 — Species registry (stateful)
# ═══════════════════════════════════════════════════════════════

class BaryonOnlyPolicyViolation(ValueError):
    """Raised when an operation would violate the baryon-only tilt invariant."""
    pass


@dataclass
class SpeciesRegistry:
    """Registry enforcing baryon-only tilt architecture.

    Invariants
    ----------
    I1. v_cdm = 0      — CDM is geometry-frame comoving.
    I2. v_gamma = 0    — photons are at-rest at background.
    I3. v_nu = 0       — neutrinos free-stream in the geometry frame.
    I4. v_electron = v_baryon — tight-coupling constraint.
    I5. Only baryon+electron can have nonzero velocity.

    The invariants are checked after every construction and state modification
    (`validate_baryon_only_invariant`); any violation raises
    `BaryonOnlyPolicyViolation`.
    """
    beta_bar: float = 0.0
    direction: np.ndarray = field(default_factory=lambda: np.array([1.0, 0.0, 0.0]))
    # Internal state: velocity 3-vector per species (units of c)
    _velocities: Dict[Species, np.ndarray] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize all species velocities consistent with baryon-only policy."""
        norm = np.linalg.norm(self.direction)
        if norm < 1e-15:
            raise ValueError(f"direction must be nonzero, got {self.direction}")
        # Store as normalized unit vector
        self.direction = np.asarray(self.direction, dtype=float) / norm

        # Build velocity dict
        self._velocities.clear()
        for sp in Species:
            if sp in (Species.BARYON, Species.ELECTRON):
                # Tilt carriers: v = β̄ ê
                self._velocities[sp] = self.beta_bar * self.direction.copy()
            else:
                # All others: v = 0 (geometry-frame comoving)
                self._velocities[sp] = np.zeros(3)

        self.validate_baryon_only_invariant()

    # ── Queries ──

    def get_velocity(self, species: Species) -> np.ndarray:
        """Retrieve velocity 3-vector for a species (units of c).

        Returns a copy so external callers cannot mutate internal state.
        """
        if species not in self._velocities:
            raise KeyError(f"Species {species} not in registry")
        return self._velocities[species].copy()

    def get_velocity_magnitude(self, species: Species) -> float:
        """Retrieve |v|/c for a species."""
        return float(np.linalg.norm(self.get_velocity(species)))

    def metadata(self, species: Species) -> SpeciesMetadata:
        """Retrieve static metadata for a species."""
        return SPECIES_METADATA[species]

    def get_xi(self, species: Species) -> int:
        """Paper I statistics parameter ξ ∈ {-1, 0, +1}."""
        return SPECIES_METADATA[species].xi

    # ── Role queries ──

    def tilt_carriers(self) -> List[Species]:
        """Species permitted to carry tilt under baryon-only policy."""
        return [sp for sp in Species
                if SPECIES_METADATA[sp].can_carry_tilt]

    def non_tilt_species(self) -> List[Species]:
        """Species required to be geometry-frame comoving."""
        return [sp for sp in Species
                if not SPECIES_METADATA[sp].can_carry_tilt]

    def thomson_participants(self) -> List[Species]:
        """Species participating in Thomson scattering."""
        return [sp for sp in Species
                if SPECIES_METADATA[sp].has_thomson_coupling]

    def species_with_teff(
        self, teff_type: Optional[TeffRepresentation] = None,
    ) -> List[Species]:
        """Species with a Teff representation.

        Parameters
        ----------
        teff_type : TeffRepresentation, optional
            Filter for one-field or two-field; None returns all non-NONE species.
        """
        result = []
        for sp in Species:
            meta = SPECIES_METADATA[sp]
            if teff_type is None:
                if meta.teff_type != TeffRepresentation.NONE:
                    result.append(sp)
            else:
                if meta.teff_type == teff_type:
                    result.append(sp)
        return result

    # ── Invariant enforcement ──

    def validate_baryon_only_invariant(self) -> None:
        """Check all invariants I1–I5. Raises on any violation."""
        # I1-3: non-tilt species have exactly zero velocity
        for sp in self.non_tilt_species():
            v = self._velocities[sp]
            if np.linalg.norm(v) > 1e-15:
                raise BaryonOnlyPolicyViolation(
                    f"[I1-3] Species '{sp.value}' has |v| = {np.linalg.norm(v):.3e} "
                    f"but baryon-only policy requires it to be geometry-frame comoving "
                    f"(v = 0)."
                )
        # I4: tight-coupling v_electron = v_baryon
        v_b = self._velocities[Species.BARYON]
        v_e = self._velocities[Species.ELECTRON]
        if not np.allclose(v_b, v_e, atol=1e-15):
            raise BaryonOnlyPolicyViolation(
                f"[I4] Tight-coupling violated: v_baryon = {v_b}, v_electron = {v_e}"
            )
        # I5: by construction; the above checks cover this

    # ── Mutations (with enforcement) ──

    def set_velocity_if_allowed(
        self, species: Species, v: np.ndarray,
    ) -> None:
        """Set velocity for a species, subject to policy.

        Raises
        ------
        BaryonOnlyPolicyViolation
            If species is a non-tilt-carrier and a nonzero velocity is requested.
        """
        meta = SPECIES_METADATA[species]
        v_arr = np.asarray(v, dtype=float)
        if not meta.can_carry_tilt and np.linalg.norm(v_arr) > 1e-15:
            raise BaryonOnlyPolicyViolation(
                f"Cannot set v = {v_arr} for '{species.value}': "
                f"baryon-only policy requires v = 0 for non-tilt species."
            )
        self._velocities[species] = v_arr.copy()
        # Tight-coupling: if setting baryon, also update electron (and vice versa)
        if species == Species.BARYON:
            self._velocities[Species.ELECTRON] = v_arr.copy()
        elif species == Species.ELECTRON:
            self._velocities[Species.BARYON] = v_arr.copy()
        self.validate_baryon_only_invariant()

    def set_tilt(
        self, beta_bar: float,
        direction: Optional[np.ndarray] = None,
    ) -> None:
        """Update tilt (baryon+electron) coherently.

        Parameters
        ----------
        beta_bar : float
            New tilt rapidity magnitude.
        direction : np.ndarray, optional
            New direction. If None, keep current direction.
        """
        self.beta_bar = beta_bar
        if direction is not None:
            d = np.asarray(direction, dtype=float)
            norm = np.linalg.norm(d)
            if norm < 1e-15:
                raise ValueError(f"direction must be nonzero, got {d}")
            self.direction = d / norm

        v = beta_bar * self.direction
        self._velocities[Species.BARYON] = v.copy()
        self._velocities[Species.ELECTRON] = v.copy()
        self.validate_baryon_only_invariant()

    # ── Summary ──

    def list_species(self) -> List[Species]:
        return list(Species)

    def summary(self) -> Dict:
        """Structured summary of the current registry state."""
        return {
            'policy': 'baryon-only',
            'beta_bar': self.beta_bar,
            'direction': self.direction.tolist(),
            'velocity_magnitudes': {
                sp.value: self.get_velocity_magnitude(sp) for sp in Species
            },
            'tilt_carriers': [sp.value for sp in self.tilt_carriers()],
            'non_tilt_species': [sp.value for sp in self.non_tilt_species()],
            'thomson_participants': [sp.value for sp in self.thomson_participants()],
            'invariant_satisfied': True,  # would have raised if not
        }


# ═══════════════════════════════════════════════════════════════
# §3 — Factory and convenience functions
# ═══════════════════════════════════════════════════════════════

def make_flrw_registry() -> SpeciesRegistry:
    """FLRW (no tilt): β̄ = 0, all species geometry-frame comoving."""
    return SpeciesRegistry(beta_bar=0.0, direction=np.array([1.0, 0.0, 0.0]))


def make_tilted_registry(
    beta_bar: float,
    direction: Optional[np.ndarray] = None,
) -> SpeciesRegistry:
    """Cosmological tilt with baryon-only activation.

    Parameters
    ----------
    beta_bar : float
        Tilt rapidity magnitude. Production CF4 value ~ 1.36e-3.
    direction : np.ndarray, optional
        Unit direction vector. Defaults to +x̂.

    Returns
    -------
    SpeciesRegistry
        Validated registry with baryon-only invariant satisfied.
    """
    if direction is None:
        direction = np.array([1.0, 0.0, 0.0])
    return SpeciesRegistry(beta_bar=beta_bar, direction=direction)


def activate_baryon_tilt(
    registry: SpeciesRegistry,
    beta_bar: float,
    direction: Optional[np.ndarray] = None,
) -> SpeciesRegistry:
    """Apply new tilt parameters to an existing registry (returns new registry).

    Convenience wrapper that preserves immutable-style usage.
    """
    dir_use = direction if direction is not None else registry.direction
    return SpeciesRegistry(beta_bar=beta_bar, direction=dir_use)


# ============================================================================
# Section 6 - VT-07 beta policy gate (Week 3 Day 2, merged v4.1)
# ============================================================================
#
# The VT-07 frame-attribution correction (documented in userMemories and the
# thesis VT-07 prompt) bounds the tilt rapidity magnitude |β| by the corrected
# safe-route limit ε_1 / (1 + η_{u̇}), where ε_1 is the first Pastén ε
# parameter and η_{u̇} is the four-acceleration frame-attribution factor.
# The ~16% frame-attribution bias on the naive route is absorbed through the
# (1 + η_{u̇}) denominator.
#
# A factor-2 `safety_margin` buffer (default 0.5) keeps production runs clear
# of the bound edge.

BETA_SAFETY_MARGIN_DEFAULT: float = 0.5
"""Production factor-2 buffer on the VT-07 safe route.

Rationale per CANONICAL_DECISION_DESIGN.md §2.1. TODO: migrate to ssot.py
when that module lands (W5+ integration).
"""


def beta_policy_gate(
    beta: float,
    epsilon_1: float,
    eta_u_dot: float,
    safety_margin: float = BETA_SAFETY_MARGIN_DEFAULT,
) -> "tuple[bool, dict]":
    """VT-07 frame-attribution-corrected safe-route gate.

    The safe route:

        |β| ≤ safety_margin × ε_1 / (1 + η_{u̇})

    Parameters
    ----------
    beta : float
        Tilt rapidity. The gate compares |β| against the threshold so sign is
        immaterial; diagnostics report the signed value.
    epsilon_1 : float
        First Pastén ε parameter. Must be positive.
    eta_u_dot : float
        Four-acceleration frame-attribution factor. Non-negative by
        construction (magnitude-like).
    safety_margin : float, optional
        Factor ∈ (0, 1] applied to the naive threshold. Default 0.5
        (production).

    Returns
    -------
    (passed, diagnostics) : tuple[bool, dict]
        `passed` — True iff |β| ≤ threshold.
        `diagnostics` — keys: `beta`, `epsilon_1`, `eta_u_dot`,
        `safety_margin`, `threshold`, `fractional_slack`.

    Raises
    ------
    ValueError
        Invalid inputs (non-positive ε_1, negative η_{u̇}, bad safety_margin).
    """
    if not (epsilon_1 > 0):
        raise ValueError(f"epsilon_1 must be positive, got {epsilon_1}")
    if eta_u_dot < 0:
        raise ValueError(
            f"eta_u_dot must be non-negative (magnitude-like), got {eta_u_dot}"
        )
    if not (0 < safety_margin <= 1):
        raise ValueError(
            f"safety_margin must be in (0, 1], got {safety_margin}"
        )

    beta_abs = abs(float(beta))
    threshold = safety_margin * float(epsilon_1) / (1.0 + float(eta_u_dot))
    passed = beta_abs <= threshold

    fractional_slack = (
        (threshold - beta_abs) / threshold if threshold > 0 else 0.0
    )

    diagnostics = {
        "beta": float(beta),
        "epsilon_1": float(epsilon_1),
        "eta_u_dot": float(eta_u_dot),
        "safety_margin": float(safety_margin),
        "threshold": float(threshold),
        "fractional_slack": float(fractional_slack),
    }
    return passed, diagnostics
