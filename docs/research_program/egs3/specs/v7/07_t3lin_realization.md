# v7 spec — T3-lin linearized realization (M2 / P31 upgrade)

owner: OBSSTAT/BASS
implementation_scope: htt/obsstat + wolfram
claim_tier: diagnostic_only (symbolic/linearized realization; not a full nonlinear GR theorem)

## Problem (referee M2)

P31 "identified-set sharpness" was proved only at the convex-component-box level. The
referee showed the physical-realizability step is a gap: the box extremes must be shown
to be realized by a configuration satisfying BOTH the Gauss (Hamiltonian) and the
momentum constraints, not merely to be feasible points of the convex program. Full
nonlinear realization (King–Ellis tilted Bianchi V invariants) is deferred; the v7
deliverable is the **linearized** realization theorem T3-lin covering the x_C ≪ 1 regime
where the comparator is actually used.

## Claim to certify (T3-lin)

For any target 4-tuple (Σ², W², Ω_tilt, Ω_k) with x_C = Σ² − W² + Ω_tilt + Ω_k ≤ x_max ≪ 1,
respecting the signed-box/cone domain, there exists a linearized 1+3 initial-data
configuration — a superposition of (i) a Bianchi-I diagonal transverse-traceless shear
mode (momentum constraint auto-satisfied, q=0), (ii) open/closed anisotropic-curvature
modes for ±Ω_k, (iii) an antipodal tilt pair (net energy flux q=0, additive Ω_tilt per
T9′ corollary), (iv) a linear vector/rotation mode for W² — whose first-order Gauss and
momentum constraint residuals both vanish and whose normalized invariants reproduce the
target to O(‖g‖²), with the matter sector satisfying the weak energy condition for small
amplitudes.

## Deliverables (all NEW files — do not edit existing modules)

1. `htt/obsstat/egs3_linearized_realization.py`:
   - `realize_endpoint(target: dict) -> dict` — build the mode amplitudes for a target
     (Σ², W², Ω_tilt, Ω_k); return amplitudes + the linear-order Gauss residual and
     momentum residual (both must be ~0 to machine precision) + WEC branch label.
   - `linearized_realization_seal() -> dict` — aggregate over the two identified-interval
     endpoints of the registered example ([11/100,17/100] open branch) plus a random
     sweep of small targets; status FAIL if any residual exceeds 1e-10; record
     `sympy_version`/`numpy_version`. Mirror the `parent_identity_seal()` shape
     (`seal`, `status`, `claim_boundary`).
   - Antipodal-pair flux cancellation must be shown symbolically (SymPy): q(β)+q(−β)=0
     while Ω_tilt(β)+Ω_tilt(−β)=2(1+w)Ω_m sinh²β.
2. `wolfram/v7_t3lin_covariant_residual.wls`: xAct covariant residual check that the
   superposed shear+vorticity+curvature+tilt first-jet satisfies the linearized
   momentum constraint D_b σ^{ab} − (2/3)D^a Θ + curl ω-term = κ q^a at first order,
   with q supplied by the antipodal pair. MUST: (a) guard xAct availability
   (`If[Not[$xActAvailable], emit a "xact_unavailable" advisory boolean = True so the
   base-engine checks still gate]`), (b) avoid the reserved symbol name `Gamma`
   (Christoffel collision — use `Chr`), (c) wrap any `Simplify`/`Resolve` in
   `TimeConstrained[..., 60, $Failed]`, (d) return a flat `checks` association of booleans.
3. `research_gates/egs3/tests/test_egs3_axis_g_realization.py`: unittest gates asserting
   `realize_endpoint` residuals < 1e-10 at both endpoints + a random small-target sweep +
   the antipodal cancellation; final class must be a CoVe adversarial guard that asserts
   the module makes NO x_C mutation (import egs3_graded_comparator, recompute a fixed x_C,
   `np.array_equal` against the pre-recorded value) and NO observational/family/native
   claim string appears in the module docstring.

## Acceptance gates

- `realize_endpoint` Gauss + momentum residuals < 1e-10 at both registered endpoints.
- antipodal flux cancellation exact (SymPy simplify == 0); Ω_tilt additivity exact.
- `linearized_realization_seal()` status PASS; deterministic (no timestamps/RNG without
  fixed seed; record library versions).
- xAct .wls returns all-true `checks` (or a clean xact_unavailable advisory that still
  lets the base-engine momentum-residual check pass).
- CoVe guard: x_C anchor bit-identical; no forbidden claim strings.

## Boundaries / house rules

- Diagnostic-only; this is a LINEARIZED realization, explicitly NOT a full nonlinear GR
  sharpness theorem (that stays a deferred candidate). The report text demotes P31 to
  "registered convex-component-box sharpness" and registers T3-lin as the physical upgrade
  over the x_C ≪ 1 regime.
- No edits to existing `htt/obsstat/*.py`, no edits to the shared seal runners/gate files,
  no `git` commands. New files only.
- No import of external review-bundle code (reimplement from the spec / `06_strengthened_theorems_ko.md` §7).
