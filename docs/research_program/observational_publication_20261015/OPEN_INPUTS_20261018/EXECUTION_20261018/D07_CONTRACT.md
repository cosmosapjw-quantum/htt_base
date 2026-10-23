# D07 bounded joint-calibration execution contract

2026-10-18, read-only framing `/root/open_d02_review`, requested Astra/xhigh,
observed UNKNOWN. Parent records its executable contract. A different reviewer
must assess execution. Original science acceptance remains HOLD.

Writer owns only D07_JOINT_CALIBRATION/. All D02/D03/H02/theory read-only.
Two threads, existing .venv; no solver/ODE/MCMC/upstream code execution, no
35970-group refit, no six-maser augmentation or publication. One numerical run,
at most97LPs, at most10minutes; preserve first failures and cumulative counts.

Inputs: reviewed D03 aggregate c326fc79b4cfd255d4655cb47b27a4b399403179c3342ac30ae7113c80dcc388,
result c711a82bf5dbe95fd7bd847fea2d7b7d8f30e18463d9113de406ae16dbbf7296,
all graph/NPZ/source identities; selected CF4 NPZ
86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c;
existing frozen H02 centers/five windows/four pooled partitions/eight coefficients
and unchanged Gaussian-marginal box rule, delta_relative_mag=.02. D02 supplies
only overlap/outcome annotations, never inverse-selection weights.

Join exactly559 D03 rows to selected H02 groups before exclusions. Retain exact
group IDs, pooled DMzp/error/direction/partition; a=DMzp_group-MU_SH0ES, not
method-specific DMsnIa/DMtf. Separately retain77 published calibrator rows with
c=MU_SH0ES-CEPH_DIST. Keep every exclusion and repeated host/group, Pantheon
row index and overlap between blocks. These are not independent likelihoods.

J2000 equatorial raw basis X=(nx,ny,nz,nx²-nz²,ny²-nz²,2nxny,2nxnz,2nynz).
All angular coefficients mag. Use selected group direction for a, corroborated
host direction for c. Any uncorroborated calibrator direction remains UNKNOWN,
not zero/imputed; report retained support explicitly. Pantheon angular response
in a is transported to group direction; unmeasured angular/depth transport
discrepancy belongs to the declared pair-comparison remainder.

One shared parameter vector:

```
b_mw = theta_w + eta + gamma_m + epsilon_mw
a_i = Za_i alpha + Xg_i (eta + gamma_m(i) - kappaP) + ra_i
c_i = Zc_i beta + Xh_i (kappaP - kappaC) + rc_i
```

Za/Zc contain common and applicable observed survey/partition scalar offsets;
retain redundant columns and explicit SVD quotient. Pantheon/Cepheid angular
responses kappaP/kappaC unrestricted, never zeroed or called independent anchors.
Same gamma_m across all H02 windows and a. H02 pooled partitions are not raw
calibration contributor labels. For each eight-basis vector v, build actual-design
gauge witness theta_w→theta_w-v, eta→eta+v, kappaP→kappaP+v,
kappaC→kappaC+v, gamma unchanged. Check all displayed predictions cancel.
Nonempty feasible set therefore has unbounded eta and theta coordinates.

Invariant targets zeta=eta-kappaP, psi_w=theta_w+kappaP,
chi=kappaP-kappaC. Determine actual estimability after nuisance projection;
psi is a relative apparent field, not physical shear/tilt.

Reference deterministic constraints ||Wa(a-Da p)||inf<=t and
||Wc(c-Dc p)||inf<=t. Wa whitens symmetric Pantheon selected subblock plus
B diag(eDMzp²) Bᵀ. Zero crossblock is a chosen reference norm, NOT a measured
missing covariance. Wc whitens symmetric calibrator Pantheon subblock only.
No joint covariance/coverage/confidence label. ra includes unmeasured pair
transport; this t is not a physical finite-z/flow bound.

Use unchanged H02 marginal boxes and shared relative-gamma bounds. One LP
minimizes compatible t. At t=tmin+{0,1,2}, project eight zeta and eight base-window
psi coordinates (96 endpoint LPs). Literal finite/infeasible/unbounded/UNKNOWN
statuses; increments are dimensionless sensitivity choices, not measured error.
For chi report actual nuisance/relative-response ranks/nullspace only.

SVDtol=max(shape)*eps*smax; disclose singular values/ranks at0.1x,1x,10x.
Unstable rank UNKNOWN. Scaled gauge infinity residual<=1e-12, permutation
invariance. HiGHS primal/dual1e-9; independently verify retained endpoint
witness constraints<=1e-7mag H02 and<=1e-7 reference units. No tolerance
relaxation on failure. Stop with raw issue on source/rank/solver ambiguity.

Artifacts: code/tests/result/small actual design+witness NPZ/one figure/report.
No permanent gate/claim-registry expansion; no canonical-node promotion.
Official SH0ES MCMC_utils.py confirms y-q@L (47x3492), but full authoritative
47-column host/parameter mapping is unresolved; do not infer it from values or
table ordering. This blocks a new named ladder fit, not this relative calculation.

Framer support clarification: use75 source-supported calibrator rows (same-release
unique SNID/IAUC, corroborating SN sky and valid named-host J2000 coordinates).
CF4 association is not required for this SN–Cepheid block;65 CF4-linked remain
a separately labelled subset. Retain77 in inventory;2005df_ANU and2008fv_comb
are UNKNOWN_HOST_DIRECTION and excluded only from angular fitting/scoring.
Use the same75indices for design/response/reference covariance, with repeated
host incidence. No independent host validation/geometric anchor is claimed.
