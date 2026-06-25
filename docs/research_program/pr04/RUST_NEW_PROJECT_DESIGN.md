# LR-06L — New Rust solver: design pack (separate long-term project)

Status: design started (lifts `AWAITING_RUST_DESIGN_PACK`). This is a **separate
repository**; it does not block PAPER-A/B and inherits **no** science validation
from the existing `bass_rs` crate. Operationalizes
`docs/research_program/pr04/RUST_HANDOFF_BOUNDARY.md`.

## Principle

Start from **language-neutral golden contracts** and an **exact FLRW comparator**.
A capability is "validated" only when it passes a golden contract that was fixed
independently of any old solver output.

## Golden contracts (gate order)

1. **Exact flat-FLRW background + perturbation comparator.** Reproduce the
   closed-form dust oracle `a(t)=(1+3H0 t/2)^(2/3)`, `H=H0/(1+3H0 t/2)`,
   `Hdot=-(3/2)H^2`, `3H^2=κμ` (proven in `pr04_paper_theorem_proofs.json`
   `B-dust`) to machine precision. **First science gate.**
2. **Lorentz/frame + STF round-trip.** Boost composition is exactly Lorentz and
   non-additive (`A-wigner`); STF pack/unpack is lossless (`stf_canonical`).
3. **Bianchi-I constraint transport + shear memory.** Gauss residual stays at
   round-off under evolution; `σ̇=STF(−3Hσ+κΠ)`, `d(σ̇)/dΠ=κ` (`B-shear`).
4. **Collision/visibility conservation + positivity.** Number/energy
   conservation and PSD second-moment positivity (`B-psd` moment cone).
5. **Transfer convergence with an independent comparator.** Grid/`ℓ_max`
   convergence checked against a second, independent transfer implementation.
6. **Truthful family × mode × orientation support matrix.** Every (family, mode,
   orientation) cell is either implemented-and-gated or explicitly unsupported;
   never silently zero. Off-support raises, fail-closed.

## Salvage vs quarantine (from the existing `src/` crate)

- **Salvage** (independently testable utilities, re-gated, no science values):
  LU/sparse kernels, PSTF/STF indexing, tensor containers, source/config
  schemas, selected quadrature utilities.
- **Quarantine** (never imported into validation): old FLRW/Bianchi spectra,
  family evidence, atlas rankings, truth-engine values, hard-coded HTT/MIO
  bridges. The forbidden-dependency scan
  (`research_gates/pr04/tools/verify_forbidden_dependencies.py`) is the guard.

## Python/Rust parity harness

Each golden contract ships a language-neutral fixture (JSON: inputs, tolerances,
expected invariants). The Python overlay (`bass.background.bi_continuation`,
`bass.observer.congruence_ssot`, `htt.common.stf_canonical`) is the reference
oracle for contracts 1–4; contract 5 needs an external transfer comparator. A
parity report records max abs/rel deviation per contract; the FLRW oracle gate
fails the build if contract 1 deviation exceeds machine-precision tolerance.

## Claim boundary

No native family response is claimed until every gate passes. Until then the Rust
project is a development artifact, not a result surface; it does not feed HTT
evidence, MIO certificates, or any family/geometry statement.

## First milestones

1. Repo skeleton + contract-fixture format + CI running contract 1 (FLRW oracle).
2. STF/Lorentz round-trip (contract 2) + Bianchi-I transport (contract 3) against
   the Python oracle.
3. Independent transfer comparator scoping (contract 5) — gated behind LR-06G's
   validated transfer owner.
