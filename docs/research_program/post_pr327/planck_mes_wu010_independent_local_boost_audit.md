# PMG-WU-010 independent local-boost audit and frozen-candidate closeout

## Authority and scope

- repository: `cosmosapjw-quantum/htt_base`
- draft PR: `#442`
- scientific base: PR #441 head `04680e99d56b9974fe1120854370af1fb94fb1d6`
- reviewed implementation candidate: `8a59ee1126b9eccdaa6fecb14de442e8c68b988d`
- branch: `changeset/planck-mes-wu010-local-boost-adapter-20260901`
- conventions: metric `(-,+,+,+)`, outward sky direction `n=-e`, active observer boost `+beta`, dimensionless `beta=v/c`, and thermodynamic blackbody temperature with Doppler weight `d=1`

This document-only closeout does not change production or test equations. The branch head containing this file is recorded externally in the PR, Jira BASS-20, and Confluence page 21463041 after exact-head CI readback. The audit is independent formula reproduction, source cross-check, code-path inspection, and exact-head test readback. It is not observed-data execution, Planck absolute-temperature admission, empirical velocity fitting, global matter-frame tilt, a Bianchi-family attribution, or replay of the unavailable P01--P27 formal dossier.

## TDD and bounded-repair record

1. Test-only commit `e57bccf5d2b6913c8ac042d0390a95f2a6b8bcfb` added the direct stored-real harmonic oracle and strict-positive absolute-temperature contracts. The PR04 Python matrix recorded the expected RED collection failures because the new APIs did not exist.
2. Commit `433fffd3acc2f4145fd6fc6858f17e0dc2259ae2` implemented the direct `l=2 -> (l=1,l=3)` stored-real harmonic response matrices.
3. Commit `651171dfd0b00238c7cf6a39fc545208d5a9c6ca` implemented the direction-safe field pullback and strict `T>0` absolute-temperature gate.
4. Characterization then exposed a test-domain mismatch: a signed pure quadrupole was passed into the absolute-temperature API. The implementation was not weakened. The affected tests were repaired by embedding the anisotropy in a positive sky or subtracting an independently boosted positive monopole.
5. Implementation candidate `8a59ee1126b9eccdaa6fecb14de442e8c68b988d` completed the exact harmonic/STF audit closure.

## Exact physical and algebraic contracts

For

```text
p^a = (epsilon/c)(u^a + e^a),       n^a = -e^a,
u_tilde^a = gamma (u^a + beta^a), beta^a = v^a/c,
gamma = (1-beta^2)^(-1/2),
```

the observed photon energy and temperature pullback are

```text
epsilon_tilde = gamma(1+beta.n) epsilon,
T_tilde(n_tilde) = T(n(n_tilde))/[gamma(1-beta.n_tilde)],
dOmega_tilde = D^(-2) dOmega.
```

The exact first-order scalar generator is

```text
delta_beta T = (beta.n)T - [beta-(beta.n)n].grad_S2 T.
```

For `T_Q=Q_ab n^a n^b`,

```text
(B_Q beta)_abc = 3 beta_<a Q_bc>,
delta_beta T_Q = (B_Q beta)_abc n^a n^b n^c - (4/5)(Q beta)_a n^a.
```

With `q2=Q_ab Q^ab`,

```text
M_Q = q2 I + (6/5)Q^2,
B_Q* B_Q = 3 M_Q,
beta_hat = M_Q^(-1)(O:Q),
P_ImB O = B_Q M_Q^(-1)(O:Q),
O_perp = O-P_ImB O,     O_perp:Q=0,
dim (Im B_Q)^perp = 4.
```

The spectral condition number obeys the sharp bound

```text
kappa_2(M_Q) <= 5/3,
```

with equality for spectra proportional to `(-5,4,1)`, up to scale, sign, and permutation.

Dimensions are preserved: `Q`, `O`, and the harmonic coefficients have temperature units; `beta` and `gamma` are dimensionless; `M_Q` has temperature squared; `B_Q beta` has temperature.

## Independent Wolfram checks

Exact symbolic algebra verified

1. `(gamma-1)/beta^2 = gamma^2/(gamma+1)` on `0<beta<1`;
2. all STF3 pair traces of `3 beta_<a Q_bc>` vanish;
3. `(B_Q beta):Q = [q2 I+(6/5)Q^2] beta`;
4. `B_Q^T G_3 B_Q = 3 M_Q` in the registered seven-component STF3 Frobenius metric;
5. the response map has rank three for nonzero `Q`;
6. the response-image projector is idempotent and STF3-metric self-adjoint, with trace three;
7. the direct stored-real dipole and octupole matrices have exact zero residual against an independent composition of the registered `a_2m <-> Q_ab` and `O_abc <-> a_3m` maps.

## Independent numerical and adversarial checks

A deterministic `80 x 160` Gauss--Legendre/uniform-azimuth sphere rule gave

- finite-to-linear field residual slope: `2.000002992637`;
- line-of-sight sign-mutation residual slope: `0.999998309811` and a nonvanishing mutated residual;
- first-order harmonic-power fraction outside `ell=1,3`: `1.419666276311e-31`;
- maximum full-sky `L2` relative drift over `|beta|={1e-3,1e-2,0.1,0.5}`: `5.097042758756e-16`.

These support the scoped full-sky local-observer claim. They do not establish a masked, beam-convolved, filtered, nuisance-projected, or instrument-specific response.

## SciSpace literature cross-check

The implementation boundary agrees with the peer-reviewed CMB aberration/Doppler-kernel literature:

- Dai & Chluba, *Phys. Rev. D* **89**, 123504 (2014), exact operator and recursion treatment of thermodynamic-temperature aberration kernels;
- Yasini & Pierpaoli, *Phys. Rev. D* **96**, 103502 (2017), generalized frequency-dependent kernels and observable-dependent Doppler weights;
- Ferreira & Quartin, *Phys. Rev. D* **104**, 063503 (2021), separate Doppler-modulation and aberration effects with realistic-sky considerations.

No adjacent invariant-theory source is substituted for the still-missing degree-15 proper-rotation chirality polynomial of the full `V_2 direct-sum V_3` representation.

## Exact-head execution readback

For reviewed implementation candidate `8a59ee1126b9eccdaa6fecb14de442e8c68b988d`:

- PR04 theory and integration gates, run `33528105799`: SUCCESS on Python 3.10, 3.11, 3.12, and 3.13;
- PR07 audit-repair gates, run `33528105778`: SUCCESS;
- repository integrity, run `33528105805`: SUCCESS;
- Python 3.12 fast tier: `26 passed, 2 skipped, 6926 deselected`;
- named low-ell regression pair: `46 passed`;
- PR04 theorem/property unit layer: `25 passed`;
- repository contracts, Rust compile, and Python package smoke: SUCCESS.

This is runtime contract evidence, not empirical-data or full-solver validation.

## Fresh PHYS--MATH review

`PASS_WITH_TYPED_LIMITATIONS`

- signs, frame convention, units, dimensions, STF projection, harmonic normalization, zero-boost limit, inverse boost, `ell=1,3` selection rule, and sharp conditioning are mutually consistent;
- the strict-positive absolute-temperature domain is physically correct and fail-closed;
- no global tilt, finite electron-frame collision, polarization, foreground, or Bianchi-source claim is generated by this adapter.

## Fresh PHYS--MATH--CODE review

`PASS_WITH_TYPED_LIMITATIONS`

- the direct harmonic oracle is independent of the Cartesian STF conversion route and closes the principal coefficient-order/sign blind spot;
- RED-to-GREEN history and the later test-domain failure are both preserved;
- exact-head CI is green across the declared matrix;
- the historical fixed-axis `boost_biposh_residual.ExactBoostOperator` is unchanged and is not silently replaced;
- parity with that specialized operator, and the complete cut-sky processed response, remain successor-node requirements rather than hidden WU-010 claims.

Fresh GitHub review `5080263134` registered this disposition against implementation candidate `8a59ee1126b9eccdaa6fecb14de442e8c68b988d`.

## Risk ledger after closeout

- **P0:** none inside the declared WU-010 full-sky local-observer scope.
- **P1:** no processed cut-sky response certificate; no Planck absolute-temperature admission; no empirical nuisance-aware inverse. These block observational use, not the scoped algebraic adapter.
- **P1:** original P01--P27 proof dossier remains unavailable and unreplayed; no formal-proof provenance promotion is allowed.
- **P2:** map-level parity with the historical fixed-axis exact operator belongs to WU-011.
- **P2:** no polarization or frequency-dependent Doppler-weight implementation is admitted.

## Final disposition

`PASS_FRESH_READ_ONLY_REVIEW_WITH_TYPED_LIMITATIONS`

The PMG-WU-010 theory/code node is closed at the scoped full-sky local-observer level. PR #442 remains draft pending owner/release decision. No merge, observed-data execution, or scientific claim promotion is authorized by this audit alone.

## Next admissible DAG

1. Start **PMG-WU-011: processed cut-sky local-boost response**.
2. Compose the finite boost with mask, beam, pixel window, filtering, nuisance projection, and the existing joint cut-sky harmonic estimator.
3. Require full-sky and zero-boost recovery, finite-to-linear convergence, direction-sign mutation kill, mask/beam sensitivity, and parity against the historical fixed-axis `ExactBoostOperator` on its declared domain.
4. Keep empirical `beta`, subtraction, global tilt, Bianchi-family, and polarization claims blocked until matched-null and instrument-response admission.
5. Continue the degree-15 `V_2 direct-sum V_3` invariant/Molien derivation as a separate P0 mathematical node; it is not a silent prerequisite for the existing incomplete morphology family.
