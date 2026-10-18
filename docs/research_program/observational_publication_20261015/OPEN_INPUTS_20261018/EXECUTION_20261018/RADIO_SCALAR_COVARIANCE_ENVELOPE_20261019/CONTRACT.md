# Radio conditional scalar-marginal PSD covariance envelope

Approved by read-only /root/radio_covariance_bound_frame, requested
gpt-6-astra/xhigh, observed UNKNOWN. Parent serialized the returned contract.
Base 9a56d1eccfb6ab4bd2413f160f971e406e1a7db3, existing branch
research/htt-open-input-theory-20261018. No new framing numerical work consumed.
Owner obsstat; C0; DIAGNOSTIC_ONLY; transfer_source none.

## Question and immutable inputs

Compute 104 coordinatewise variance maxima: 13 retained coordinates for EACH of
eight existing D05 radio estimators, over PSD covariances with prescribed scalar
marginals and otherwise free within-source and cross-source covariance.
Reuse D05_GAIA_RADIO/observable_vsh.py SHA256
318acb829f163eedda76a136a0edc4d247c17a6893f2faf24681e34fd79822b5
and RESULTS.json SHA256
386bfa19ff1f0c24ec836f2e3e471717edf38c3c10da6d119d70548cf062baa0.
Raw directory /mnt/extdrive/workdir/htt_open_data/vlba/233_3/:
table6.dat 99085 bytes SHA256
5358da3b6233194cad556010259400b729b7472c5037e39facf1f413e2aa3bff;
ReadMe 13460 bytes SHA256
cb6d18077090e27b803924068c2c9a8b52e2991d61882ff6cc502cefe0274b98.
Verify identities before use. Preserve all 713 rows and published order.

Read ONLY required geometry/error fields: RA hours slices [9:11], [12:14],
[15:24], multiply position hours by 15 to degrees. Declination sign [32],
components [33:35], [36:38], [39:48]. Motion errors [65:72], [92:99] are ALREADY
microas/year: NO factor 15 or 1000. Position errors are not motion errors.
Require 713 valid rows, finite directions/errors, positive motion errors;
reject invalids, never drop/zero-fill/add source cuts. Unused nulls remain unused.
CDS labels positions J2000 at most recent VLBA observing epoch, NOT Gaia J2016.0;
condition on released directions and selection, do not propagate epochs.

## Frozen maps

Scenario order: published_pmRA_is_tangent with rho -0.9,-0.5,+0.5,+0.9;
then published_pmRA_is_coordinate_rate with rho -0.9,-0.5,+0.5,+0.9.
Neither RA interpretation is resolved or preferred. Tangent sigma_alpha*=raw
RA error; coordinate-rate sigma_alpha*=cos(dec)*raw RA error. Sigma_delta is
raw DE error in both. Require transformed errors finite and strictly positive.

Reuse D05 design(), precision(), STF basis and full16 column order.
KEEP=[0,1,2,6,7,8,9,10,11,12,13,14,15], FRAME=[3,4,5]. Retained order:
E1_x,E1_y,E1_z,E2_xx-yy,E2_zz,E2_xy,E2_xz,E2_yz,
B2_xx-yy,B2_zz,B2_xy,B2_xz,B2_yz. These are Cartesian/Frobenius-STF
coordinates, not normalized Y_lm amplitudes/powers. Physical B1 UNKNOWN.

C_si=[[sigma_a^2,rho*sigma_a*sigma_b],[rho*sigma_a*sigma_b,sigma_b^2]],
W_si=C_si^-1. Read full cached16x16 V_s; R selects KEEP;
M_s=R V_s, L_si=M_s X_i^T W_si. NEVER truncate design or V before full mapping.
Construct N_s=sum_i X_i^T W_si X_i during the one actual calculation for checks.
No new RHS, motion fit, normal(X,y,w), solve(stats), holdouts or crosswalks.
Coefficients unnecessary; any displayed coefficient must be copied from D05.
Working rho defines the estimator map, NOT true correlation assumptions.

## Functional and derivation

For flattened1426 scalar errors with finite second moments and
Sigma PSD, Sigma_aa=sigma_a^2, a fixed row ell has sharp coordinatewise
v_max=(sum_a |ell_a|sigma_a)^2. PSD implies |Sigma_ab|<=sigma_a*sigma_b.
Attainment: Sigma=u u^T, u_a=sigma_a sign(ell_a), choosing either sign for zero
weights, preserves all diagonal entries. Positive-definite restriction gives
the same supremum. True correlations include endpoints +/-1, NOT only four rho.

For each coordinate use a_i=ell_i,alpha*sigma_alpha, b_i=ell_i,delta*sigma_delta:
vmax=[sum_i(|a_i|+|b_i|)]^2;
d=sum_i(a_i^2+b_i^2);
vwork=sum_i[(a_i+rho*b_i)^2+(1-rho^2)*b_i^2].
d is a computational sum, NOT a filled-in observed covariance. vwork is a
conditional old working reference, not measured source independence.
Use float64 and compensated/extended-precision accumulation, reject nonfinite
values, no clipping. Variance units (microas/year)^2; sqrt units microas/year.

## Acceptance for every scenario

V expected16x16, finite, symmetric numerically, positive diagonal;
N nonsingular positive definite. max|V N-I|<=1e-10.
max|sum_i L_i X_i-R|<=1e-10; report frame columns separately.
V[KEEP,KEEP] vs existing frame_projected.covariance_uas2yr2:
E(A,B)=max|A-B|/(1+max|B|)<=1e-12. Use E<=1e-12 for V symmetry as well.
Every d_old=diag(R V R^T)>0, |vwork-d_old|/d_old<=1e-10, NO absolute tolerance.
Outputs finite/nonnegative; vmax>=(1-1e-10)*vwork;
vmax>=(1-1e-10)*d; vmax<=(1+1e-10)*1426*d.
Store all8 new N matrices as compact consumed derived statistics for review,
not raw rows or row-level weights. Observable frame quotient does not recover
physical B1 or NNR-removed signal.

## Focused controls BEFORE actual source calculation

Zero weights EXACT zero. One scalar ell=-2,sigma=3 ->36.
Two scalar ell=(1,-2),sigma=(2,3) ->64, witness u=(2,-3);
fixed block [[4,1],[1,9]] would instead give36 (catch Gaia formula reuse).
Four scalar ell=(1,-2,3,-4),sigma=(2,3,4,5) ->1600, d=584.
Check rank-one witness PSD/diagonal/attainment including zero weight;
component/source permutations, overall weight sign, chunk addition, unit scaling.
Clarification APPROVED by same Astra framer: RA coordinate-rate hypothesis at
dec60, T=diag(1/2,1). Raw ell=(1,-1),sigma=(2,3) gives25; tangent ell=(2,-1),
sigma=T*sigma_raw=(1,3) gives25, with ell_raw=ell_tangent*T. Pairing tangent ell
with untransformed raw errors instead gives49 and is NOT this invariant control.
Small deterministic geometry: compare full16 selected map with explicit Schur
map, verify frame annihilation, no motion fitting. Invalid/nonfinite errors,
scenario mismatch, malformed required fields fail visibly.
Finite nonzero algebra E<=1e-12; numerical zero absolute<=1e-12;
zero-weight kernel EXACT zero.

## Resource/ownership/stopping contract

One cumulative60-second numerical budget includes controls, actual8-map713-row
calculation, plots, failures and any review checks. Framing used0 numericalseconds.
Canonical .venv/bin/python; one backend thread, <=2 observed OS threads,
RSS<=512MiB. Adapt existing bounded runner in this NEW directory, pin backend
environment, record actual command/START/END/exit/resource observations.
An incomplete accounting entry blocks continuation until reconciled.
Controls must completely PASS before ONE actual calculation. Reserve >=8seconds
for plot/review before actual launch. No automatic retries/source rerun/cap
increase/tolerance change. Stop on any failure, preserve raw evidence/preimages,
return for interpretation and explicit bounded repair if approved.
Original inputs and completed D05/Gaia calculations read-only, no replay.
Worker owns new implementation/tests/results/plots/report/usage in this directory;
parent owns this contract and common progress notes/review recording/publication.
No nested agents, no new checkout, no Git operations by worker/reviewer.

## Required outputs and scientific ceiling

Code/tests; complete104-row RESULTS with vmax/sqrt/vwork/ratio/residuals and8N;
raw logs and usage; PNG/PDF showing ALL104 values in fixed scenario order, useful
two-convention columns with13x4 heatmaps of sqrt(vmax) and sqrt(vmax/vwork).
Not confidence error bars. Concise derived report, plot/source provenance,
requested author Sol6.1/high vs observed UNKNOWN. Fresh independent read-only
Astra/xhigh review of final candidate required before publication; any numeric
review uses SAMEremaining budget and cached/finite inputs, no actual-source replay.

Published marginal errors are a WORKING hypothesis for the selected catalogue,
not established total physical variances. Actual frame/NNR constraints may exclude
maximizing Sigma. Bias unmeasured: centered-variance envelopes, NOT bias/MSE bounds.
104 maxima need not be jointly attained; their diagonal is neither joint covariance
nor Loewner upper bound. Eight maps do not cover all weights, choose convention,
or establish Gaia-radio independence. No confidence/coverage/pvalue/cosmiccurl/
mattervorticity/native solver/familyID/K03 admission. Original17/42 and allsix
NOT_READY_TO_SUBMIT unchanged. Source drift/invalid/order mismatch/map failure/
nonfinite/resource exhaustion => exact failure HOLD, not exclusions or relaxation.
