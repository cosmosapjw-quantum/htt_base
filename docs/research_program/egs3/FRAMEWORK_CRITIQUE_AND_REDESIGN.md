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

## Revisionary redesign — PSD-cone comparator (next stage, ticket)

Replace the scalar layer with a **PSD-matrix comparator** `M ⪰ 0` whose
invariants are the sectors (shear+tilt second moment; PAPER-B B-psd moment cone
is the admissible set). Then:
- `x_C`, `F` are functionals of `M` (trace-class contractions);
- identifiability = which eigen-directions of `M` the channels reach (A1 becomes
  a statement about `M`'s reachable spectrum);
- the NT2-B3 blind sector = a *structural null direction* of `M`;
- the NT2-B1 two-sided bracket = *cone membership* of `M`;
- `Π` exceedance = a measure on the cone with the A3 e-value calibration.
This unifies rank, bracket, blind sector, and exceedance under one object and is
the headline conceptual novelty; it is gated behind the additive upgrade so the
existing `x_C` regression and all downstream artifacts are untouched until the
redesign is independently reviewed. See `tickets/psd_cone_redesign.yaml`.
