# HTT Library reuse notes — 2026-11-15

Scope: targeted retrieval and semantic review of the cited sections. This is not an exhaustive read of all Library or historical Git blobs. No repository mutation or observational execution was performed by this worker. Personal Context returned `Personal context is unavailable for this conversation.` November R47–49 Library searches did not recover relevant HTT documents; unrelated CIC/WU results were excluded.

## Verified current Library sources and sections

| File | Library ID | Read/review scope |
|---|---|---|
| HTT_METHOD_FOUNDATIONS_20261028.pdf | libfile_fa84f71e4fdc8191969c868b7b68e18d | Five-object definitions pp2–9; saved Gaia-law analysis pp10–16 |
| HTT_FIVE_THEORY_LOOPS.pdf | libfile_5f95d8ab5b248191a69d06386797aab5 | Introduction, five-loop result table, convention and semantics |
| HTT_INTEGRATED_V15.pdf | libfile_b63fbeed9f3c8191bb91e5300fa4220e | v15 integration and explicit new results, opening sections |
| REPORT_KO(20260929-224437).md | libfile_63608c37cc748191b88d9cca917c1252 | Tilt/frame theorem text, Sections 1–8 |
| HTT_MES_AND_OBSERVED_LINEAGE_AUDIT_R5_KO_20260908.pdf | libfile_679a5c7774f481919c803921013218c4 | Coverage statement; tensorized MES operator/response audit, pp2–5 |
| TASK_GRAPH.json | libfile_4a017d02f69c8191b814230c2bd7b1ae | READ-ALL and DATA-01..03 contracts; search excerpts DATA-06..07 |

## Five-object semantics that must not drift

The October 28 foundation explicitly defines one constructive version, not a claim that all historical versions shared meanings:

- x: response-sufficient signed joint carrier T(Y), with covariance/full law.
- Q: gauge p_K0(theta)=inf{r>0:theta in r K0} relative to declared physical body.
- F_alpha(v;Y): directional support utilization h_Theta_alpha(Y)(v)/h_K0(v), v nonzero.
- Pi: P[Q(theta)>epsilon | Y,M], or a separately named calibrated tail. A continuous-prior P(theta!=0)=1 is uninformative.
- G_F: declared depth contrast or transport map on the joint carrier, preserving complete cross-depth law. For fixed D, covariance is D C_x D^T.

These are five views of one inference; they are not five independent observations or likelihood factors and do not generate additional Fisher information. Historical Fsup, Fcert=x_C/U and F_nu (actual occupancy measure) have different semantics and must retain distinct definition IDs.

Physical target theta_kin=(Sigma/H, Omega/H, A/(cH), beta_RM), with physical rates Sigma,Omega,H in s^-1 and proper acceleration A in m s^-2. Observer beta_MO belongs to the observation model. MES coordinate x_kin=(Sigma/(3 H Bsigma), sqrt(2) Omega/(3 H Bomega), A/(c H a*), beta_RM/b*). The sqrt(2) is the full antisymmetric tensor versus axial-vector norm conversion. No MES authority is claimed for arbitrary a*, b*. A=0 in geodesic dust is a domain restriction, not a measurement or division by a zero radius.

## Concrete prior results to reuse

1. Radiation: L_I S=(8 rho/15)S+(10/7)STF(S pi)-H4:S. In the declared geodesic, irrotational, collisionless branch, L_I Sigma=-R_tau, R_tau=partial_tau pi+4H pi+(2c/5)D_<a q_b>+c D^d H_abd. It uses brightness ranks 0,2,4; residual requires differentiated ranks 1,2,3. A single sky can supply the operator without the residual. For fixed invertible L_I and residual set R, exact feasible shear set is -L_I^-1 R and support h_S(v)=h_R(-L_I^-T v).
2. Angular calculus v15: matching energy moments through L=4 preserves that shear operator exactly. With delta=1-<w^(3/4)>, w=4pi I/rho, ||L_I-(8rho/15)Id||_op <= rho sqrt(8delta/3). A sufficient inverse condition is delta<8/75. These are prior conditional theory results, not newly fitted shear constraints.
3. Exact Gaussian common-family compression requires both mean-response columns and model offsets. Preserve all in whitened nuisance-free union span; retain q_perp for adequacy and possibly residual orientation for later model attribution. Covariance-dependent models require quadratic forms, not only mean-score spans.
4. Saved Gaia INFO-01: 755,850 selected rows; old 102-column nuisance design; six added g(z)=z/(1+z) slopes. 24D carrier=(three E1/B1 six-vector bin intercepts, one six-vector slope); not E2 shear. Profile information trace retention 0.01584852677360534. Saved working statistic 12.1402056890 and tail 0.0589130888 are conditional summaries. A 24->18 bin-centre map exactly erases within-bin slope information when each bin intercept is unrestricted nuisance. Joint GLS equals matched invertible tensor coordinates (max parameter discrepancy 2.42e-13). For g versus g^2 response families, each rank6 but union rank12. Saved full/common-carrier deviance difference -67.77514657; projection onto one family's score makes both models fit exactly and erases comparison to zero. Do not present this repeat as new novelty.
5. Stronger retained R36-03 E2/STF5 carrier extracted from 102D Gram has positive rank5 after nuisance profiling. Bianchi-I weak-history response A_PM=2c(B_o-B_s)/D-dot B_o. At a common distance it measures five combinations of ten history/current-shear components, kernel delta s=k delta q_hist. A correct signed carrier does not resolve this physical kernel.

## Tilt and local boost lineage

September 30 report distinguishes N homogeneous normal, U chosen species matter flow, O observer, R radiation frame. Output uses joint (eta_UN,eta_OU), with eta_OR separate; 3-velocities from different rest spaces cannot simply be subtracted. Source intercept Z(n)=lim_(d_A->0)(1+z)=zeta0+zeta.n gives beta_U/O=zeta/zeta0 under explicit smooth-congruence/extrapolation assumptions. Hubble quadratic-form eigenframe reconstruction requires geodesicity and a unique timelike eigenline; vorticity is absent from the symmetric null contraction. Cosmological tilt U/N further needs geometric normal information (curvature scalar clock or Codazzi plus matter assumptions). Bianchi-I total momentum constraint J=0 excludes single-perfect-fluid tilt when enthalpy is nonzero, but not multi-fluid counterflows. The boost-invariant distance combination is (1+z)d_A=d_L/(1+z) on the same ray under reciprocity; it controls observer boost but is not by itself a global-tilt detector.

## Owned-data catalog and pitfalls

The September 29 TASK_GRAPH identifies 52 owned products through:
- dl_pipeline/assets/obs_meta/INDEX.json
- dl_pipeline/assets/obs_meta/obs_loader.py
- scripts/inventory_observational_data.py
- htt/src/common/data_contracts.py

DATA-03 plans owned NSIDE16 I/Q/U maps, Commander/SMICA as same-sky alternate reductions, temperature ell=2..5 complete 32-component carrier. Actual map/mask/beam/pixel ordering and downsampling provenance are needed. DATA-02 retains asymmetric Planck errors, ACT SACC row/tracer identity plus original full covariance/windows if present, and release-specific SPT/BK alignment. Diagonal exports cannot restore missing covariance; C_l does not recover a_lm morphology; SPT792-vs39 mismatch is an explicit failure fixture. CF4 reconstruction-query products must not become independent raw-galaxy likelihood rows.

The historic READ-ALL gate required every source line before analysis, but the current user requests convergence and actual executable units. Preserve inventory and honest read coverage; targeted input/consumer review can proceed without claiming all-history semantic completion. September R5 audit itself reports only 265 fully read unique blobs out of 18,885 historical blobs (182 branch refs, 2,061 commits, 2,003 root trees). An indexed or fetched history is not a full-read claim.
