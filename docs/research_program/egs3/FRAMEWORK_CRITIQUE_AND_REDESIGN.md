# Five-variable framework: critique, upgrade, revisionary redesign

The diagnostic layer is `x_C` (signed comparator), `Q` (policy-normalized score),
`Π` (exceedance), `F` (filling), `G_F` (depth gap), in
`htt/htt/htt/core/departure_posteriors.py`.

## Critique (real weaknesses)

1. **`x_C` sign cancellation.** `x_C = Σ²−W²+Ω_tilt+Ω_k` contracts four distinct
   invariants into one signed scalar; `Σ²−W²` can cancel, so a large shear *and*
   a large vorticity read as near-FLRW. Sector identity is destroyed.
2. **`F`/`Q` ill-posed + redundant.** `F=x_C/x_max` is a "filling fraction" but
   `x_C<0` is admissible (`Q_status=defect_negative`), so the fraction is
   undefined there; `Q` and `F` are both `x/x_max` (Q only adds status flags).
3. **`x_max` convention dependence.** The ceiling mixes shear+tilt+curvature; `F`
   inherits the convention.
4. **`Π`/`G_F` already disciplined** (S4 domination; NT-B3 additive contrast) but
   `Π` was only "not a probability" — not yet a *calibrated* certificate.

## Upgrade — graded comparator (landed, rev-r123)

Promote the primary object to `g = (Σ², W², Ω_tilt, Ω_k) ∈ R⁴`, with
`x_C = ⟨c,g⟩`, `c=(+1,−1,+1,+1)` a *derived* linear summary. Implemented as
`DeparturePosterior.compute_graded_comparator()` (additive; asserts
`x = Σ²−W²+Ω_tilt+Ω_k` bit-identically, so nothing downstream changes) and the
standalone `htt/obsstat/egs3_graded_comparator.py`. Per-sector filling uses the
nonnegative sectors only, removing the `F<0` pathology. Sector identity is
preserved under cancellation (contract `test_graded_comparator_upgrade.py`).
A1 then proves the data-identifiable subspace of `g` is rank 2, so `x_C`'s
sign-cancellation is a *projection artifact*.

## Revisionary redesign — PSD-cone comparator (realized + gated, rev-r125)

Replace the scalar layer with a **PSD-matrix comparator** `M ⪰ 0` whose
invariants are the sectors (shear+tilt second moment; PAPER-B B-psd moment cone
is the admissible set). The labelled-eigenbasis comparator is `M = diag(g)` with
signature `C = diag(+1,−1,+1,+1)`. Then:
- `x_C` is a functional of `M`: `x_C = tr(C M)`, **bit-identical** to `⟨c,g⟩`
  because `M` is diagonal in the sector eigenbasis (the gating regression);
- the admissible set is the **PSD cone** — fail-closed on any negative labelled
  invariant, and **convex** (closed under nonnegative scaling + convex
  combination), the property the ad-hoc `x_max` ceiling lacked;
- identifiability = which **eigen-directions** of `M` the channels reach: the
  measurement map `M ↦ P_R M P_R` keeps `{Σ², Ω_tilt}` (rank 2) and annihilates
  the blind sector (A1);
- the NT2-B3 blind sector `{W², Ω_k}` = a *structural null direction* (kernel) of
  the measurement map — its invariants are killed exactly (null residual 0);
- the NT2-B1 two-sided bracket = membership in a convex **cone-shell**
  `{M⪰0 : s_lo < λ_Σ(M) < s_hi}` with `s_lo>0`, which excludes the shear-free
  FLRW vertex (`λ_Σ=0`).

This unifies rank, bracket, blind sector, and admissibility under one object and
is the headline conceptual novelty.

**Realized this revision (rev-r125), representation only**:
- module `htt/obsstat/egs3_psd_cone.py`;
- gates `research_gates/egs3/tests/test_egs3_axis_psd.py` (P1 trace identity,
  P2 convex cone + fail-closed, P3 reachable eigendirections / structural null,
  P4 convex cone-shell bracket);
- contract `tests/contracts/test_psd_cone_redesign.py` (bit-identical `x_C`);
- Wolfram core `wolfram/egs3_psd_cone.wls` → `docs/generated/egs3_psd_cone_proof.json`
  (trace identity, convex cone, convex shell, vertex exclusion — all PASS);
- experiment `scripts/run_egs3_experiments.py:axis_psd`.

It **ships behind** the additive graded upgrade and does **not** front the
production diagnostic: the `x_C`-bit-identical regression is the standing guard
and the redesign stays gated until an independent reviewer signs off
(`tickets/psd_cone_redesign.yaml`, `state: implemented_behind_review`).
Off-diagonal (cross-sector) PSD structure is a strict superset reserved for the
native solver and is **not** asserted here.
