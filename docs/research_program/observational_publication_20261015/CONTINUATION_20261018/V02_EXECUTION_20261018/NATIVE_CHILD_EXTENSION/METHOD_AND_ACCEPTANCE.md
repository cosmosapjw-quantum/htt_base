# Source-defined finite V02 native-child processing extension

Owner obsstat, C0, DIAGNOSTIC_ONLY, non-claim-bearing. Requested executor
gpt-6.1-sol/high; observed model and effort UNKNOWN. Existing checkout only;
no child commit/push or canonical DAG/status edit. Parent arranges independent
read-only scientific review. The existing centre candidate and all its seven
finite experiments remain immutable and are not rerun.

## Frozen source and operator

The source is the original `SMICA_FULL` retained T fit from NPZ SHA256
`900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459`.
The same saved `s_lm=a_fit_lm/b_INT(l)` on ell2..5 is used, in microK_CMB.
This defines a finite signed source perturbation; it does not reconstruct
the intrinsic physical sky or fill unknown physical sectors with zero.
The scalar Doppler weight is one, directions outward/sourceward,
beta=v/c, metric (-,+,+,+). The exact pullback and quadratures are read-only
imports from the preserved centre candidate's `v02_response.py`.

`A_native = retain_ell2..5 OLS_ell0..5(centre RING64 design)
            AFTER original fixed-valid masked native-child mean`.

The original source producer and reducer are inspected at Git
`c2889730d2b5e5b778951f15e8f09afd55bed4e3`:
`scripts/run_htt_planck_multisplit_spin_20261015.py::source_iqu` and
`htt/obsstat/planck_split_joint_law.py::nested_coarse_masked_mean`.
Their `TMASK & isfinite(original I_STOKES) & original I_STOKES>-1e20`
validity defines the fixed fine-pixel averaging window. Actual native I
validity is inspected once; only packed booleans/counts are saved, no raw
source I values or FITS copy. This avoids L03's different simulated-value
validity rule. The implementation uses a local independent streamed reducer.

Native common/HM/OE TMASK are ANDed, then 1024 contiguous NESTED2048 children
per NESTED64 parent give mask coverage. Selection is original cache
confidence>.5 AND TMASK coverage>=.995, independently of source validity.
Selected actual value coverage must also be>=.995; selected parents are
never silently dropped. Exact RING64 support count 26846 and mask SHA256
`98c90cbd186aceed02f6692ef83685b44d0f7f22569f218ea2936dcfafcedfbf`
must match the saved centre candidate.

The incremental response is

`d_native(beta) = A_native B_INT [P16 U_beta s - s]`;
the perturbed delivered-fit vector is `a_fit + d_native(beta)`.

The distinct unboosted mismatch `A_native B_INT s - a_fit` is reported,
not set to zero and not used to redefine the source. INT_BEAM is checked
against the actual delivered SMICA table, then applied exactly once after
the boost; healpy adds no Gaussian smoothing or pixel window.

## Six projected fields and finite diagnostics

Exactly six native full maps are synthesized, one at a time:

1. Unboosted B_INT s.
2. Three B_INT-applied analytic first-order generator columns (ell<=6),
   read from the unchanged historical analytic generator.
3. Two B_INT-applied finite increments at
   beta=.00123*(1,2,3)/sqrt(14) and half that vector.

`hp.alm2map` receives real coefficients converted to complex alm by
`alm_lm=(cos_lm-i sin_lm)/sqrt(2)` for m>0, preserving the real
Condon-Shortley convention including sine signs. Its RING native output
is streamed through ring2nest-indexed sums/counts. There is no native
design matrix. A deterministic selection of native children is checked
against direct real harmonic synthesis, and explicit child sums include
a partially masked selected parent.

The three native analytic columns define J. Joint OLS and independent
pixel monopole/dipole FWL quotient must agree within 1e-8 microK/beta.
Constant-pixel nuisance and small-resolution constant-through-reducer
tests are required. Native zero-increment propagation must be<=1e-9
microK. Synthesis/explicit reducer sample checks use<=1e-9 microK.
No tolerance is relaxed. Raw first failures, if any, remain in the run log.

Both finite `d_native-J beta` vectors/norms, native-vs-centre processing
differences and singular values are reported. Centre comparisons apply
the preserved centre transfer matrix to these same six fields; the old
seven experiments are not rerun. Half-amplitude centre output is a
matched linear-processing comparison, not a repeated old experiment.

The same 32x64 and 48x96 quadrature projections and ell12/16 comparison
are reused at coefficient level. For each finite coefficient difference,
the propagation envelope

`||P_retained||2 sqrt(26846) (L+1)/sqrt(4 pi) ||delta_c_after_beam||2`, L=16,

follows from the spherical-harmonic addition theorem, convex valid-child
averages, and the selected-pixel OLS norm. It bounds only the declared
finite coefficient comparison. It is not an infinite Lorentz-tail bound,
sampling covariance, physical noise law or physical uncertainty.

## Review and claim ceiling

Original V02 acceptance remains “Matched mask/beam/input and mode leakage”.
Fresh review may decide
`PASS_SCOPED_V02_SOURCE_DEFINED_FINITE_NATIVE_PROCESSING` when the actual
operator, source, beam, support, J, both finite points and controls pass.
The author records execution and offers artifacts for review; no self-admission.
Unknown physical upstream component-separation/frequency/calibration mapping
remains UNKNOWN and is outside this defined finite operation. No local/global
physical rank, physical velocity, covariance, posterior, p-value, global-history
transfer or Bianchi-family claim follows. Paper publication readiness is unchanged.

## Local and external API evidence

Source identities, historical source hashes, actual beam values and exact mask
identity are in generated `results/NATIVE_RESPONSE.json`. Installed healpy is
tested by direct harmonic samples, including nonzero sine coefficients.
The [official healpy alm2map reference](https://healpy.readthedocs.io/en/latest/generated/healpy.sphtfunc.alm2map.html)
was checked 2026-10-18: complex alm input, RING map output, optional pixwin and
Gaussian smoothing. Runtime version is recorded separately from current docs.

## Reproduction

Use the existing `.venv/bin/python` with OPENBLAS_NUM_THREADS=2,
OMP_NUM_THREADS=2, MKL_NUM_THREADS=2 and `-B` from the repo root.
Run `-m pytest -q` on this directory's `test_native_processing.py`.
The scientific command is `native_processing.py`; it is create-only.
Reuse the completed output rather than repeating its six full native fields.
`finalize_native.py` generates the PNG/PDF, report and receipt from saved
results only. Parent performs review and publication.
