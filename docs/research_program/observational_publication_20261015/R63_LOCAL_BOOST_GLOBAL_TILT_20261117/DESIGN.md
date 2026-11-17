# R63 — fixed design before theory/code construction

Date: 2026-11-17. Baseline: f29bbab420a33aecb1c398ddd961fd45097f536b.
Scope: one ten-stage loop for local observer boost versus physical global tilt.
R2 source mapping is complete. This document closes R3/C3 and R4/C4 before new
scientific code or data fits. Later source-contract findings may narrow physical
interpretation; they do not authorize a new survey campaign.

## R3/C3: definitions and selected experiment

Use (-,+,+,+), physical velocities in km/s and c=299792.458 km/s. Sourceward n,
normalized four-velocities U.U=-c^2, and qualified beta_(X|Y) distinguish observer O,
matter M, radiation energy rest R, total-energy normal N and statistical frame F.
A local tetrad boost cannot change -U_M.U_R/c^2. A spatially global interpretation
additionally requires a source history and congruence, beyond a local invariant.

For a declared bolometric source class at first velocity order, define
A=c(1+z)/(H chi), g=(A-1)/c. At fixed quoted redshift, the processed logarithmic
distance residual is

    eta = g n.(V_S - V_O + V_r)
          + n.[a_cal + (2 V_r - V_O - V_d)/c] + remainder.

V_r is the actual fixed catalogue redshift correction; V_d is its actual distance
correction. They are recorded operations, not independent measured velocities.
The current CF4 source has published Vcmb and calibrated dmzp; its full physical
flux/distance correction contract remains to be qualified. The inherited g model
is therefore a declared working response. Arbitrary common dipole calibration is
profiled; arbitrary functions of angle or redshift are not claimed controlled.

The exact constant-velocity response fibre at this order is
(V_S,V_O,a_cal) -> (V_S+delta,V_O+delta,a_cal+delta/c), for fixed V_r,V_d.
This is a statement about this finite experiment, not a general no-go theorem.

Reuse the FRONTIER compensated dust+radiation first-order Einstein-matter mode:
beta_m(a)=b/a, beta_r=-R b, R=3 epsilon_m0/(4 epsilon_r0), beta_o=b+ell.
For finite post-decoupling a>=a_i, require
max(|b|/a_i,R|b|,|b+ell|)<=beta_* <<1 and small Doppler displacement relative to z.
This has no first-order metric perturbation and generally has quadratic stress.
Its native distance history h=1+z-z A=1-c z g is an established response
specialization, not a new velocity law. After free dipolar calibration, only the
small depth-changing h part remains distinct from constant bulk.

Free endpoint/history diagnostic:
    eta = g n.V_p + z g n.W + n.d + STF nuisance,
    W=c b only if the compensated-history interpretation is imposed.
Under the additional homogeneous-radiation/CMB-reference contract
V_r/c=Delta_obs=ell+(1+R)b, the physical subcase instead obeys
    U=(1+R)W, V_p=U,
    eta = g [1+z/(1+R)] n.U + n.d + STF nuisance.
U is present matter relative radiation; W is matter relative normal. A bulk of
hundreds km/s in U is not hundreds km/s in W. No CMB marginal error bars are
converted into a fabricated 3D likelihood. Pure observer boost, in this corrected
chart and after free d, has no remaining velocity column; constant coherent bulk
g n.V is a distinct comparator and is not labelled pure observer boost.

Actual experiment: original R58 y32,C32 (all dipole12/STF20 cross covariance),
35970 CF4 groups, four overlapping source windows, seven retained nuisance
operators. Use actual O_m applied to each new source design, never infer new
response columns from the old 11-dimensional sufficient score. Reuse J2 tensor
Legendre source mean as primary and J3 as sensitivity, retaining vector/STF cross
covariance. No independent multiplication of the seven correlated experiments.

## R4/C4: finite construction and acceptance

1. Reproduce R62 constant-bulk fits and carrier hashes as source parity controls.
2. On the inherited fixed background, fit the free [V_p,W,d,K_0..K_J] response
   (24 parameters for J2,29 for J3), test W=0 by exact nested Gaussian Wald/LR,
   and report nuisance-profiled history singular values in declared physical units.
   A large unconstrained W is a tangent-model coefficient, not a physical tilt.
3. Add one explicit flat dust+radiation+Lambda benchmark with the existing
   Omega_m=0.3153 and declared Omega_r=1e-4, hence R=2364.75. This radiation
   density is a benchmark, not an inferred parameter or precision cosmology prior.
   Use independent Gauss-Legendre distance quadrature for chi_r, include
   mu_0=ln(chi_old/chi_r) in the old eta chart, and use g_r consistently. Keep the
   inherited covariance as a declared fixed working law, not a newly calibrated
   two-fluid covariance. Execute constant-bulk and physically tied-history fits
   on the same y-mu_0 and nuisance space; their non-nested residual difference is
   descriptive and receives no invented chi-square or Bayes-factor calibration.
4. After projecting constant bulk, calibration and STF nuisance, compute the
   exact conditional separation matrix S=D^T D for the tied-history response.
   Evaluate observed-size and explicitly fixed 300 km/s amplitudes and the
   declared matter/radiation perturbative body. For any uniformly size-alpha
   test, a nearest-null simple Gaussian pair gives the oracle power bound
   Phi(Phi^-1(alpha)+sqrt(U^T S U)); identify its limited experiment/model scope.
   Calculate principal angles/response discrepancies without declaring missing
   physical remainder or unknown systematics negligible.
5. Meaningful checks: independently derived endpoint signs and catalogue chart;
   exact common-boost/calibration null fibre; compensated momentum and h identity;
   known limiting backgrounds; quadrature refinement; units; actual-operator
   small-amplitude injection; nested Wald/LR; R62 parity; rotation covariance;
   nuisance expansion by one depth-dipole block as a sensitivity for J2 only.
6. Use existing tensorized five-variable definitions, retaining likelihood score,
   precision, stable whitened factors, full cross covariance and exact image/null
   information. Do not present conventional Gaussian compression as a new
   probability law or identify a statistical noise gauge with physical MES.

No Boltzmann solver, new catalogue, new O(N^2) covariance, full nonlinear
Einstein history, arbitrary systematic immunity, standalone CMB aberration
likelihood, or second research loop is authorized by this design. Absence of an
available independent anchor is an unresolved source obligation, not a no-go.

Primary verification precedes the actual-data run. Stage8 will assess physical
domain/remainder and interpret data. Stage9 has one fresh independent review and
one bounded repair episode. Stage10 records a finite paper plan, additive P4 DAG
updates, preserved original acceptance gates and authorized non-force push.
Journal status remains NOT_READY_TO_SUBMIT until source/remainder and empirical
coverage gates are met. No local-agent restart prompt will be produced.
