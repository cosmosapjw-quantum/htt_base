# Report A R2E — frozen-source blind review

Date: `2026-09-03`  
Repository: `cosmosapjw-quantum/htt_base`  
Observational gate: `DATA_DEFERRED_BY_OWNER`

## Verdict

```text
PASS_R2E_THEORY_AND_METHODS_CORE
/
MANUSCRIPT_STATUS_REGENERATION_REQUIRED
/
EXACT_HEAD_EXECUTION_PRESTART_BLOCKED
/
NO_PUBLICATION_OR_MERGE_AUTHORITY
```

A fresh review of the R2 working manuscript, the 29-claim ledger, the R2C/R2D
audits, and the current PR #450/#451 source found no P0 mathematical,
statistical, or scope defect. The theory report is scientifically coherent at
its declared evidence grades. It is not yet a frozen release candidate because
the manuscript's implementation-status paragraphs lag the repaired source
branches and no exact-head runner has executed.

## 1. Surviving core

The following claims survive the blind review at their stated scope.

1. The stored-real harmonic carrier and the `Q/O` PSTF norm identities are
   exact.
2. On the nonzero cyclic domain, the overcomplete Q/O Krylov packet separates
   proper-rotation orbits for packets in the forward image. It is not a global
   invariant-ring or all-strata theorem.
3. MES quantities are one-way, premise-conditioned scalar norm functionals.
   They do not tensorize the observation or estimate physical shear/vorticity.
4. An observation-inclusive finite rank is super-uniform under joint
   exchangeability or a valid randomization symmetry when the complete
   adaptive analysis is row-equivariant.
5. The WU-010 local-observer STF response and condition bound retain their
   frozen implementation-verified status.
6. The WU-011 nuisance-quotient and nested-image identities are exact. The last
   finite-HEALPix scientific terminal remains rank unresolved.
7. The continuum `L=12` axial rank is exact-author-artifact evidence; the five
   other registered directions remain independent high-precision numerical
   evidence.
8. The matrix-valued numerical-error envelope is a valid conditional theorem
   for a frozen complete error-family class. Actual family completeness remains
   unresolved.

## 2. Current source repairs

### PR #450

The source seed schema now has one exact key set per row. The malformed
`source_kkind` entry was replaced by `source_kind`, and an explicit row-schema
test was added. The registered surface is unchanged:

```text
37 registered = 36 INCLUDED + 1 DEFERRED
```

Source-equivalent verification is `14 passed`; exact-head execution remains
`PRESTART_NO_EXECUTION`.

### PR #451

The packet decoder now uses a fixed Frobenius-orthonormal seven-dimensional
Cartesian STF3 basis and reconstructs the octupole from ten trilinear equations
using a row-scaled full-rank least-squares solve. It then requires STF closure,
`O:Q=B e0`, and full packet replay.

Source-equivalent verification:

```text
28 focused tests passed
10,000 forward-generated stress pairs
7 typed OrbitChartUnavailable refusals
0 silent replay failures
maximum packet residual 5.2119071003442485e-09
```

Independent exact SymPy arithmetic gives a `7 x 7` identity Gram matrix, zero
trace and symmetry residuals, and basis rank seven. A fresh Wolfram replay was
attempted but returned an upstream 502 and is not counted as a pass.

The patch improves numerical coherence without weakening the public condition
limit or fitting a threshold to one witness. It remains source-level until an
exact-head supported-runtime job executes.

## 3. MES equation-level provenance

R2D closes the primary-source coefficient and premise audit.

- Eqs. (59) and (60) of `astro-ph/9501016` give the geodesic shear and
  vorticity coefficient triples after assumptions C1/C2.
- Eqs. (15), (17)--(19) of `astro-ph/9904346` give the harmonic-to-PSTF norm
  conversion.
- Eq. (12) of the same paper makes `epsilon_1=0` an adopted peculiar-motion
  attribution while acknowledging a possible non-Doppler residual.

Fresh exact algebra reproduces

\[
\epsilon_2^2=\frac{75C_2}{8\pi T_0^2},\qquad
\epsilon_3^2=\frac{245C_3}{8\pi T_0^2},
\]

and

\[
\left.U_\omega\right|_{\epsilon_1=0}
=\frac{C_2}{4\pi T_0^2}.
\]

## 4. Open publication blockers

### P1

1. PR #449, PR #450, and PR #451 exact-head GitHub jobs continue to terminate
   before runner assignment with no executed steps.
2. The R2 manuscript still reports the older PR #450/#451 local counts and does
   not yet describe the conditioned STF3 decoder or bind the R2D equation-level
   MES provenance in the body.

### P2

1. The five non-axial continuum ranks are not interval-certified.
2. Novelty of the repository-specific Q/O Krylov packet is unresolved; current
   literature search found adjacent invariant/separating-set methods but no
   direct theorem match.
3. The 10,000-pair decoder stress run is strong numerical evidence, not a proof
   that every forward packet below the nominal condition limit will decode.

## 5. Required next manuscript regeneration

Regenerate the working manuscript from the current frozen inputs and make only
bounded status/provenance edits:

1. change PR #450 from `13 passed` to `14 passed` and record the schema repair;
2. change PR #451 from a minimal 26-test image guard to the 28-test conditioned
   STF3 decoder plus the 10,000-pair stress boundary;
3. insert the R2D equation/page-level MES provenance paragraph;
4. keep every scientific conclusion and observational firewall unchanged;
5. rerun the five manuscript contract tests and a fresh claim/citation scan.

## 6. Claim boundary

No current scalar rank, corrected Planck tensor rank, empirical observer
velocity, boost subtraction, global matter-frame tilt, physical shear or
vorticity measurement, foreground cause, Bianchi-family attribution,
finite-HEALPix no-go theorem, BASS/native-solver result, publication approval,
or merge is introduced.
