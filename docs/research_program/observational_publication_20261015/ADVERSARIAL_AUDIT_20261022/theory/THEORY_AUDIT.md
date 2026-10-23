# Two-redshift observer equivariance and V03 acceptance audit

Date: 2026-10-22. Subject owner: HTT. Audit owner: COMMON. Source repository:
`cosmosapjw-quantum/htt_base` at `76595070beb97e52dce9f2d7a0ff1dbf3c289e98`.
Scope: C0 analytic/method validation; no observational significance or publication
admission. Requested author runtime: Astra/xhigh; observed backend: UNKNOWN.
This is an isolated selected-file audit, not a repository checkout or new clone.

## Findings that change the next research action

1. **The existing compensated history is a valid, already independently reviewed
   linear physical subcase.** Its same-frame, distinct-response, units clauses
   meet the text of V03's acceptance. V03's separate requested output still says
   external Einstein–Boltzmann history; that specific payload was not delivered.
   A transparent alternate-output adjudication can recognize this progress.
2. **The current selected-design report is scientifically careful.** Its 12/15
   combined rank is explicitly a comparison of distinct forward models. It must
   remain a conditional design warning. No new defect was found in its algebra;
   using that zero space as a physical local/global no-go would be an invalid
   downstream inference.
3. **A source-processing null can proceed before a parent selection law or a
   full physical likelihood.** The exact observer-boost identity below tests the
   two-redshift distance/magnitude pipeline on the same source labels. It gives
   a finite deterministic tube for incomplete magnitude or redshift corrections.
   This is the new calculation here. It does not rerun the completed V02 finite
   CMB boost or R7 nuisance-ellipsoid results.

## Evidence read and reuse

Read AGENTS.md and CURRENT_CODEX_RUNTIME.md, project physics/math, local/global,
observable-statistics, claim-firewall and physmath audit skills; global physmath
policy, theory loop and evidence/handoff references. Read the pinned:

- FRONTIER_20261020/projection/REPORT.md and distance/CONDITIONAL_MODEL.md;
- RESEARCH_LOOP_20261022/THEORY.md, selection/REPORT.md, LEGACY_MAP_KO.md;
- FRONTIER_20261020/theory/THEORY.md, CLAIMS_AND_TRANSFER.json, SOURCES.json;
- FRONTIER_20261020/INDEPENDENT_REVIEW.md;
- tensor_joint_r7/THEORY.md; mes_tensor_research_integration/RESEARCH_SYNTHESIS.md;
- solver_free_research_20261014/research/THEOREM.md; PUBLICATION_DAG.json.

The first-order endpoint derivation, compensated history, finite nuisance
ellipsoid, robust-rank perturbation lemma and existing selection bounds are
reused. No old catalogue fit, 97-LP campaign, Gaia stream, CMB boost campaign,
54-history/432-optics campaign, or ODE was rerun.

Primary comparison: Horstmann, Pietschke & Schwarz,
[arXiv:2111.03055v2](https://arxiv.org/html/2111.03055v2), section 2, Eqs. (5),
(8)–(11), (13), read 2026-10-22. Those equations give distance duality, exact
observer solid-angle aberration and the first-order source/observer distance
terms. Its arbitrary-relative-vector Eq. (6) is not used as an exact formula.
The exact boost statement below is derived directly from the photon energy
ratio and aberration; it is not claimed as a new relativity theorem. The
contribution is the finite two-redshift pipeline target and its failure tube.

## 1. Exact same-source observer-boost lemma

Use signature (-,+,+,+). Fix spacetime, one emission event and source velocity,
one observation event, and the source's proper bolometric luminosity. Compare
two observer tetrads with future timelike velocities u and u'. For the same
photon four-momentum k define

\[
\delta=\frac{-u'\cdot k}{-u\cdot k}>0.
\]

This definition avoids ambiguous boost/line-of-sight sign conventions. If n is
sourceward in the unprimed tetrad and u' moves by beta=v/c relative to u,
\(\delta=\gamma(1+\beta\cdot n)\). Aberrate n when comparing primed directions;
keep the same source label, not the same angular pixel.

For a point source or differential ray bundle in geometric optics with
distance duality,

\[
1+z_H'=\frac{1+z_H}{\delta},\quad
d\Omega'=\delta^{-2}d\Omega,\quad
D_A'=\delta D_A,\quad D_L'=\frac{D_L}{\delta}. \tag{1}
\]

**Proof.** The source photon energy is fixed, so dividing by the observed
energy gives the first identity. Aberration gives the second. The emitter
screen area in \(D_A^2=dA_s/d\Omega\) is fixed, giving the third. Apply
\(D_L=(1+z_H)^2D_A\) to obtain the fourth. Equivalently, the point-source
bolometric flux obeys \(F'=\delta^2F\), with the source luminosity fixed.
No FLRW geometry or time evolution is needed for these local transformations.

Take a catalogue comparison distance

\[
D_{cat}=(1+z_H)\chi(z_D),\qquad
R=m-M-5\log_{10}(D_{cat}/{\rm Mpc})-25. \tag{2}
\]

Here chi is any fixed positive comparison-distance function. Suppose z_D is
recomputed in a **fixed reference tetrad** for the same ray; hence z_D'=z_D.
For bolometric m, Eq. (1) gives \(m'=m-g\ln\delta\), \(g=5/\ln10\), and

\[
\boxed{R'=R,\qquad \frac{D_L'}{(1+z_H')\chi(z_D')}
=\frac{D_L}{(1+z_H)\chi(z_D)}.} \tag{3}
\]

The restriction on z_D is substantive: a reference-frame correction including
an estimated source PV must be transformed covariantly with its source model.
Keeping a raw observer-frame PV estimate numerically fixed need not satisfy it.
The theorem holds to all boost orders for its stated optical experiment.
It neither assumes nor establishes a Lorentz transformation law for released
SALT2 standardized magnitudes.

## 2. The three derivatives are different experiments

| Experiment | What is held fixed | Response |
|---|---|---|
| Passive observer reboost of the same source measurement | Source/ray, fixed reference z_D, comparison chi; transport m and z_H | Eq. (3): zero |
| One-redshift Hubble residual | D_cat=(1+z_H)chi(z_H); transport m and z_H | Nonzero radial-coordinate change; at zero boost the forward effect is g A n·beta |
| Infer a candidate reference velocity from fixed measured data | m,z_H,n fixed; z_D(beta) recomputed from the trial reference correction | \(\partial R=-g(\chi'/\chi)\partial z_D\), giving an A-type column |

For the last row, if \((1+z_D)=(1+z_H)\delta_{trial}\), then
\(\partial R/\partial\ln\delta_{trial}=-g(1+z_D)\chi'/\chi=-gA\), with
\(A=c(1+z_D)/(H\chi)\) when chi'=c/H. Thus observer equivariance is **not** a
no-information theorem about unknown cosmic rest frames. A candidate frame
parameter is changed relative to the fixed data; a passive reboost changes
the data and tetrad together.

The current two-redshift first-order result
\(R_{frac}=(1-A)s+Ar+Ap+k_m\) is consistent with Eq. (3): the local observer
o cancels when r is fixed and all source labels are transported. The old
same-observer column \(A n\) remains correct in its original experiment. It
cannot be transferred to a different fixed-release experiment merely because
both expressions contain the word 'redshift'. A numerical n/r re-fit of the
651-row fiducial design would not resolve this distinction.

## 3. Finite correction tube and an explicit bandpass falsifier

For a general standardized magnitude pipeline define its actual mismatch

\[
\kappa_i=m'_{corr,i}-m_{corr,i}+g\ln\delta_i,\qquad
\eta_i=z'_{D,i}-z_{D,i}.
\]

With z_H transformed correctly, exact subtraction of Eq. (2) yields

\[
\Delta R_i=\kappa_i-g\ln\frac{\chi(z_{D,i}+\eta_i)}{\chi(z_{D,i})}. \tag{4}
\]

This algebra is exact. To turn it into a physical bound requires externally
justified bounds on the actual pipeline kappa and eta. If
\(|\kappa_i|\le k_i\), \(|\eta_i|\le e_i<z_{D,i}\), and chi is positive
and increasing on \([z_D-e,z_D+e]\), then

\[
\boxed{-k_i-g\ln\frac{\chi(z_D+e_i)}{\chi(z_D)}\le\Delta R_i
\le k_i-g\ln\frac{\chi(z_D-e_i)}{\chi(z_D)}.} \tag{5}
\]

These endpoints are attained in the relaxed independent-box class by
\((\kappa,\eta)=(-k,+e),(+k,-e)\). Correlated physical correction errors can
make the true interval narrower. If z_D-e<=0, this specific finite logarithmic
bound is unavailable; one must supply a tighter positive-distance domain.
For any prechosen same-source contrast w, interval propagation is exact for
independent row boxes: sum the lower or upper endpoint according to the sign
of w_i. Shared calibration uses its common feasible set instead of independent
row boxes. No Gaussian distribution or covariance inversion is needed.

The bandpass caveat has a constructive counterexample. Intensity invariance
\(I_\nu/\nu^3\), frequency \(\nu'=\delta\nu\), and aberration imply for a
point source \(F'_{\nu'}(\nu')=\delta F_\nu(\nu'/\delta)\). A fixed observer
band R(nu) therefore gives

\[
F'_R=\delta^2\int R(\delta\nu)F_\nu(\nu)\,d\nu. \tag{6}
\]

Bolometric R=1 gives delta^2. For a power-law spectrum F_nu proportional to
nu^(-alpha) over the relevant frequencies, a fixed band instead gives
\(F'_R=\delta^{1+\alpha}F_R\). Consequently,

\[
\kappa=\frac{5}{2\ln10}(1-\alpha)\ln\delta. \tag{7}
\]

This is nonzero unless alpha=1, even though the optics is perfectly Lorentz
covariant. An actual supernova check must transform its spectral time series,
filter response and phase/standardization together. Equation (7) prevents
mistaking a bandpass effect for failure of local special relativity or a
global-tilt signal.

## 4. Actual minimal computation

Command executed once, exit 0:

```
python -B HTT_AUDIT_20261022/theory/verify_two_redshift_null.py
```

The script uses only standard-library finite arithmetic and the existing exact
flat dust+radiation algebraic comparison distance. It writes RESULT.json.

| Check | Actual result |
|---|---|
| Twelve finite observer boosts, four directions/three depths, speed about 0.165c | Max Eq. (3) roundoff 3.55e-15 mag |
| Wrong pipeline: transform z_H but freeze m | Spurious residual range [-0.17463, 0.27625] mag, equal to g ln(delta) |
| z_D=0.02, e=0.0002, k=0.0005 mag | Exact attained interval [-0.02178703, 0.02200413] mag |
| Fixed-band alpha=0.4, delta=1.0012 | 0.0007812614043 mag residual, agrees with Eq. (7) |
| Fixed-data trial-frame derivative at z=0.08 | -27.6757731621 vs analytic -27.6757731702 per unit log Doppler factor |
| Domain z_D-e<=0 | Rejected explicitly |

The large finite-boost witness tests the exact local transformation; it is
not inserted into the earlier small-velocity compensated cosmological model.
Wolfram separately reduced Eq. (3), the kappa cancellation and Eq. (7) to
{0,0,0}. The exact calls/results are recorded in WOLFRAM_CHECK.json. No
four-axis CAS, physical null calibration, data fit, or statistical power is
inferred from these arithmetic checks.

## 5. V03: original and revised acceptance are distinct

The original node has objective 'Obtain physically distinct global tilt
source-history response (not endpoint copy)', output 'external
Einstein-Boltzmann history response and validation', acceptance 'Same-frame,
different radial/temporal transfer and exact source units', and external
missing 'Calibrated global-tilt history/source transport unavailable'. It
depends only on V01, already completed_scoped.

| Clause | Existing exact evidence | Verdict |
|---|---|---|
| Physical relative-motion history | beta_m=b/a, beta_r=-R b; positive dust/radiation momenta cancel; zero linear stress perturbation apart from canceled momentum | Pass in finite post-decoupling first-order model |
| Same frame | Normal total-energy tetrad; dust source; observer beta_o=b+ell; radiation frame distinct | Pass |
| Distinct temporal/radial response | A=c(1+z)/(Hchi), h=1+z-zA; d(h/A)/dz=H'chi/c>0 for the positive two-fluid background | Pass; not an endpoint copy |
| Exact source units | b,ell physical v/c; chi length, H inverse time, fractional bolometric distance dimensionless | Pass |
| Validation | FRONTIER_20261020/INDEPENDENT_REVIEW.md PASS_SCOPED: separate source checks, constraints/history/endpoint signs, 14 test reuse and independent finite stress derivative | Pass at that linear scope |
| Original external general payload | No external history atlas/transport calibration supplied | Unmet original output |
| Actual released-data optical operator, selected law, finite application error | Not supplied by this linear model | Downstream V04/V05/application obligations |

The model uses independently prescribed post-decoupling isocurvature velocity
IC. It does not establish generation from primordial tight coupling. Its
compensation makes R|b| smallness restrictive; no 300 km/s observed dust flow
can be inserted without checking the radiation speed. These are explicit
model assumptions/domain restrictions, not a defect in the first-order proof.

**Recommended minimal policy override, for parent adjudication:** preserve the
original V03 record and unmet external payload. Permit
`DERIVED_PHYSICAL_HISTORY_SUBCASE` as an alternate output for a named material,
IC, source and order, provided the unchanged same-frame/distinct-response/units
criteria and independent physical validation are met. The current user's
solver-free direction supports replacing the external-only method requirement;
it does not support weakening physical consistency. The compensated model
meets that alternate output. Mark any accepted status explicitly
`completed_scoped: compensated linear dust+radiation bolometric history`.

This changes method/output scope, not the historical scientific result. If
accepted, report 18/42 under the revised scoped-output rule versus 17/42 under
the original external-output requirement (assuming no other node changes).
V04/V05 retain source matching, nuisance/selection/covariance/remainder and
calibrated inference. B02 retains its full polarized transfer requirement.
No native Bianchi family claim, whole P4 completion or submission readiness
follows. The parent/reviewer owns this status adjudication; this worker has
not mutated the DAG or published anything.

## 6. Exact next inputs and stopping rules

The immediate useful implementation is a **paired source-processing test**:
feed the same retained supernova spectral/lightcurve fixture through its actual
pipeline in two observer tetrads, then compare Eq. (4) with the declared tube.
Required inputs are the producer's lightcurve/spectrum, passbands, phase and
standardization map, exact zHEL/zHD/PV correction implementation, tetrad and
aberration convention, and immutable source-row mapping. A small representative
producer fixture is sufficient for this operator test. Full parent selection
and CF4 cross-covariance are not prerequisites for a same-object deterministic
equivariance test. They remain prerequisites for the later population claim.

A fake test that manufactures m' solely as m-g ln(delta) verifies algebra,
not the actual release pipeline. The current script is expressly that algebra
falsifier plus two deliberately wrong-pipeline witnesses. It cannot close the
real SALT2 response obligation without the producer inputs just listed.

If a stochastic paired discrepancy is later tested, its covariance is
\(C_{11}+C_{00}-C_{10}-C_{01}\). The two reprocessed versions share the same
measurement and calibration realization. Independent-error addition would
invent data. MES and morphology likewise remain functionals of their common
CMB carrier and must enter the same joint law, not a second likelihood factor.

This route preserves the original local-boost/global-history and tensor-MES
intuition: qualify the measured operator first, retain full morphology and
joint dependence, then compare a physically specified history against the
kinematic null. None of the current finite-rank or missing-input statements
proves a universal impossibility. No new strong no-go or priority claim is
proposed; NG1–NG7 admission is therefore not invoked.

Research-loop disposition: R1–R4 reuse/contract complete; R5 exact lemma and
tube derived; R6 symbolic/primary-equation comparison complete; R7 finite
falsifiers executed; R8 conditional adoption recommended; R9 code+equation
handoff provided; R10 this unit complete, producer-data application open.
