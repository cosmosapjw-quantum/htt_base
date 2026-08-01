# PR-272 Pillar-S inference, coverage, and multiplicity

Status: registered synthetic validation artifact, independently reviewable
Claim ceiling: `diagnostic_only`
Observed-data effect: none
Source-theorem effect: none; conditional/program dispositions are retained

The DGPs, seed derivation, calibration/evaluation splits, tolerances,
coverage intervals, failure thresholds, and negative controls are frozen in
`pr272_spec.yaml`. The generated validation registry is rebuilt solely from
that specification. Its nine rows are obligation-validation records, not a
proof count and not a promotion of the source statements.

## VT-S3 — matched-null simultaneous max-Q

For a calibration sample of exchangeable null vectors, define
\[
T_i=\max_j |Q_{ij}|.
\]
With \(n\) calibration draws and
\(k=\lceil(n+1)(1-\alpha)\rceil\), the split-conformal critical value is the
\(k\)-th calibration order statistic. A future exchangeable null vector is
accepted when its maximum does not exceed that value. The report carries a
one-sided Clopper-Pearson lower bound from an independent evaluation split.
The same statistic evaluated under a changed covariance identity is retained
as a failed negative-control cell; its outer label cannot be used to claim
simultaneous control.

## VT-S5 — partially identified Pi

For every preregistered identified-set width, the least-favourable boundary
point is evaluated with the Imbens-Manski confidence interval. Per-grid
Clopper-Pearson confidence is Bonferroni-adjusted across the frozen grid.
Coverage is therefore grid-conditional. A naive no-expansion construction is
preserved in the failure map. An uncertified interior extremum, an unbounded
set, or a bare optimizer point remains a typed refusal; it is never converted
to a probability draw.

## VT-S6 — joint random anchor

For estimator mean \((\widehat N,\widehat A)\) with registered joint
covariance \(\Sigma/n\), a ratio \(r=N/A\) belongs to the pushed-forward
confidence body when
\[
(\widehat N-r\widehat A)^2
\le z^2\operatorname{Var}(\widehat N-r\widehat A).
\]
This is a quadratic inequality in \(r\). A positive leading coefficient and
nonnegative discriminant give a bounded interval; an anchor body intersecting
zero returns `INCONCLUSIVE_UNBOUNDED`. Two marginal variances without the
cross covariance do not instantiate the contract.

## VT-S9 — finite depth/mask path multiplicity

The registered finite path uses a maximum absolute standardized contrast
calibrated from the same centered-null path. Its adjusted familywise error is
reported next to the deliberately unadjusted pointwise mutation. A nonnested
path or a different target at each rung is refused. This is not an exact
continuum-mask statement.

## VT-S10 and VT-S11 — weak identification and composition

Let \(\widetilde R=C^{-1/2}R\). The executable perturbation diagnostic is
\[
\|\Delta\theta\|_2
\le \frac{\|\Delta y\|_2}{s_{\min}(\widetilde R)}
\]
within the declared linear cell. Full rank does not override the frozen
minimum-singular-value or principal-angle floor: a cell below either floor
returns `ABSTAIN_WEAK_IDENTIFICATION`.

For a registered orbit-chart Jacobian \(J\) and supported response \(R\),
rank of \(RJ\) is checked on one declared principal-stratum linear cell.
Losing a column in either factor yields `ABSTAIN_NON_IDENTIFIED`. The check
does not establish global orbit separation or a family label.

## VT-S12 and VT-S13 — counterpairs and open set

The matched-counterpair benchmark fixes scalar and anchor differences at
exactly zero, then evaluates the held-out power of preregistered morphology
features. Any scalar or anchor drift invalidates the pair. Power is a property
of the frozen synthetic DGP only.

The open-set threshold is calibrated on known-library draws before held-out
known and unknown draws are inspected. Known selective coverage, unknown
abstention, and sensitivity to removing one finite-library member are all
reported. Unknown cases abstain; nearest labels are not emitted outside the
calibrated support.

## VT-S14 — depth-conditioned local/global adapter

HTT evaluates two declared Gaussian GLS response candidates with a full
depth covariance and mask-path identity. The output is a synthetic,
model-conditional diagnostic comparison. MIO receives only Euclidean
residual/coherence summaries. Its object has no likelihood, posterior, Bayes
factor, or evidence fields. The VT-S14 source remains a program obligation
pending repository-admitted data.

## SBC and conditional auxiliary requirements

SBC is run only because the registered HTT computation cell makes a posterior
calibration claim. The exact-conjugate cell and two frozen variance
misspecifications remain together. PPC and LOOCV are not required because
PR-272 makes neither a predictive-adequacy nor an out-of-sample model-ranking
claim.

## Forbidden interpretations

These results do not consume observed data, validate a native solver or
morphology atlas, support geometry detection, or identify a Bianchi family.
MIO does not own inference. Failed registered cells cannot be removed or
hidden by changing a seed, tolerance, grid, or threshold.
