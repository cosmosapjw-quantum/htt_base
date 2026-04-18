# LB-1 — Species Background Evolution Specification

**Session LB-1**. Produces `bass/species/` subpackage: one background module per species, an ABC, a registry, and a test suite.

**Prerequisites**:
- LB-0 (`00_conventions.md`) — signature, units, SSOT, PSTF convention
- Y-Block `bass.tilt.species_tilt` (v → T_ab decomposition; already in repository)
- `bass.background.bianchi_types.StructureConstants` (already)
- `bass.background.einstein_bianchi.BianchiCosmology` (already)
- `bass.background.tetrad_state.TetradBackgroundState` (Y-Block)
- `bass.recombination.recombination_ingest.RecombinationInterp` (already — HyRec fixture)

**Size estimate**: ~800 LoC implementation + ~600 LoC tests.

**Reference material** for this session (no other chapter reading required):

- **Ellis §5.1–5.4** — general matter treatment, perfect fluid T_ab, multi-fluid system, equations of state
- **Kolb §3.3** — equilibrium thermodynamics, distribution functions
- **Kolb §3.4** — entropy per comoving volume, temperature-scale-factor relations
- **Kolb §3.5** — brief thermal history (temperatures + redshifts of key events)
- **Kolb §5.4** — recombination (Saha, Peebles C-factor, freeze-out)
- **Kolb §5.5** — neutrino cosmology, T_ν = (4/11)^{1/3} T_γ derivation
- **Baumann §3.6** — neutrinos, massive-neutrino horizon
- **Baumann §3.10** — recombination and decoupling

---

## Table of contents

1. Physical content per species
2. Software architecture — ABC, concrete classes, registry
3. Data contracts
4. Unit sanity — cross-species consistency
5. Interaction couplings
6. Initial conditions
7. Edge cases
8. Test criteria (exact numerical targets)
9. Implementation checklist
10. Cite map (code comment ↔ textbook equation)

---

## 1. Physical content per species

For each species we specify: (a) rest-frame thermodynamic state, (b) equation of state, (c) number-density evolution, (d) energy-density evolution, (e) interactions with other species, (f) initial conditions.

**Universal baseline** (applies to every species at background level):

- The orthogonal-Bianchi case has 4-velocity u_(s)^a = n^a. Tilted case is u_(s)^a = γ_s (n^a + v_(s)^a); the decomposition machinery for tilted species already exists in `bass.tilt.species_tilt` and is NOT re-implemented here — LB-1 uses it.
- Continuity in the 1+3 covariant form (Ellis §5.3):

  **ρ̇_s + Θ (ρ_s + p_s) + D^a q_a^(s) = C_s**

  where the overdot is `d/dτ` = `u^a ∇_a`, Θ is the expansion scalar (Θ = 3𝓗/a at background), `q_a^(s)` is species momentum density (zero at orthogonal background), and `C_s` is the collision loss/gain per unit proper time.

- For background in the orthogonal case with u^a = n^a, D^a q_a^(s) = 0 and C_s depends only on species identity and local temperature. Equation reduces to

  **ρ̇_s + Θ (ρ_s + p_s) = C_s**

  which in η-parameterisation is `ρ_s'(η) + 3𝓗 (1 + w_s) ρ_s = a C_s`.

### 1.1 Photon (γ)

| Item | Value | Citation |
|---|---|---|
| Equation of state | p_γ = ρ_γ / 3, w_γ = 1/3 (always) | Kolb §3.3 eq (3.51) |
| Rest-frame energy density | ρ_γ = (π² / 15) g_*γ T_γ⁴ with g_*γ = 2 | Kolb §3.3 eq (3.54) |
| Temperature scaling (entropy-conserving) | T_γ × a = const, with step at e⁺e⁻ annihilation (Kolb §5.5) | Kolb eq (5.13) |
| Today's value | T_γ,0 = 2.7255 K | Fixsen 2009 (SSOT C.T0_K) |
| Energy density fraction today | Ω_γ,0 = (π² / 15) × g_*γ × T_γ,0⁴ / ρ_crit,0 ≈ 5.39 × 10⁻⁵ | derived |
| Continuity equation (orthogonal) | ρ̇_γ + (4/3) Θ ρ_γ = C_γ | Ellis §5.3 |
| Collision with baryons (Thomson) | C_γ = 0 at background (exchange is with dipole Θ₁, not monopole ρ_γ) | Ellis §5.5 |
| Phase-space | Bose-Einstein with μ_γ = 0, T = T_γ | Kolb §3.3 |
| Initial condition at η_i (z_i ≈ 10⁷) | T_γ(η_i) = T_γ,0 × (1 + z_i); ρ_γ derived | |

**Key identity enforced in code**:

  `ρ_γ(a) = Ω_γ,0 / a⁴`   (exact entropy-conservation, no annihilation reheating past the standard model epoch we resolve)

- e⁺e⁻ annihilation is at z ~ 10⁹, well before any η-grid we integrate. The temperature step it induces is *already baked into* T_γ,0 and the (4/11)^{1/3} ν ratio.

### 1.2 Neutrino (ν)

| Item | Value | Citation |
|---|---|---|
| Equation of state (massless) | p_ν = ρ_ν / 3, w_ν = 1/3 | Kolb §5.5 |
| Rest-frame energy density (massless) | ρ_ν = (7/8) × (T_ν / T_γ)⁴ × N_eff × ρ_γ | Kolb eq (5.17) |
| T_ν / T_γ ratio after e⁺e⁻ annihilation | (4/11)^{1/3} | Kolb eq (5.14) |
| Effective number | N_eff = 3.044 (Planck 2018 incl. QED corrections) | Planck 2018 |
| Decoupling redshift | z_dec,ν ≈ 10¹⁰ (T ~ 1 MeV, Γ_wk ~ H) | Kolb §5.5 |
| Collisionless assumption | valid for all η on our grid (z < 10⁸) | Kolb §5.5 |
| Continuity (orthogonal, massless) | ρ̇_ν + (4/3) Θ ρ_ν = 0 | Ellis §5.3 |
| Today's value | Ω_ν,0 = (7/8) × (4/11)^{4/3} × 3.044 × Ω_γ,0 ≈ 3.83 × 10⁻⁵ | derived |
| Phase-space | Fermi-Dirac with μ_ν ≈ 0, T = T_ν | Kolb §3.3 |

**Massive-neutrino extension (deferred)**: when m_ν ≲ 3 T_ν the fluid behaviour transitions from w = 1/3 to w → 0. For `Σ m_ν = 0.06 eV` the transition happens around `z_mν ≈ 185`. **LB-1 assumes massless** for all three generations; a massive-neutrino upgrade hook in the API accepts `m_nu_eV: float = 0.0` but treats any non-zero value as a `NotImplementedError` for now (explicit, not silent).

**Key identity enforced in code**:

  `ρ_ν(a) = Ω_ν,0 / a⁴`   (exact in massless limit)

### 1.3 Baryon (b)

Baryons are the species where bass_py has the *most existing infrastructure* and the *most subtle couplings*. LB-1 consumes existing machinery rather than re-derive.

| Item | Value | Citation |
|---|---|---|
| Composition (post-BBN) | mostly ionised H + neutral He4, mass fractions X_H ≈ 0.755, Y_He ≈ 0.245 | Kolb Ch 4 |
| Equation of state | p_b = n_b k_B T_m × (1 / m̄_b), where m̄_b is mean baryon mass | Kolb §3.3 |
| Sound speed² | c_s,b² = (p_b/ρ_b) × (∂ ln T_m / ∂ ln a + ...) ≈ (5/3) × (T_m / m_b) at late time | Baumann §3.10 |
| Tight-coupling c_s² | c_s² = 1 / [3 (1 + R)] where R = (3/4) ρ_b / ρ_γ | Ma-Bertschinger 1995 |
| Rest-frame energy density | ρ_b = Ω_b,0 / a³ (dust) | |
| Number density | n_b(a) = Ω_b,0 ρ_crit,0 / (m_p × a³), m_p proton mass | |
| Ionisation fraction | x_e(z) from HyRec table (bass_py fixture) | Kolb §5.4 |
| Matter temperature | T_m(z) from HyRec table (follows T_γ until Compton decoupling z ~ 150, then T_m ∝ a⁻²) | Kolb §5.4 |
| Continuity (orthogonal) | ρ̇_b + Θ ρ_b = 0 (dust) | Ellis §5.3 |
| Interaction with γ | τ̇(z) = a n_e σ_T from HyRec | Kolb §5.4 |
| Today's value | Ω_b,0 = 0.0494 (h² = 0.02237 / h² with h = 0.6736) | Planck 2018 |

**Existing bass_py machinery consumed**:

- `bass.recombination.recombination_ingest.RecombinationInterp` supplies `x_e(z)`, `T_m(z)`, `τ̇(z)`, `κ(z)`, `g(z)` via cubic spline interpolation.
- `bass.recombination.reionization` supplies the `tanh` reionisation boost to x_e at z ≲ 8 with τ_reion = 0.054.
- LB-1's `BaryonBackground` is a **thin wrapper** that exposes these on an η-grid and implements the continuity equation for ρ_b.

**Key identity**:

  `ρ_b(a) = Ω_b,0 / a³`   (exact; baryons lose no energy to radiation at background because the coupling is quadrupole/dipole not monopole)

### 1.4 Cold dark matter (c)

| Item | Value | Citation |
|---|---|---|
| Equation of state | p_c = 0 exactly (first-pass CDM) | Kolb §9.1 |
| Sound speed | c_s,c = 0 | |
| Rest-frame energy density | ρ_c = Ω_c,0 / a³ | |
| Continuity (orthogonal) | ρ̇_c + Θ ρ_c = 0 | |
| Interactions | none (only gravitational) | |
| Today's value | Ω_c,0 = Ω_m,0 − Ω_b,0 = 0.3153 − 0.0494 = 0.2659 | |

**Key identity**:

  `ρ_c(a) = Ω_c,0 / a³`

### 1.5 Cosmological constant (Λ)

| Item | Value | Citation |
|---|---|---|
| Equation of state | p_Λ = −ρ_Λ, w_Λ = −1 | Ellis §5.1 |
| Rest-frame energy density | ρ_Λ = Ω_Λ,0 × ρ_crit,0 (constant in comoving frame) | |
| Continuity | ρ̇_Λ + Θ (ρ_Λ + p_Λ) = ρ̇_Λ + 0 = 0 ✓ | |
| Interactions | none | |
| Today's value | Ω_Λ,0 = 1 − Ω_m,0 − Ω_r,0 (flat universe) | |

**Key identity**:

  `ρ_Λ(a) = Ω_Λ,0`   (trivially exact)

---

## 2. Software architecture

### 2.1 Subpackage layout

```
bass_py/bass/species/
├── __init__.py             — public re-exports
├── constants.py            — Ω_X,0, T_γ,0, N_eff, etc. (mirror ssot.C)
├── base.py                 — SpeciesBackground ABC + common types
├── photon.py               — PhotonBackground(SpeciesBackground)
├── neutrino.py             — NeutrinoBackground(SpeciesBackground)
├── baryon.py               — BaryonBackground(SpeciesBackground)
├── cdm.py                  — CDMBackground(SpeciesBackground)
├── lambda_.py              — LambdaBackground(SpeciesBackground)
│                            (filename has trailing underscore: `lambda`
│                             is a Python reserved keyword and cannot
│                             appear in an `import` statement)
├── registry.py             — SpeciesBackgroundRegistry
├── test_constants.py       — bit-exact match with ssot.C
├── test_photon.py
├── test_neutrino.py
├── test_baryon.py
├── test_cdm.py
├── test_lambda.py
└── test_registry.py        — sum rules, Friedmann constraint
```

### 2.2 The `SpeciesBackground` ABC

```python
# bass/species/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np


class SpeciesLabel(Enum):
    """Canonical species ordering from 00_conventions.md §6."""
    PHOTON   = 'γ'
    NEUTRINO = 'ν'
    BARYON   = 'b'
    CDM      = 'c'
    LAMBDA   = 'Λ'


@dataclass(frozen=True)
class SpeciesSnapshot:
    """Rest-frame thermodynamic state at one η.

    For LB-1 all species are in thermal equilibrium or frozen-out; the
    snapshot captures only macroscopic quantities. LB-2 and later will
    add moments of the distribution function (Π_{A_ℓ}).
    """
    eta: float           # [Mpc]
    a: float             # scale factor
    rho: float           # ρ_X(a) [ρ_crit,0 units]
    p: float             # p_X(a) [ρ_crit,0 units]
    T: Optional[float]   # K, None if not defined (Λ, CDM)
    w: float             # p/ρ (defined as 0 when ρ = 0)


class SpeciesBackground(ABC):
    """Background (η-dependent) energy density and pressure of a species.

    All methods accept scalar or ndarray η in Mpc.  The ABC fixes the
    interface; concrete subclasses supply closed-form expressions or
    interpolations of precomputed tables.
    """

    label: SpeciesLabel  # class-level attribute set by subclass

    @abstractmethod
    def rho_rest(self, eta: np.ndarray) -> np.ndarray:
        """Rest-frame energy density ρ_X(η) in ρ_crit,0 units."""

    @abstractmethod
    def p_rest(self, eta: np.ndarray) -> np.ndarray:
        """Rest-frame pressure p_X(η) in ρ_crit,0 units."""

    def w(self, eta: np.ndarray) -> np.ndarray:
        """Equation of state parameter w_X = p_X / ρ_X."""
        rho = np.asarray(self.rho_rest(eta), dtype=np.float64)
        p = np.asarray(self.p_rest(eta), dtype=np.float64)
        out = np.zeros_like(rho)
        mask = rho > 0
        out[mask] = p[mask] / rho[mask]
        return out

    @abstractmethod
    def dot_rho(self, eta: np.ndarray) -> np.ndarray:
        """dρ_X/dη from the covariant continuity equation.

        Must equal −3𝓗(1 + w_X) ρ_X for an isolated species (no
        collision). Species that exchange with others override this
        to add the collision contribution.
        """

    def temperature(self, eta: np.ndarray) -> Optional[np.ndarray]:
        """Temperature T_X(η) in Kelvin. None if undefined (Λ, CDM)."""
        return None

    def snapshot(self, eta: float) -> SpeciesSnapshot:
        """Convenience container at one η."""
        rho = float(self.rho_rest(np.atleast_1d(eta))[0])
        p = float(self.p_rest(np.atleast_1d(eta))[0])
        w = p / rho if rho > 0 else 0.0
        T = self.temperature(np.atleast_1d(eta))
        T_val = float(T[0]) if T is not None else None
        return SpeciesSnapshot(
            eta=float(eta), a=self._a_of_eta(eta),
            rho=rho, p=p, T=T_val, w=w,
        )

    @abstractmethod
    def _a_of_eta(self, eta: float) -> float:
        """Scale factor at η. Subclasses must share a background table."""
```

### 2.3 Concrete class signatures

Each concrete class takes an **`FLRWBackgroundTable`** (a thin wrapper around `bass.background.einstein_bianchi.solve_bianchi_background` output, exposing `a(η)`, `𝓗(η)`, `Θ(η) = 3𝓗/a`). This table is built once and shared across species.

```python
# bass/species/photon.py
class PhotonBackground(SpeciesBackground):
    label = SpeciesLabel.PHOTON

    def __init__(self, bg_table: 'FLRWBackgroundTable',
                 Omega_gamma_0: float):
        ...

    # rho_rest(η) = Ω_γ,0 / a(η)⁴
    # p_rest(η) = rho_rest / 3
    # temperature(η) = T_γ,0 / a(η)    (no step past BBN epoch)
    # dot_rho(η) = −(4/3) Θ ρ_γ       (no collision at monopole)
```

```python
# bass/species/neutrino.py
class NeutrinoBackground(SpeciesBackground):
    label = SpeciesLabel.NEUTRINO

    def __init__(self, bg_table: 'FLRWBackgroundTable',
                 Omega_nu_0: float, N_eff: float = 3.044,
                 m_nu_eV: float = 0.0):
        if m_nu_eV != 0.0:
            raise NotImplementedError(
                "Massive neutrinos deferred; see 01_species_background_spec §1.2"
            )
        ...

    # rho_rest(η) = Ω_ν,0 / a(η)⁴
    # p_rest(η) = rho_rest / 3
    # temperature(η) = (4/11)^(1/3) × T_γ,0 / a(η)
    # dot_rho(η) = −(4/3) Θ ρ_ν
```

```python
# bass/species/baryon.py
from bass.recombination.recombination_ingest import RecombinationInterp

class BaryonBackground(SpeciesBackground):
    label = SpeciesLabel.BARYON

    def __init__(self, bg_table: 'FLRWBackgroundTable',
                 Omega_b_0: float,
                 recombination: RecombinationInterp):
        ...

    # rho_rest(η) = Ω_b,0 / a(η)³
    # p_rest(η) = 0 at strict background level
    #   (the sound speed c_s,b² matters only for perturbations; at
    #    background the baryon fluid is pressureless and equivalent
    #    to dust. LB-1 stays strictly at background, so p_rest = 0.)
    # temperature(η) = T_m(z(η)) from HyRec
    # x_e(η), tau_dot(η), visibility(η) exposed via helpers
    # dot_rho(η) = −Θ ρ_b
```

```python
# bass/species/cdm.py
class CDMBackground(SpeciesBackground):
    label = SpeciesLabel.CDM

    def __init__(self, bg_table: 'FLRWBackgroundTable',
                 Omega_c_0: float):
        ...

    # rho_rest(η) = Ω_c,0 / a(η)³
    # p_rest(η) = 0
    # temperature(η) = None
    # dot_rho(η) = −Θ ρ_c
```

```python
# bass/species/lambda.py
class LambdaBackground(SpeciesBackground):
    label = SpeciesLabel.LAMBDA

    def __init__(self, bg_table: 'FLRWBackgroundTable',
                 Omega_Lambda_0: float):
        ...

    # rho_rest(η) = Omega_Lambda_0   (constant)
    # p_rest(η) = −rho_rest          (w = −1)
    # temperature(η) = None
    # dot_rho(η) = 0                 (trivially)
```

### 2.4 The `FLRWBackgroundTable` helper

```python
# bass/species/base.py (continued) or bass/species/background_table.py

@dataclass
class FLRWBackgroundTable:
    """η-sampled FLRW background quantities shared across species.

    Built once from solve_bianchi_background(flrw_cosmology(), ...).
    All species consume the same instance.
    """
    eta: np.ndarray      # [Mpc]
    a: np.ndarray
    z: np.ndarray
    H_mpc: np.ndarray    # H/c in Mpc⁻¹
    calH_mpc: np.ndarray # conformal Hubble 𝓗 = a H/c
    Theta: np.ndarray    # expansion scalar 3 𝓗 / a

    def interp_a(self, eta: float) -> float: ...
    def interp_calH(self, eta: float) -> float: ...
    def interp_Theta(self, eta: float) -> float: ...
```

The table is built by a module-level factory:

```python
def build_flrw_background_table(
    a_start: float = 1e-8,
    a_end: float = 1.0,
    n_eta: int = 4000,
    cosmo: Optional[BianchiCosmology] = None,
) -> FLRWBackgroundTable:
    """Driver: solve the FLRW background once, return a shared table."""
```

### 2.5 The `SpeciesBackgroundRegistry`

```python
# bass/species/registry.py

class SpeciesBackgroundRegistry:
    """Immutable collection of all 5 species in canonical order.

    Provides total energy density, total pressure, and Friedmann-
    constraint residual at any η.
    """

    def __init__(self,
                 photon: PhotonBackground,
                 neutrino: NeutrinoBackground,
                 baryon: BaryonBackground,
                 cdm: CDMBackground,
                 lambda_: LambdaBackground):
        self._species = {
            SpeciesLabel.PHOTON:   photon,
            SpeciesLabel.NEUTRINO: neutrino,
            SpeciesLabel.BARYON:   baryon,
            SpeciesLabel.CDM:      cdm,
            SpeciesLabel.LAMBDA:   lambda_,
        }

    def __getitem__(self, label: SpeciesLabel) -> SpeciesBackground: ...

    def rho_total(self, eta: np.ndarray) -> np.ndarray:
        """Σ_s ρ_s(η)."""

    def p_total(self, eta: np.ndarray) -> np.ndarray:
        """Σ_s p_s(η)."""

    def friedmann_residual(self, eta: np.ndarray,
                            H_mpc: np.ndarray) -> np.ndarray:
        """Should be zero: (8πG/3) ρ_total × a² / c² − 𝓗² − a² k = 0."""

    @classmethod
    def from_planck2018(cls, bg_table: FLRWBackgroundTable,
                         recombination: RecombinationInterp
                        ) -> 'SpeciesBackgroundRegistry':
        """Factory: Planck 2018 Ω's, N_eff=3.044, m_ν=0."""
```

---

## 3. Data contracts

### 3.1 Return types

| Method | Input | Output | Units |
|---|---|---|---|
| `rho_rest(η)` | scalar or (N,) ndarray | same shape | ρ_crit,0 |
| `p_rest(η)` | scalar or (N,) ndarray | same shape | ρ_crit,0 |
| `w(η)` | scalar or (N,) ndarray | same shape | dimensionless |
| `dot_rho(η)` | scalar or (N,) ndarray | same shape | ρ_crit,0 / Mpc |
| `temperature(η)` | scalar or (N,) ndarray | same shape or None | Kelvin |

### 3.2 Broadcasting rule

All public methods accept either a Python float or a NumPy array. If input is `float`, return is `float`. If input is `ndarray`, return has same shape. No silent shape broadcasting between species — the caller must ensure shape compatibility.

### 3.3 Out-of-range behaviour

Each `SpeciesBackground` has an η-domain bounded by the `FLRWBackgroundTable` it was built with. Queries outside `[eta[0], eta[-1]]` raise `ValueError` — **no silent extrapolation**.

For baryons, the `RecombinationInterp` table's z-range further restricts: outside `[z_min_recomb, z_max_recomb]` the temperature T_m and x_e queries raise. LB-1 handles this in `BaryonBackground.__init__` by clipping its η-domain to the intersection.

---

## 4. Unit sanity — cross-species consistency

The following **must** hold at `η_today` (a = 1):

| Quantity | Expected | Tolerance |
|---|---|---|
| ρ_γ(1) | Ω_γ,0 ≈ 5.39e-5 | 1e-10 absolute |
| ρ_ν(1) | Ω_ν,0 ≈ 3.83e-5 | 1e-10 |
| ρ_b(1) | Ω_b,0 ≈ 0.0494 | 1e-6 |
| ρ_c(1) | Ω_c,0 ≈ 0.2659 | 1e-6 |
| ρ_Λ(1) | Ω_Λ,0 ≈ 0.6847 | 1e-10 |
| Σ ρ_s(1) | 1.000 (flat FLRW today) | 1e-5 |

The sum rule is enforced as a test in `test_registry.py`.

Additionally, at η_eq (matter-radiation equality):
- `ρ_γ + ρ_ν = ρ_b + ρ_c`
- Using bass_py's current Ω values, `z_eq = (Ω_m / Ω_r) − 1 ≈ 0.3153/9.22e-5 − 1 ≈ 3418`.

---

## 5. Interaction couplings

For LB-1 the background evolution is **decoupled** in a specific sense: each species' ρ̇ is determined by its own w and the expansion. The couplings that DO exist enter:

| Coupling | Between | Active at | Where it appears in LB-1 |
|---|---|---|---|
| Thomson scattering | γ ↔ b (via electrons) | all z (weights change) | **τ̇(η)** exposed by BaryonBackground; monopole-level C_γ = C_b = 0 |
| Neutrino decoupling | ν ↔ plasma | z ~ 10¹⁰ | already encoded in T_ν/T_γ = (4/11)^{1/3}; no dynamical coupling afterwards |
| Gravitational | all ↔ all | all z | via shared FLRW background |

At the background monopole level, the collision sources cancel pairwise (Thomson preserves photon number at background). Species **dipoles** (Π_1 in the hierarchy) do see the Thomson drag, but dipoles belong to the hierarchy (LB-2), not to the background (LB-1). Keep this separation clean.

---

## 6. Initial conditions

For LB-1 the "initial condition" is simply the normalisation at `a = 1` (today):

| Species | IC |
|---|---|
| γ | ρ_γ(1) = Ω_γ,0 |
| ν | ρ_ν(1) = Ω_ν,0 |
| b | ρ_b(1) = Ω_b,0 |
| c | ρ_c(1) = Ω_c,0 |
| Λ | ρ_Λ(1) = Ω_Λ,0 |

All a-dependence is then analytic (a⁻⁴, a⁻³, or constant) and no ODE integration is needed for LB-1. **LB-1 does not integrate anything** — it provides tables / closed-form functions.

Dynamical integration begins in LB-5 (the unified hierarchy integrator), where species enter as right-hand-side inputs.

---

## 7. Edge cases

The following must be handled explicitly (with tests):

1. **a → 0 (early time)**: `ρ_γ, ρ_ν → ∞`. Methods must produce `inf` (not NaN), and downstream code must be able to handle that.
2. **a → ∞ (far future)**: `ρ_γ → 0`, `ρ_Λ → const`. Should not produce underflow.
3. **η outside table range**: `ValueError` with informative message.
4. **Massive-neutrino requested**: `NotImplementedError` with pointer to this doc.
5. **Ω_b > Ω_m** (pathological): `ValueError` at registry construction — Ω_c would be negative.
6. **Ω_total ≠ 1** with flat cosmology: documented tolerance ±1e-4. Outside that, `ValueError`.
7. **Recombination table z-range doesn't cover η-grid**: `BaryonBackground` clips and logs a warning (not an error) because this affects only the `temperature` and `tau_dot` methods, not `rho_rest`.

---

## 8. Test criteria (exact numerical targets)

| # | Test | Target | Tolerance |
|---|---|---|---|
| T-01 | `rho_gamma(1) == Omega_gamma_0` | 5.39e-5 | 1e-10 rel |
| T-02 | `p_gamma / rho_gamma == 1/3` at all η | 0.33333 | 1e-15 abs |
| T-03 | `rho_gamma(a) * a**4 == Omega_gamma_0` | constant | 1e-12 rel |
| T-04 | `T_gamma(z=0) == 2.7255 K` | SSOT | 1e-8 |
| T-05 | `dot_rho_gamma / (−4/3 Θ rho_gamma) == 1` | 1.0 | 1e-12 |
| T-06 | `T_nu / T_gamma == (4/11)^(1/3)` | 0.71377 | 1e-12 |
| T-07 | `Omega_nu_0 / Omega_gamma_0 == (7/8) × (4/11)^(4/3) × 3.044` | exact | 1e-14 |
| T-08 | `rho_nu(a) * a**4 == Omega_nu_0` | constant | 1e-12 |
| T-09 | `rho_b(a) * a**3 == Omega_b_0` | constant | 1e-12 |
| T-10 | `p_b == 0` everywhere (background level) | 0 | 1e-30 abs |
| T-11 | `tau_dot` at z=1000 matches HyRec table | RecombInterp.query_tau_dot | 1e-10 |
| T-12 | `x_e` at z=8 matches reionization (0.5 × x_e,post) | 0.5 × x_e,post | 1e-6 |
| T-13 | `rho_c(a) * a**3 == Omega_c_0` | constant | 1e-12 |
| T-14 | `rho_Lambda` constant | Ω_Λ,0 | 1e-15 |
| T-15 | `w_Lambda == −1` | −1 | 1e-15 |
| T-16 | `Σ ρ_s (1) == 1.000` | 1.000 | 1e-5 |
| T-17 | `z_eq = Ω_m / (Ω_γ + Ω_ν) − 1` | ≈3418 | 1 |
| T-18 | `friedmann_residual` at z ∈ {0, 1, 100, 1000, 10000} | 0 | 1e-8 |
| T-19 | Out-of-range η raises `ValueError` | — | exact |
| T-20 | Massive-neutrino request raises `NotImplementedError` | — | exact |
| T-21 | Registry iteration order matches canonical (γ, ν, b, c, Λ) | — | exact |
| T-22 | `_a_of_eta(eta_today) == 1.0` | 1.0 | 1e-12 |
| T-23 | `T_nu(z=0) == 1.9454 K` | (4/11)^(1/3) × 2.7255 | 1e-6 |
| T-24 | `T_m(z=150) ≈ T_gamma(z=150)` (Compton coupling still efficient) | T_γ within 1% | 1e-2 |
| T-25 | `Omega_gamma_0 × c² / (8πG × ρ_crit,0) × 4 aSB × T⁴` constructed from CODATA matches SSOT | within 1e-4 | 1e-4 |

Target total: ~40 tests across the 7 test files.

---

## 9. Implementation checklist

Step-by-step for the LB-1 implementer:

- [ ] Review `00_conventions.md` §§5, 6, 7, 8 to fix units and labels
- [ ] Create subpackage layout (§2.1) with empty `__init__.py`
- [ ] Write `constants.py` — mirror `htt.core.ssot.C` with explicit re-exports; add `test_constants.py` (T-25)
- [ ] Write `base.py` — `SpeciesLabel`, `SpeciesSnapshot`, `SpeciesBackground` ABC, `FLRWBackgroundTable`
- [ ] Write `photon.py` with analytic closed forms; tests T-01 to T-05
- [ ] Write `neutrino.py`; tests T-06 to T-08, T-20, T-23
- [ ] Write `baryon.py` consuming `RecombinationInterp`; tests T-09 to T-12, T-24
- [ ] Write `cdm.py`; test T-13
- [ ] Write `lambda.py`; tests T-14 to T-15
- [ ] Write `registry.py` with `from_planck2018` factory; tests T-16, T-17, T-18, T-21
- [ ] Write `build_flrw_background_table` factory; test T-22
- [ ] Run full bass_py regression + LB-1 tests; confirm 0 regressions
- [ ] Commit as `LB-1: species background evolution (γ, ν, b, c, Λ)`

---

## 10. Cite map (code comment ↔ textbook equation)

Each public method in the concrete species classes must have a docstring with citations in this exact format:

```python
def rho_rest(self, eta):
    """Photon rest-frame energy density ρ_γ(η) = Ω_γ,0 / a(η)⁴.

    Derivation: ρ_γ(a) follows entropy-conserving adiabat
    (Kolb §3.4 eq (3.94)) together with the blackbody relation
    ρ_γ = (π²/15) × 2 × T_γ⁴ (Kolb §3.3 eq (3.54)). Combined with
    T_γ × a = const (Kolb eq (3.78)), we get ρ_γ ∝ a⁻⁴.

    Reference: Kolb §3.3–3.4; Ellis §5.1; Baumann §3.2.
    """
```

This is mandatory. Future LLM agents reading the code should be able to find the textbook derivation in seconds without hunting.

**Minimum cite density**: one citation per public method, plus one citation block at the top of each concrete species file explaining the equation of state + continuity choice.

---

## 11. What LB-1 does NOT do

For clarity, LB-1 does **not**:

- Produce any ODE that is actually integrated (LB-5 is the integrator)
- Touch the multipole hierarchy (LB-2)
- Touch the collision tensor (LB-4)
- Handle tilted species backgrounds (deferred — orthogonal-only in LB-1; tilted activation is an LB-1 extension that re-uses `species_tilt.decompose_tilted_species` at a higher level, spec'd as an **LB-1b extension** below)

### LB-1b extension (optional, same session or next)

After LB-1 is green, a lightweight extension adds tilted species to the registry:

```python
class TiltedSpeciesBackgroundRegistry(SpeciesBackgroundRegistry):
    def __init__(self, ..., v_species: dict[SpeciesLabel, np.ndarray]):
        """v_species[label] is a (N, 3) array of v^a(η) for species `label`.
        Orthogonal species have v ≡ 0; tilted species provide a trajectory.
        """
        ...

    def T_ab_total(self, eta_idx: int) -> np.ndarray:
        """(4, 4) total stress-energy in the n^a frame, using
        `species_tilt.decompose_tilted_species` per species and
        summing the decompositions."""
        ...
```

LB-1b is ~150 LoC including tests and uses the existing Y-Block `species_tilt` machinery without new physics.
