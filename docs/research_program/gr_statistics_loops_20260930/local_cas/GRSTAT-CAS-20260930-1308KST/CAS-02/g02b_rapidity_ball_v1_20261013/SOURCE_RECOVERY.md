# G02-B source recovery

Author run: headless single Lean author (requested claude-opus-5-5 / high; observed runtime UNKNOWN).
Repository HEAD at invocation: `b976a27ca0c4fc038788e6ab8449e2d7e98b1b76`
(branch `proof/cas15-ls-matrix-synthesis-20261008`). All paths below are repository-relative.
`$C` = `docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-02`.

## Card
- `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip` (sha256 `2d0b6da9308ab43e070a620f49241640b5aa7c80c277e1f0857edea22bc4af6f`)
  member `HTT_ALL_OBLIGATIONS_20261011/tasks/G02-B.json` (sha256 of member bytes
  `b89a6a10133393b4dee956c8e233100a0b65d7d10596b21d0052b531aa757a9d`).
  Lean steps (translated): (1) package the actual Du Gram eigen-actions as a
  maximum-eigenvalue / operator-norm theorem including d=0; (2) for R>=0 and
  ||d||<=sinh R prove max <= 1+tanh(R)^2 and the original rapidity monotonicity;
  (3) construct the closed Euclidean ball projection, prove nonexpansive and
  fixed-point properties; (4) from a derivative bound on a convex segment derive a
  mean-value Lipschitz bound and connect it to the C04 positive-anchor stability
  theorem. Acceptance: R=0, d=0 not excluded; regularity and projection constants
  needed by the final finite inverse map are explicit assumptions/conclusions.

## Contract and theory
- `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-02.json`
  (sha256 `71283a74d0fc4a0f632e13b7361c407bdddaf9fa4486044dd30a64cb68b057a3`):
  C03 component text ("For u(d)=(sqrt(1+|d|^2),d) ... For |d|<=sinh R, the largest is <=1+tanh(R)^2");
  C04 text ("projection nonexpansiveness and regularity remain separately tracked");
  `full_theorem_boundary.additional_analytic_obligations` = "Triangle/Cauchy and operator norms",
  "Nonexpansive projection, derivative/mean-value and rapidity monotonicity";
  `uncontracted_research_targets` include "Ball-clipped dipole d*: u*=(sqrt(1+|d*|^2),d*); ||u*-u||<=sqrt(1+tanh(R)^2)eta_d"
  and "Independent monopole mismatch<=eta0+tanh(R)eta_d"; `frame_signature_units_conventions.positive_norms`
  = "Declared Euclidean observer/rest component norms; do not use indefinite norm in inequalities";
  singular loci STAB-R0, STAB-AMPLITUDE, STAB-OFFSHELL.
- `docs/research_program/gr_statistics_loops_20260930/gr/OPTICAL_THEOREMS.md`
  (sha256 `5ae2b6a65a5704247bed3d7dc5f01924318063ee5443cfa95c30c452b0ea8c21`;
  contract lists it as research provenance):
  - line 104: rapidity chi>=0, zeta_0=cosh chi, |zeta|=sinh chi; at zero dipole u=o, no direction selected.
  - lines 158-159: all Section-5 norms are positive Euclidean component norms in a fixed observer tetrad, not Lorentz norms.
  - lines 165-172 (eqs 18-19): eps_Z, eps_H, M=sqrt(cosh 2R), L=min(||S||op, ||S~||op).
  - lines 175-180 (Theorem 4, eq 20) and line 180: L may be replaced by either norm individually.
  - lines 212-222 (optional off-shell extension, eqs 22-23): project the supplied dipole onto the closed
    Euclidean ball of radius sinh R to get d_*; u_*=(sqrt(1+|d_*|^2),d_*); convex projection gives
    |d_*-zeta|<=eta_d; gradient of d->sqrt(1+|d|^2) has norm <= tanh R on the ball; hence
    |u_*-u|_E <= sqrt(1+tanh^2 R) eta_d (22); eq (20) applies with L replaced by ||S_*||op;
    monopole check |zeta0hat - sqrt(1+|d_*|^2)| <= eta0 + tanh R eta_d (23); line 212: applying the map
    "does not establish that the supplied sky is in the exact image" (STAB-OFFSHELL).
- `docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md`
  (sha256 `4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897`): no additional
  projection/rapidity definition (grep for rapidity/sinh/ball/projection: only line 9, index-variance of
  spatial projectors, unrelated).
- Implementation `htt/`: grep for ball projection / dipole clipping found only
  `htt/htt/htt/nulls/scanning_law.py` (scanning-law nulls, unrelated). No implementation owner of the
  clipped-dipole map exists; the definition is taken from OPTICAL_THEOREMS.md lines 214-220.

## Reused Lean sources (imported unchanged)
- C01-C03: `$C/c01_c03_input_aligned_v1_20261005/lean/Cas02.lean`
  sha256 `283f64377e49585c697c3cb51f04cacece79015b36fa3c8d4a8e2d640678b520`
  (git blob 9922d424..., added by d2ffe35e; independent review
  `$C/c01_c03_independent_review_v1_20261011/RETURN.json` sha256
  `1d8d6a9e0d38892c5f5594e8e777fe44f35e75c6e12a6ab98fc7f272ccfe3f6e`, PASS_SCOPED; G02-A closeout
  `$C/g02a_source_identity_closeout_v1_20261013/RETURN.json` sha256
  `cd624040f20d0c62b297c4af4c83cb18734ea86ec3f894bb9f1aa16f51b41139`).
  Used declarations (file:line): `chart` 116, `chartJac` 118, `C03_hasFDerivAt` 122 (actual Frechet
  derivative), `chartJac_apply` 131, `chartGram` 142, `C03_gram` 145, `gramVec` 162,
  `C03_gram_action` 165, `C03_longitudinal` 186, `C03_eigenvalue_only` 203, `ratio_mono` 249,
  `C03_rapidity_bound` 256.
- C04: `$C/c04_inverse_bound_v1_20261008/lean_clean/InverseBound.lean`
  sha256 `bfdf0a778edd6f7af13d8b8cdb43afef1524b9dca1fe422925a294d99f085c6b`
  (PR #498 payload, head c0365da5, 83/83 blobs byte-identical per G02-A closeout; C04 RETURN.json sha256
  `118ee1019e5bc140c5866815be5e2b7715cb4a20ceb6a746c4ae00d1639ed87f`, CAS_4AXIS_PASS_REVIEW_RETURNED,
  lifecycle BLOCKED_GLOBAL_REGISTRATION_UNAVAILABLE). Used declarations: `Vec3`/`Vec4`/`Mat4` 7-9,
  `future` 18, `rapidityCap` 29, `future_norm_le_cap` 35, `spectral` 53, `spectral_nonneg`,
  `inverse` 187, `CAS_02_C04` 213.
- Not imported: `$C/c03_gram_eigenvalue_bound_v1_20261011/GramEigenBound.lean`
  (sha256 `5e1518e1...d3258cb`) re-declares C03 excerpts in namespace `Cas02` and would clash with the
  imported `Cas02` module; its single theorem is re-derived here from the imported C03 lemmas.

## Missing items
None blocking. The physical admissibility of the clipped output is NOT recoverable as a theorem and is
not claimed: the source itself (OPTICAL_THEOREMS.md:212, 222; contract STAB-OFFSHELL) states the
projection does not establish raw compatibility.
