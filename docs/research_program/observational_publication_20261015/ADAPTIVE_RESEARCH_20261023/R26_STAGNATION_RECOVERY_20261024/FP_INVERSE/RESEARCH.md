# R26-FP-LATENT-MEMBERSHIP-8-ROUNDING-INVERSE

Owner: HTT source-method research. Status: terminal conditional counterexample;
source genealogy HOLD. Claim tier: C0 diagnostic/method result. Transfer source:
none. Requested runtime: gpt-6-astra/xhigh; observed runtime: UNKNOWN.
Date: 2026-10-24 (Asia/Seoul). This is a new issue grounded in the actual reviewed
forward-pooling witnesses, not a new allocation or a renamed exhausted repair.

## Decision

The proposed **deletion-only, released-count-constrained inverse pooling model is
empty for the eight mismatch groups**, without any subset enumeration or fitting.
Group 1490017 has one observed table2 FP galaxy and a released table3 count of two.
No subset of that one-element set has cardinality two. This is a conditional
counterexample to that repair model; it is not a diagnosis of the true producer
genealogy and is not a scientific-integrity verdict against CF4.

No new numerical worker contract is issued: its terminal discriminator has
already been resolved by a source-bound cardinality witness. A complete all-mask
enumeration would also be infeasible to promise within the remaining original
budget. H02 remains HOLD, and the controller should immediately continue its
independent ready work (the concurrently authorized full7 branch) while keeping
the exact source request below available.

## Evidence and correction to the historical narrative

The frozen input is the actual `/mnt/extdrive/workdir/htt_open_data/`
`r26_cf4_fp_pooling_closure/{RESULT.json,WITNESSES.json,SOURCE_BINDING_RECEIPT.json}`,
reviewed as `ACCEPT_FINITE_OPERATOR_RESULT` by
`r26_cf4_fp_closure_independent_result_review/RETURN.json`.
`SOURCE_FACTS.json` records the current hashes of those artifacts, the relevant
ReadMe identity, all 54 exception metadata records and the raw minimal witness.
The two minimal raw lines were independently read by their recorded byte offsets
and matched exactly. No whole-catalogue scan or old computation was rerun.

An additive correction is required in downstream prose, leaving historical
receipts unchanged: **all 46 `MISSING_TABLE3_FP_FIELDS` cases lack only
`o_DMfp`; every one contains numerical `DMfp` and `e_DMfp`.** The appropriate
interpretation is `COUNT_UNAVAILABLE`, with the released numerical target retained.
It is not established that the FP method was excluded. In particular, group 23771
has 23 observed table2 FP contributors, blank count, and table3
`DMfp=36.694`, `e_DMfp=0.098`. Do not zero-fill a count, infer `k=n`, treat the
numerical target as absent, or infer an exclusion decision from the blank.

The ReadMe defines `o_DMfp` (bytes 114–116, I3) as the number of galaxies with
FP observations, and marks it nullable. `DMfp` and `e_DMfp` are separate nullable
fields at bytes 118–123 and 125–129. The source offers no missing-count rule
that authorizes replacing it with a count inferred from table2.

| Group | Observed galaxies n | Released k | Number of k-subsets |
|---:|---:|---:|---:|
| 34025 | 4 | 3 | 4 |
| 36071 | 133 | 129 | 12,457,445 |
| 47462 | 3 | 2 | 3 |
| 56501 | 2 | 1 | 2 |
| 56962 | 217 | 193 | 51,151,555,361,451,396,680,857,696,101,525 |
| 57215 | 3 | 2 | 3 |
| 57455 | 38 | 34 | 73,815 |
| 1490017 | 1 | 2 | 0 |

These are integer metadata/combinatoric counts, not a mask experiment. The
observed contributors are the already reviewed complete table2 FP sets within
the retained cohort; replacing them by only the SDSS-identified subset would
incorrectly discard the 249 other FP contributors present in 51 groups. A PGC
match to SDSS does not establish that the galaxy-level CF4 value has pure SDSS
subsource ancestry.

The minimal counterexample uses table2 line 28029, byte offset 5353348,
PGC=1490017 and 1PGC=1490017, `DMfp=38.226`, `e_DMfp=0.46`; table3 line 20472,
byte offset 2807894, has 1PGC=1490017, `o_DMfp=2`, `DMfp=37.959`,
`e_DMfp=0.322`. Byte offsets are zero-based; line numbers are one-based.

## Public producer records located, and their present evidential limit

The CF4 paper identifies the EDD methodology and group catalogs. Its FP section
states that five surveys are combined and gives a 3.5-sigma rejection procedure
with 2 ENEAR, 1 SMAC and 17 6dFGSv removals. Those aggregate counts do not identify
the membership of these eight groups. The paper also describes distinct grouping
and scale-registration stages. Their existence makes stage or membership
differences plausible explanations, but does not establish which explanation
applies to a frozen mismatch. [CF4, sections IV.3, XII and Appendix](https://arxiv.org/html/2209.11238v2)

Two official EDD schema pages expose the specific upstream information needed:

* [`kcf4fps`, All CF4 FP Samples](https://edd.ifa.hawaii.edu/describe_columns.php?table=kcf4fps):
  `pgc`, `1PGC`, `T17`, `Nest`, `DM_zp`, `DM_av`, `eDM`, `av_flag`, and
  subsource distance/error/accepted-outlier fields for SDSS, 6dFGSv, SMAC, ENEAR
  and EFAR. `av_flag` distinguishes at least one accepted distance from rejection
  of every recorded distance; the subsource flags distinguish accepted entries
  from outliers. The documented galaxy-level `eDM` is the minimum subsource error.
* [`kcf4fpgroup`, CF4 FP Groups](https://edd.ifa.hawaii.edu/describe_columns.php?table=kcf4fpgroup):
  `PGC`, `Nest`, `Nfp`, `DM_zp`, weighted `DM_w`, `eDM`, unweighted `DM_av`,
  `rms`, `StDv` and group-velocity fields. Its `Nfp` counts galaxies and
  `DM_w` uses inverse-variance weighting.

These are **search-indexed official schema observations**, not acquired
release-matched accepted-member rows. Direct web access returned timeout/502;
bounded ordinary HTTPS requests failed certificate verification before any
payload was acquired. The raw local request failures and measured source-probe
durations are retained in `PUBLIC_SOURCE_RECEIPTS.json`. No certificate check was
disabled, no catalog was bulk-downloaded and no network retry is required to
accept the cardinality counterexample.

The indexed [EDD table selector](https://edd.ifa.hawaii.edu/dfirst.php) reported
55,874 individual entries and 38,057 groups, whereas the frozen CDS files contain
55,877 and 38,053. These are observations of distinct snapshots; they do not
establish the current live EDD counts or the cause of a discrepancy. A matching
catalog name, count at one group, or close numerical values cannot establish
release identity. The paper's example rows do independently show `Nfp=193` at
56962 and `Nfp=129` at 36071, but do not supply their accepted PGC sets.

## Exact fixed-subset method, retained as a derivation rather than an execution

This section supplies the requested mathematical specification so a later
source-bound task does not need to invent an optimizer. It is not necessary to
execute it to obtain this issue's terminal result.

Assume a fixed nonempty subset A of distinct observed table2 galaxies, with
`|A|=k`. For each galaxy, let its printed modulus interval be `[a_i,b_i]` and its
strictly positive printed uncertainty interval be `[s_i^-,s_i^+]`. Define exact
rational weight bounds `l_i=1/(s_i^+)^2`, `u_i=1/(s_i^-)^2`. Let the group target
modulus interval be `[t^-,t^+]`, and the target error interval be `[q^-,q^+]`
with `q^->0`. The model is

```
w_i = 1/s_i^2,
S = sum_A w_i,
M = sum_A(w_i mu_i)/S,
q = S^(-1/2),
target modulus = M + delta.
```

All moduli, uncertainties and delta have units of magnitude; weights have
inverse-magnitude-squared units. The sign convention is explicitly target minus
pooled source. The deterministic offset delta is global across the groups under
test and does not alter q. No sky, cosmological or transfer convention is changed.

The source precision conventions are separately fixed: half of the last lexical
printed place, or one full last lexical printed place. Use closed intervals as
an outer model even at rounding ties. Table2 FP modulus/error quanta are 0.001
and 0.01, and table3 modulus/error quanta are 0.001 and 0.001. Thus even the
half-place assumption is an explicitly independent printed-rounding **outer
model**, not proof of the producer's hidden numeric representation. The model
does not assert stochastic independence or a distribution for rounding errors.

The target-error restriction and box restriction give exactly

```
S in J_A = [1/(q^+)^2, 1/(q^-)^2]
           intersect [sum_A l_i, sum_A u_i].
```

If this intersection is empty, A is infeasible. Otherwise the simultaneous
mean/error feasibility problem is solved as follows.

1. For each fixed S in J_A, the minimum mean uses `mu_i=a_i`. Start every
   weight at `l_i`, then allocate `S-sum l_i` among capacities `u_i-l_i` in
   nondecreasing order of `a_i`. The maximum uses `mu_i=b_i` and allocates in
   nonincreasing order of `b_i`. Equal endpoint values may be ordered by PGC for
   deterministic certificates; that choice cannot change an extremal value.
2. To prove the allocation rule, suppose a lower-endpoint item has spare
   capacity and a higher-endpoint item has weight above its lower bound.
   Transferring epsilon weight from the latter to the former preserves S and
   the bounds, and decreases or preserves the numerator. Repeating these
   exchanges gives the sorted allocation. Reverse the order for the maximum.
3. In a segment between consecutive cumulative-capacity breakpoints, its
   extremal numerator is `alpha+beta*S`. The corresponding mean is
   `beta+alpha/S`, with derivative `-alpha/S^2`. It is monotone or constant.
   Therefore its extrema over J_A occur at J_A endpoints or at a capacity
   breakpoint contained in J_A. Enumerating these finitely many candidates
   gives exact extrema `m_A^-` and `m_A^+` with the q constraint already imposed.
4. The admissible weight box intersected with the S slab is compact and convex.
   Its product with the modulus box is compact and connected. The mean map is
   continuous because `S>0`. Its image in R is consequently the whole closed
   interval `[m_A^-,m_A^+]`, not merely two bounds. This proves that the
   projected delta set for this particular subset is exactly
   `I_A=[t^- - m_A^+, t^+ - m_A^-]` under the stated box model.

This is a special positive-denominator linear-fractional problem. The general
connection to linear programming is classical; the exchange and segment
argument above is supplied here directly, rather than treating a floating-point
solver status as an exact certificate. [Charnes and Cooper (1962), original
reprint](https://iiif.library.cmu.edu/file/Cooper_box00010_fld00009_bdl0001_doc0001/Cooper_box00010_fld00009_bdl0001_doc0001.pdf),
[journal identity](https://doi.org/10.1002/nav.3800090303).

For a group g with known k, let `C_g` be **all** k-subsets of its observed set;
then `U_g=union_{A in C_g} I_A`. Intersect unions as interval sets, preserving
gaps; replacing a union by its convex hull gives only an outer bound. Joint
feasibility for the groups under test requires

```
D = B intersect (intersection_g U_g),
```

where B may be the necessary delta outer interval already obtained from the
22,599 structurally qualified groups. Those earlier results separated the mean
and error projections; their B is **not** evidence of simultaneous mean/error
feasibility for those groups. A nonempty D would establish simultaneous
feasibility only for the newly exactly treated groups, conditional on the box
model, while satisfying necessary conditions for the others. A globally
compatible mask at g must satisfy `I_A intersect D != empty`; local feasibility
alone is insufficient. A unique compatible mask is uniqueness within the
conditional candidate universe, not actual producer genealogy.

Every formula before decimal rendering can use exact rationals because all
printed endpoints are rational and only squared reciprocal errors are needed;
no square root is required to impose q. Extrema candidates, comparisons and
interval-set operations must be rational. If displayed decimals are used,
round lower bounds downward and upper bounds upward. Merely seeing a decimal
overlap cannot justify existence, while a certified disjoint outer enclosure
can justify exclusion. Store rational extrema/active S and weight allocation
if a future execution needs independently checkable certificates.

The fixed-subset method costs O(k log k) to sort and O(k) segment evaluation,
with O(k) memory, excluding rational bit complexity. It does not remove the
combinatorial cardinality problem. No credible unconditional claim is made that
all roughly 5.12e31 masks at group 56962 can be resolved within 538.397892826004
seconds. This report neither silently restricts its candidate set nor supplies
a sampled/fitted mask as a substitute.

For the present eight-group model, `C_1490017=empty` by `k=2>n=1`, hence
`U_1490017=empty` and `D=empty` for every B, every global delta and either printed
rounding convention. This is stronger than a numerical residual check and is
independent of all quoted modulus and error values. The 46 count-unavailable
groups have no specified C_g under this model; their count-constrained inverse
problem is undefined. Their numerical data remain available to a separately
defined future task, without admitting any k or membership now.

## Meaningful limits and minimal next source input

The result excludes repairing all eight mismatches by **deleting from the
frozen observed table2 FP sets while enforcing the released counts**. It does
not exclude group reassignment, a missing contributor, changes between catalog
stages/releases, a count transcription error, or a different counting unit.
The last alternative conflicts with the published galaxy-count semantics unless
supported by explicit producer documentation. It is not licensed merely by the
existence of repeated subsource measurements.

For a substantive next H02 source transition, obtain a release-matched extract
or producer history for the frozen CDS J/ApJ/944/94 stage containing:

* For group 1490017: the two accepted FP PGC identities and their assigned group
  at the table3 pooling stage, or an authoritative correction to `o_DMfp=2`,
  together with the corresponding FP value/error stage. Include extra/reassigned
  contributors; a rejected-only list cannot repair this witness.
* For groups 56962 and 36071: the accepted PGC set and any exclusions/reassignments
  that lead to the released counts of 193 and 129. The `kcf4fps` flags and
  `kcf4fpgroup` summaries are concrete producer candidates, not yet matched
  evidence. Obtain their release identifier/date and stage mapping before using
  their current values to replace old genealogy.
* For 23771 and the other 45 groups: the missing-count semantics or original
  producer count field. Preserve their numerical group FP modulus/error.
* For the upstream SDSS-to-CF4 operator: accepted subsource identities,
  distance/error values, the per-galaxy combination/weight rule and inter-stage
  zero-point mapping. This is separate from group accepted membership. The
  documented minimum-error rule for combined FP galaxy values reinforces why
  blindly summing subsource inverse variances is not authorized.

A source/release identifier, documented stage relationship and finite exact row
correspondence can establish scientific provenance without requiring that an
entire live database equal the old CDS file byte-for-byte. However a numerical
fit to a delta, an arbitrary current EDD snapshot or the right total count alone
cannot establish the missing row genealogy. Record unmatched candidates as
unbound evidence; do not overwrite the frozen inputs. No contact message to
producers has been sent or authorized here.

If an additional unknown subsource bias b is unrestricted, decompositions such
as `released_mu = true_mu + b` are unchanged by
`true_mu -> true_mu + c`, `b -> b - c`. Thus finite printed-rounding intervals
cannot provide a physical truth/error bound when those biases lack a justified
bound or model. Source-dependent angular/depth selection makes a scalar delta
especially insufficient to certify anisotropy. Successful membership inversion
would not establish the empirical calibration-error law or a calibrated
posterior, and would not replace full tensor x, F, Pi, Q or G_F inputs.

## Audit, execution and preserved state

Physics/math audit: conditional cardinality counterexample established from
source-bound metadata; fixed-subset projection formula derived under explicit
positive-weight independent-box assumptions, not numerically executed. No GR
equation, background model, likelihood, uncertainty law or cosmological convention
was modified. Empty-set, k>n, positivity, ties and disconnected union cases are
handled explicitly above. A future implementation would require its own bounded
controls for these cases and for simultaneous q/mean feasibility; none is
required to decide the present cardinality witness.

Claim audit: permitted `DELETION_ONLY_MODEL_EMPTY`, `COUNT_UNAVAILABLE`,
`SOURCE_GENEALOGY_HOLD`, and `SPECIFIED/DERIVED_CONDITIONAL_FIXED_SUBSET_METHOD`.
No posterior, actual accepted mask, global error-law validity, native solver,
physical tensor/denominator/null-coverage admission or H02 PASS is established.
No permanent claim-ledger row is added for this bounded process question.

The original scientific budget remains 600 seconds, with prior observed
cumulative science execution 61.602107173996046 seconds and remaining
538.397892826004 seconds. No new scientific runner, numerical campaign, LP,
mask enumeration, old 64-box Y0 test or FP–TF/SNIa regression was started.
This research used source-document reads, metadata/hash/byte-offset checks,
integer combination counts and bounded public-source discovery. The source
probe's own measured durations are separate provenance, not invented science
execution. Every future scientific process that starts must debit its actual
elapsed time to the same cumulative budget, including failed starts; there is
no new allocation and no ULTRA escalation.

Only the assigned new external research directory was written. Canonical source
files, prior results/reviews, STATE, Git, original 17/42 and alternative 18/42
baselines, R9 and one-use histories remain untouched. No child agent was spawned.
Independent review and scientific admission remain separate from this research
recommendation. Root retains sole canonical writing ownership; its independent
ready full7 work continues without depending on this source HOLD.
