# Bounded independent physical review, R6

This pass checks the new P1–P11 derivations, the finite four-window H03 response experiment, and the source-bound R28 unit correction. It finds the finite GLS calculations correct and the physical constructions usable with the local conditions below. It makes no broad novelty, admission, or family-wide exclusion judgment. No catalogue fit, native cosmological solver, Boltzmann calculation, map analysis, or ODE was run.

Requested runtime: `gpt-6-astra/xhigh`; observed runtime: `UNKNOWN`. This is one fresh-context native child pass, with no nested agents. The independent numerical implementation uses eigensystem whitening and SVD, whereas the parent uses Cholesky whitening and least squares. No author function was imported or executed.

## Current material findings and smallest repairs

1. **P11 present-day normalization — FIX_SOON, local formula repair.** The stated profile `sigma(t)=H0*s0*g(t)` gives `sigma(t0)/H0=s0*g(t0)`. Therefore the printed `Sigma0=||QT||/(sqrt(6)*|J|)` requires **g(t0)=1** and H0=H(t0). Without that normalization the correct expression contains `|g(t0)|`. A constant profile g=2 is a factor-two counterexample: the printed expression returns half the actual present-day normalized shear. Add the normalization, as the parent has agreed to do. The integrated-deformation equation and its norm inequality remain valid under their stated optical approximations.

2. **P9–P10 tilt orientation — FIX_SOON, convention repair.** The metric's original source, printed p.148/PDF p.149, explicitly has A0>0. Restore A0/X>0, H>0 and define beta as the fluid velocity along the oriented +z axis in the signed momentum equation. State the speed bound in P10 for `|beta|`, or choose the axis so 0<=beta<1. The squared shear–tilt curve is unchanged. The original metric supports this repair directly; no new dynamical assumption is needed.

3. **P4 proper/comoving divergence — local notation repair.** The velocity jet uses proper separation r, so its theta is `theta_phys=div_r(v_p)`. Write `theta_com=div_x(v_p)=a*theta_phys=-a*H*f*delta` and `theta_phys=-H*f*delta`. Using one theta for both derivatives makes it too easy to insert an extra scale factor into P4. The reported isotropic slope shift `-H*f*delta/3` is already correct.

4. **P6 attainability and P7 coefficient metric — state the domain once.** P6 is exactly attained for the *unrestricted twelve-dimensional whitened mean-error ball*. For a smaller physical error family, the displayed eta95 is a necessary budget, and sufficiency requires that family to contain the attaining direction. P7's `sqrt(q*lambda_max(C_Q))` is a Frobenius tensor radius when C_Q is written in Frobenius-orthonormal STF coordinates. This holds for the retained source basis. In raw or scaled coordinates the tensor decoding metric must be included. These are scope clarifications, not changes to the checked equations or numbers.

The first two items repair a present-day normalization and a signed convention. No material numerical error was found in the new experiment. Gaussianity remains an explicit additional working assumption for the printed tails; the retained H03 carrier establishes a fixed diagonal row-scatter covariance construction, not empirical Gaussianity or a survey-calibrated null law.

## P1–P11: dimensions, physical maps, and limits

| Item | Independently checked meaning and units | Outcome |
|---|---|---|
| P1 | b has velocity units; H, S, Omega have inverse-time units; r is proper length. Antisymmetry removes n^T Omega n from radial motion. Transverse angular motion has units inverse time. | Correct local first-jet decomposition. It is not yet a finite-redshift optical transfer. |
| P2 | S:S/(6H^2) is dimensionless. The spherical fourth moment gives 2(S:S)/(15H^2)=(4/5)Sigma^2. | Correct shear normalization and directional rms factor. Positive eigenvalue means faster than the mean, not necessarily positive second time derivative. |
| P3 | For observer-to-source n, A is physical acceleration, A/c a rate, sigma and H rates. `d=-A/(cH)` and `T=sigma/H` are dimensionless. | Correct same-congruence local optical coefficient and sign. Endpoint translation instead contributes b/r and must retain its different radial response. |
| P4 | m_W has inverse-length units, Q_W is dimensionless with trace one. All three slope contributions are rates. | Correct without sky symmetry. Clarify theta_phys versus theta_com as above. |
| P5 | D and d0 are km s^-1 Mpc^-1; R is Mpc^-1; b is km s^-1. | Correct reduced mean hypotheses on the delivered summary response, with H/STF means unrestricted. |
| P6 | T, eta and the covariance-whitened residual are dimensionless. | Exact for the unrestricted ball, including eta>=sqrt(T), where the minimum is zero. |
| P7 | Qhat, sigma, r_Q, Hhat, r_H are rates. Sigma is dimensionless and denominator positivity requires 0<=r_H<Hhat. | Correct triangle bounds on one common event. The statistical radius needs an orthonormal tensor coordinate metric. |
| P8 | Ordered eigenvalues and error radius are rates. | Correct Weyl bound. It certifies principal-rate signs, not eigenvector-direction precision near degeneracy. |
| P9 | A0/X is inverse length; 3R is inverse length squared; c^2*3R/H^2, Sigma, beta and Omega_m are dimensionless. | Curvature coefficient, shear coefficient and momentum normalization checked from the metric. Restore sign convention. |
| P10 | a and beta are dimensionless. The stable positive root solves a beta^2+beta-a=0. | Correct conditional speed curve; use a common compatible state and |beta|. |
| P11 | sigma dt, QT, s0 and J are dimensionless. | Correct integrated-deformation relation under fixed leading-order ray direction and isolated-source assumptions. Present-day conversion additionally needs g(t0)=1. |

The optical sign in P3 is consistent with a stationary accelerated congruence: a source along positive acceleration is blueshifted relative to the observer, giving the negative A.n/c contribution. If u has norm -1 and its derivative uses proper length s=c*tau, its geometric acceleration is A/c^2, its geometric shear is sigma/c and its geometric expansion scalar is 3H/c. Stating these conversions keeps the displayed physical rates distinct from geometrized derivatives.

For the magnitude map, at fixed leading-order redshift the luminosity-distance ratio is `(1+q)^-1`, so `delta_mu=-(5/ln10)*ln(1+q)`. Its linear coefficient is `B_mu=-kappa*T`. A design that already places -kappa in its columns estimates T directly. This confirms the need for the R28 correction and the separation of the three recorded coefficient types.

## H03: independent finite response experiment

Input SHA-256: `5d31e2ab4fea682c538c31c15181ae7b07e11efba98b36c66aff6feca88f8326`. The parent binds this retained JSON to commit `0d5ab96bdb55398076629099664c77517ec33bb4` and blob `538caae5212e576232b1c6b270cc084704504624`; this pass independently hashes and calculates from the local JSON. It does not independently reexecute the original 35,970-row producer.

The selected twelve-coordinate covariance is positive definite; its least eigenvalue is 0.003831267441054774 in squared rate units. SVD confirms ranks 3, 3 and 6, hence residual dimensions 9, 9 and 6.

| Restricted dipole mean | T | df | Tail if fixed Gaussian law holds | Smallest whitened mean budget to 95% threshold | tau95 in km s^-1 Mpc^-1 |
|---|---:|---:|---:|---:|---:|
| One bulk vector | 79.9870126913061 | 9 | 1.6257600e-13 | 4.830277386 | 0.496334344 |
| One constant rate dipole | 94.5983167465742 | 9 | 1.9373652e-16 | 5.612898119 | 0.532969213 |
| Bulk plus constant rate dipole | 23.3967205226671 | 6 | 0.000673933420 | 1.288553004 | 0.105211045 |

The independent parameter solutions are b=(-119.1123,57.6779,-263.5932) km/s for the first model and d0=(-0.744599,0.260378,-2.788087) km s^-1 Mpc^-1 for the second. The joint fit gives b=(-272.7109,118.3497,-25.9390) km/s and d0=(1.440035,-0.697740,-2.443996) km s^-1 Mpc^-1. These are parameters of these restricted summary models. The joint fit's substantial change in b is an actual response degeneracy/tradeoff, not an independently measured change in the underlying physical bulk flow.

### Why the delivered R and covariance treatment are appropriate

For a window define the complete nine-column row design

`F_i=d_i*(1,n_i^T,STF(n_i)^T)` and its WLS left inverse `L_w=(F^T W F)^-1 F^T W`.

A bulk input adds N b, where N has rows n_i^T. Its complete coefficient response is `L_w N b`; the requested R_w consists of its three dipole rows. This matrix already accounts for all jointly fitted monopole and STF columns. Recomputing a dipole-only estimator would change the response. The independent finite synthetic check finds a nonzero difference 8.7868e-5 Mpc^-1 between those constructions. This is a check of the algebraic mechanism, not a new CF4 response estimate.

A constant rate dipole adds `d_i*n_i.d0`, exactly three columns of F. Therefore `L_w*(d_i*n_i)=E_D`: dipole response I, other coefficient responses zero. The saved H03 maximum identity residual is 5.55e-16, consistent with that algebra. Finite mask anisotropy does not break this identity in the stated full-rank joint model; an omitted signal outside its columns can still leak into the fitted coefficients.

The twelve-coordinate covariance used by the parent is the **marginal** dipole covariance. This is correct when the remaining 24 mean coordinates are unspecified nuisance means. As an independent check, I fitted all 36 recorded coordinates with the *complete* bulk response, the constant-rate dipole response, and 24 unrestricted monopole/STF mean columns. Profiling those columns reproduces every twelve-coordinate statistic within 5e-13 and every physical-response coefficient within 1.5e-11. Conditioning on the other estimates and substituting a Schur-complement covariance would instead impose a different mean model.

Shared-window correlations materially change the answer. Dropping cross-window blocks gives T=88.5692,108.9351,8.92571 for the three models. In particular the last value is below the six-degree 95% threshold, whereas the correct shared-covariance value 23.3967 is above it. Full covariance is therefore essential to the combined response comparison.

The Gaussian statement is mathematically exact only if the stated mean and fixed covariance are the actual Gaussian sampling law. The same calculation remains a deterministic quadratic diagnostic without Gaussianity; a covariance matrix alone does not establish these tail probabilities. Adding tau^2 I refers to the *twelve summary-coordinate covariance*, not to galaxy scatter, a newly measured systematic, or a physical acceleration covariance.

### Exact mean-error frontier

With any whitening W satisfying W C W^T=I, let r=(I-P)Wy. For eta<=||r||, the allowed discrepancy `e=W^-1*(eta*r/||r||)` attains `(||r||-eta)^2`; for eta>=||r||, take e=W^-1*r. This supplies the equality and proves feasibility for the declared ball. The independent check constructs each eta95 discrepancy and refits, reaching the specified chi-square cutoff to numerical precision. A physically restricted discrepancy e=J alpha may not contain that direction. In that case P6 gives an optimistic lower limit on the required budget until its response image is checked.

## Metric-level LRS V check and CMB scope

The supplied monograph's metric is `-c^2 dt^2+X^2 dz^2+Y^2 exp(-2A0 z)(dx^2+dy^2)`. Its actual source uses A0>0. At fixed time r=Xz, the spatial metric is `dr^2+Y^2 exp(-2kr)(dx^2+dy^2)` with k=A0/X. The nonzero spatial connections include Gamma^r_xx=Gamma^r_yy=k Y^2 exp(-2kr) and Gamma^x_rx=Gamma^y_ry=-k. Direct contraction gives Ric_rr=-2k^2, Ric_xx=Ric_yy=-2k^2 g_xx and `3R=-6k^2`.

For the four-metric, the off-diagonal Einstein component equals `G_0z=R_0z=-2A0(HX-HY)=-6A0*s`. A perfect fluid moving at signed speed c*beta along +z has `T_0z=-c*X*(epsilon+p)*gamma^2*beta`. Einstein's equation therefore gives

`6(A0/X)(s/c)=(8*pi*G/c^4)*(epsilon+p)*gamma^2*beta`.

Using `K=(c*A0/(X*H))^2` and `Omega_m=8*pi*G*epsilon/(3*c^2*H^2)` gives P9 with its factor two. These derivations are supported by exact rational connection contractions in two independent parameter cases, including a negative HX case. SymPy was unavailable, so no symbolic-CAS execution is claimed. The stable root was checked over a from 1e-12 to 1e5; the normalized polynomial residual stayed below 3.17e-16.

Omega_m here uses **rest-frame fluid energy**, normalized with the normal-frame Hubble rate. It is not the full energy seen by the normal. For this single-fluid branch that normal energy contributes `Omega_m*((1+w)*gamma^2-w)` to the Hamiltonian sum. With a cosmological constant and no other matter, its compatible state condition is `1=K+Sigma^2+Omega_m*((1+w)*gamma^2-w)+Omega_Lambda`. Thus taking independent ceilings/floors in P10 is a valid conservative implication for a nonempty joint family, while it does not itself establish that every selected bound combination is realizable.

P11 is an integrated deformation because photon energy accumulates shear along the entire ray. A time profile with zero integral can have nonzero present-day shear; for example, on a unit duration interval a fixed-frame profile proportional to cos(2*pi*t) has zero integral and a nonzero endpoint. This explains why a quadrupole amplitude cannot by itself supply an instantaneous shear ceiling. A fixed-direction tensor integral also needs its stated ray approximation; spatially curved models can require the full direction/transport kernel even in an isotropic background. The parent's explicit source-isolation, propagation and cancellation qualifications preserve this scope.

## R28 source-bound units and the distinct 274-row model

The retained E1 source has SHA-256 `843b19e464817d14455df68e9043a93cc71cc7449ab339052c3ddfe1c7298c19`, exactly matching `source_inputs.e1_design.sha256` in the R28 quotient result. Direct source reading confirms `register('shear',-KAPPA*response)`, the explicit `shear is dimensionless` declaration, and the basis tensor `diag(1,1,-2)/sqrt(6)`. The R28 consumer takes those columns without additional scaling and decodes with the same basis. Independent decoding of the repaired exact-factor result gives the recorded 3x3 tensor to below 1e-16.

Consequently b is dimensionless, K and M7 have inverse-magnitude units, and Gamma7 has squared-magnitude units. The reported source labels b as magnitude, M as dimensionless, and the inverse Fisher as squared magnitude are inconsistent with this sealed producer chain. Correcting those labels while retaining the numerical arrays is the smallest repair. Reversing the second basis tensor without changing its coordinate would change the tensor; use the actual source basis and stored decoded tensor.

The independently recovered norm is 0.03265680189321492, directional rms 0.011924578035260817, and conditional Sigma=0.013332083544922036 if this apparent coefficient is physically sigma/H. These numbers require **no second factor -ln(10)/5**. That factor would wrongly convert an already dimensionless apparent-rate coefficient again.

The older P1 likelihood is explicitly distinct: its 274 magnitude responses use raw STF columns `n^T E_a n`, and its text says retained coordinates are raw coordinates. Its B coefficients therefore genuinely have magnitude units. The four-window H03 coefficient tensor is a third convention, in km s^-1 Mpc^-1. The R28 correction does not change either of these separate models.

## Actual execution and retained evidence

Successful command, exit 0:

```bash
python HTT_PHYSICAL_20261025/research/independent_physical_check.py > HTT_PHYSICAL_20261025/research/independent_physical_check_result.json
```

The final script checked the three actual-data fits, fixed-Gaussian residual dimensions, eta/tau frontiers, 36D nuisance profiling, cross-window sensitivity, complete-design response identities, the nonisotropic estimator slope, angular fourth moments, norm/eigenvalue bounds, rational metric contractions, the stable tilt root, and the source-bound R28 basis/units chain. The weighted slope residual was 2.54e-15; the largest sphere-moment error was 4.44e-16; 100 norm/eigenvalue cases had no violation. These finite numerical checks supplement the derivations rather than replace their assumptions.

Two initial invocations exited 1 before scientific execution because SymPy was missing in both the default and primary Python environments. The optional CAS dependency was removed; the metric check now uses explicit exact rational contractions. This was a diagnosed implementation repair, not a relaxed scientific tolerance.

`skill_context_used`: physmath-research-loop 1.3.0 `SKILL.md`, `references/POLICY_INTEGRATION.md`, `references/SUBAGENT_MODE.md`, and the R6 definition in `references/THEORY_LOOP.md`, all actually read through `skills.read` from package `c38/physmath-research-loop`. This pass applies the requested finite review boundary, typed numerical/source identity, explicit dimensions/conventions, evidence-specific corrections, and no recursive review. Parent integration owns the small derivation edits and final interpretation.
