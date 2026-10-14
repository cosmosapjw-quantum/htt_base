# Statistical construction and coding traceability

## C2: retained sources and computational objects

The local R1 package fixes conditional Gaussian/remainder inference and preserves
the observation/physical-state distinction. R2
`research/JOINT_COMPRESSION_AND_ERROR.md` constructs a joint latent observation
law and treats legacy quantities as draw-wise derived observables. The historical
report sections 16–23 retain shared nuisance and same-sky dependence, covariance
support, observation-inclusive conservative ranks, registered functionals and
the transfer needed before interpreting CMB morphology as physical kinematics.
The current production rank core is reused rather than redeveloped.

Here an observed vector y0 and B joint null vectors yi belong to one declared
observation-feature space. The null must match the complete observation pipeline,
not merely a Gaussian label on extracted coefficients. Same-sky map variants
occupy columns of each yi. The independent sampling unit is a latent realization.
HTT's model-dependent inference remains separate from these observation features.

## C3: fixed or independently learned scores

For fixed feature center cj and positive scale sj, let zj(y)=(yj-cj)/sj. Alternatively,
an independent training set fixes cj and sj once, before evaluating observed and
calibration rows. The null validity statement is conditional on this training
set. Upper, lower and two-sided extremeness are respectively zj, -zj and |zj|.
The signed zj is always retained. All tails, feature/mask/depth searches and the
transformation method are predeclared. Scale degeneracy is explicit, and singular
joint covariance does not cause a problem because no covariance inverse is used.

This feature does not offer an observed/calibration-trained whitener. Such a
method requires a genuinely permutation-equivariant fit or independent training,
and its conditional null/support interpretation must be carried through.

## C5–C7: rank and dependence-preserving multiplicity

For a fixed high-extreme score T, count k=sum_i 1[T(yi)>=T(y0)]. The returned
rank is the exact Fraction from the current repository core,

`p_rank = (1+k)/(B+1)`.

The pooled score vector must be exchangeable under the declared null, conditional
on independent training where used, and the same deterministic score must be
applied to every row. Counting ties with >= is conservative. For a pooled vector
with no ties, the observed upper rank is uniform on its finite grid under
exchangeability; with ties, it is superuniform. Consequently Pr(p_rank<=alpha)
is at most alpha. The +1 alone does not establish any of these conditions.

For the predeclared family of feature scores Sj, the global score is
`M(y)=max_j Sj(y)`. Each simulated row is maximized as a complete joint vector;
features are never flattened into an IID sample. The global rank compares M(y0)
to Mi=M(yi). For reporting a feature's single-step adjusted rank, compare Sj(y0)
to the same null Mi. The smallest adjusted rank equals the global rank. The
probability of any adjusted rejection is therefore bounded at alpha under the
complete joint null. This is weak familywise control; strong control under
partial alternatives needs additional conditions such as subset pivotality and
is not asserted. Marginal ranks alone do not calibrate a selected minimum.

The finite minimum is 1/(B+1). If alpha is smaller, rejection is unattainable.
B is fixed beforehand; the implementation runs all declared rows and has no
score-driven early stop or retrospective budget change.

## C6–C8: IID tail uncertainty and numerical evidence

Conditional on an observed threshold t and independent training, IID null rows
give k~Binomial(B,q), where q=Pr_null(T(Y)>=t | training). Its estimator is k/B.
The equal-tailed 1-gamma Clopper–Pearson interval has lower endpoint zero for k=0
and otherwise BetaQuantile(gamma/2;k,B-k+1). Its upper endpoint is one for k=B
and otherwise BetaQuantile(1-gamma/2;k+1,B-k). These are **marginal intervals for
q**, not intervals for the realized finite p_rank. They are not simultaneous
across features. IID rows are stronger than mere pooled exchangeability, so this
CLI restricts the declared row law to IID joint vectors; group-orbit or dependent
null pools need a different uncertainty law even when a rank test is justified.

Unit verification enumerates small tied/untied exchangeable pools and the full
binomial mass for B=12 over a fixed q grid, checks max-statistic dependence,
and rejects provenance violations. Exact duplicate feature columns yield
singular covariance but unchanged coherent ranks. Affine unit changes preserve
ranks. Finite input/scale guards avoid silently dropping unsupported coordinates.
The local run uses NumPy/SciPy/Matplotlib only. Its synthetic 1000-repetition
campaign and replay provide bounded runtime and deterministic numerical evidence;
they are not Planck null qualification or a new physical inference.

## C4: dependency and low-cost execution

1. A product provider supplies observed features with fixed support/pipeline.
2. A qualified simulator supplies joint features per latent realization;
   an independent training pool is supplied only if standardization is selected.
3. The declaration fixes B, features, tails, transform, identities and pipeline.
4. The CLI validates contracts, freezes transform, scores every full row,
   calls the existing rank core, and writes uncertainty/report/plots/receipts.
5. The parent performs one bounded independent review and repository integration.

For d features and B null rows, score storage is O(Bd), and reductions O(Bd).
There is no full covariance matrix or inverse. The demo campaign uses one
(B+1)-by-d pool at a time rather than retaining all repetition pools. Actual
timings and whole-process high-water RSS are in the execution receipt, not a
portable speedup claim. Final source/core versions are hashed at execution.

## Primary references checked 2026-10-14

- Phipson and Smyth (2010), *Permutation P-values Should Never Be Zero*,
  DOI 10.2202/1544-6115.1585. Author's corrected preprint:
  https://gksmyth.github.io/pubs/PermPValuesPreprint.pdf . Relevant Monte Carlo
  rank formula and finite tail-estimation distinction are in sections 2 and 4.
- Hemerik and Goeman (2018), *Exact testing with random permutations*,
  DOI 10.1007/s11749-017-0571-1:
  https://link.springer.com/article/10.1007/s11749-017-0571-1 . Group-transformation
  validity is distinct from arbitrary reference-pool exchangeability.
- Clopper and Pearson (1934), DOI 10.1093/biomet/26.4.404. SciPy's official
  `BinomTestResult.proportion_ci` documents the exact method and original paper:
  https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats._result_classes.BinomTestResult.proportion_ci.html .

The existing rank-core header pairs Phipson/Smyth with arXiv:1603.05766, but that
identifier is Hemerik/Goeman. Its uniform-rank wording also needs the no-tie
qualification. These are documentation corrections for the parent integration;
the cached source remains unmodified and the computation is reused unchanged.

## Additional observed-pilot source regime and scope

The current `fit_cmb_smica_noise_modes.py` source supplies
`require_gated_cache(path,json_gate)`, which validates the exact cache SHA256
against a green reproducibility gate. The observed pilot reuses that gate and
`obsstat.r7_cmb_product_response.pixel_fit_geometry(nside=64)` returning directions
and the registered real harmonic design. Generic injection tests independently
check the Cholesky OLS projection against least squares. The exact linearity
identity fit(signal+noise)=fit(signal)+fit(noise) permits freeing the 999-row
signal NPZ member before loading the 300-row noise member. This controls memory
without changing the coefficient sum or dropping power cross terms.

Planck 2018 IV section 3.5 describes 999 CMB-only and 300 independent
noise-plus-systematics simulations and fixed actual-data component-separation
weights enabling separate propagation of CMB and noise. The maintained
`plancklens.sims.planck2018_sims` source's delivered-map simulator adds signal and
noise maps. These facts justify a delivered component-sum experiment; they do
not certify equality of that null law to the actual observed sky including all
foreground/systematic residuals. The pilot's feature family is fixed before its
current score calculation, while its project-level selection is retrospective.
Both limitations are explicit in output admission and interpretation fields.

- Planck Collaboration (2020), *Planck 2018 results. IV. Diffuse component
  separation*, section 3.5:
  https://www.aanda.org/articles/aa/full_html/2020/09/aa33881-18/aa33881-18.html
- Maintained plancklens source, delivered simulation library:
  https://plancklens.readthedocs.io/en/stable/_modules/plancklens/sims/planck2018_sims.html
