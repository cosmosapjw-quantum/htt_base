# R62 independent final scientific and code review

Date: 2026-11-17 UTC. Reviewer: `/root/r62_final_review`. Requested agent runtime: `gpt-6-astra / xhigh`; observed model and effort: **UNKNOWN**. No observed runtime receipt was supplied, and the requested profile is not treated as observed identity.

Baseline: `c118982e56ee50d68dd0446aa10f16ffe65bd02b`; existing branch `research/r62-anisotropy-classification-20261117`. Read-only review on authorized device `edd1b263-56a0-4391-8a2a-677dd00eabf5`, checkout `/home/cosmosapjw/Dropbox/bianchi/htt_base`. No remote production writes, checkout changes, nested agents, or broad scientific reruns.

## Verdict

**PASS for publication to the scoped research branch.** The tensor-classification mathematics, scoped CF4 conclusions, source-response distinction, and conditional Bianchi results pass this review. One material physical-unit constraint defect, R62-FR-01, was independently reproduced and **closed after the targeted repair**. No current blocking finding remains. The scientific manuscript remains **NOT_READY_TO_SUBMIT** for the stated reasons already retained in the paper plan; a research-branch release is a different decision.

This is one fresh-context final pass and its one bounded repair closeout. The final reviewed BASS state source has SHA-256 `e36dd616f4d0e2998e48e1a50ae9b67e1cd48842ef5b52ee2b1e4b94b888fe04`. Another review tree or repeat classification campaign is unnecessary.

## Scope and inspected evidence

I read the candidate tensor implementation, four original R62 scripts, changed BASS code and diff, R62 tests, REPORT_KO.md, THEORY.md, DESIGN.md, RESEARCH_PLAN_KO.md, source/derivation/history notes, Wolfram receipt, test/execution receipts, and all 42 saved classification records. The bounded inherited SN reuse was then inspected and independently checked. Input SHA-256 values, exact read-only calculation commands, observed numerical runtime, and per-record identities are in the companion JSON.

The review uses PhysMath Research Loop **1.3.0**, its integrated finite-review policy and R6/R9/C9/C10 contracts; mathbox computation-audit and numerical/coverage checklist; root and BASS AGENTS; and the repository scientific-audit/reviewer skills. Separate reviewer views were covered within this single pass. No descendant reviewer was created.

The unfinished additive DAG metadata, all historical PR diffs, raw catalogue reconstruction, empirical covariance calibration, full optimizer replay, full R61 solver audit, and manuscript build/layout were outside this review.

## Minimal publishable claim

For each declared fixed Gaussian tensor carrier, every tested structured class has an explicit feasible state inside that carrier's 95% joint confidence ellipsoid. The classes share one confidence event within that carrier; the 42 carriers and seven nuisance treatments are not independent repetitions and do not jointly acquire a 95% coverage guarantee.

An actual-operator, noise-free construction demonstrates that a common-frame source can yield noncommuting apparent-window tensors. The exact common-offset quotient and covariance transport correctly isolate the specified calibration freedom. Conditional Bianchi compatibility is a subsequent inference requiring an admitted normal-frame physical response, source assumptions, and, for generic action classification, sufficient connection or curvature-derivative information.

These claims are useful and supported. They do not establish a Bianchi family, physical shear history, tilt, cosmic rotation, posterior class probability, or calibrated nonlinear Wilks significance.

## Resolved finding R62-FR-01

**Original severity HIGH; initial priority BLOCK_NOW; final status CLOSED.** The following counterexample records the defect in the pre-repair candidate; it is not a live defect in the reviewed final code.

Object: `htt/bass/background/tilted_bianchi_state.py`, the new actual-range guard, its interaction with absolute equation-scale floors, and the newly documented direct physical-unit usage.

The pre-repair guard compared the residual of `-kappa*q` with `tol*max(1, norm(kappa*q))`. The dimensional constant 1 permits a change of unit scale or small physical Einstein coupling to hide a source outside an exactly zero momentum range. The pre-repair physical-unit docstring explicitly invited `kappa=8*pi*G/c^4`.

A read-only calculation on process **1584067** reproduced:

```python
source = SpeciesFluidCongruence(
    species="cdm", eps_hat=1., p_hat=0., v_vec=[.1, 0., 0.])
construct_admissible_tilted_state(
    family="I", species=[source], kappa=8*np.pi*G/c**4)
```

At `kappa=1`, the constructor raises `CodazziProjectionError`. At `kappa=2.0766474428449717e-43`, it instead returns `is_admissible=True`, `H=2.6442539462271684e-22`, `q=(0.10101010101010102,0,0)`, `D=0`, and Codazzi residual `2.0976236796413858e-44`. A single uncompensated Type-I dust tilt is forbidden by the momentum equation regardless of the nonzero coupling. This is a concrete regression relative to the former family guard's comparison before multiplication by kappa. CF4 likelihood/class results are unaffected.

The required constructive repair was:

1. Test the source's component outside the actual momentum range with a dimensionless/source-relative criterion independent of overall kappa. A scale derived from the sum of species momentum norms can retain tolerance for compensating flows.
2. If direct physical-unit input remains supported, use declared relative physical equation scales for Jacobi, dual Ricci, Hamiltonian, Codazzi, and shear checks; retain raw residuals and expose normalization. Otherwise explicitly require a nondimensionalized input chart and remove the unqualified direct-SI certification claim.
3. Verify uncompensated Type I rejects at both couplings; compensation remains accepted; a unit-equivalent IX example remains accepted; deliberately wrong small-scale Hamiltonian and Codazzi states fail. Run only the affected regression paths.
4. Record the repaired source identity and close this same finding. No CF4 refit or nonlinear classification rerun is needed.

Root implemented this repair. The source-range check now works on q before multiplication by kappa and scales with the sum of species momentum norms. Jacobi, Ricci, Hamiltonian, Codazzi and shear checks expose dimensionally matched scales and normalized residuals; raw fields are retained. Positive finite kappa and tolerance are checked. The physical translation now recommends an explicit nondimensional length/energy-density chart.

Independent targeted process **1600223** checked the actual repaired source:

- The original Type-I single-tilt counterexample rejects at kappa=1, 2.0766474428449717e-43 and 1e30, while compensated two-fluid states remain accepted.
- Doubling H gives the same normalized Hamiltonian error 0.6 and is rejected in every coupling chart.
- The valid IX tuple remains accepted at (L,E)=(1,1), (1e-22,1), (1e12,1e5), with largest normalized residual <=8.89e-17. A 10% shear perturbation is rejected in all three charts.
- The 14 new unit-regression cases and repair diff were inspected. The parent's targeted affected suite reports **100 passed, exit0**; its log hash matches the receipt and repaired source hash. No duplicate pytest sweep was run by this reviewer.

The repaired inputs were unchanged during the independent closure calculation. **R62-FR-01 is closed; no second current blocker was identified.**

## Scientific and numerical checks

| Object | Independent evidence | Result |
|---|---|---|
| Saved carrier population | Iterated every declared receipt and all five classes; checked hashes, means, covariance marginals and contrasts | 42 carriers, 210 class queries, 616 recorded enclosures |
| Structured witnesses | Independently reconstructed 3x3 tensors from saved frame/axis/shape and amplitudes; recomputed SPD objectives | All 168 structured states intersect; largest q/cutoff = 0.4462169159808548 |
| Witness precision | Compared independently recomputed objective and tensor reconstruction | Maximum objective difference 2.31e-14; tensor-entry difference 2.43e-17; class commutator norm 2.17e-18 |
| Source Gaussian fits | Independent QR on saved whitened 32D designs, with no production fitting routine | All fourteen J2/J3 fits have ranks 21/26; scaled mean/covariance differences <= 6.11e-14 / 7.29e-13 |
| Zero hypotheses | Recomputed stored zero-state distances | 16 exclusions and 26 intersections across all 42; nuisance-union zero remains |
| IX initial slice | Reconstructed dust independently and called candidate constructor at geometric H=kappa=1 | beta3=-0.02004008016032064; Gauss residual8.88e-16, Codazzi2.78e-17 |
| Exceptional VI_h | Rechecked actual momentum rank at h=-.12,-1/9,-.10 | 3,2,3 |
| Existing affected tests | Read command, exit receipt and matching hashed log | Initial author run: 113 passed; not independently rerun as a duplicate suite |
| Repair affected tests | Read new regressions, patch, current source binding and matching log hash | Targeted author run: 100 passed, overlapping prior tests; independent counterexample closure performed separately |

The independent core computation ran on Python3.12.3, NumPy2.5.4, SciPy1.18.1, one BLAS thread, remote process1580059. Its inspected inputs were unchanged during that computation. The numerical values above are finite binary64 checks, not formal exact-arithmetic certification.

The Bianchi signs agree with the stated bracket and normal-frame q=T^{0i} convention: D+kappa*q=0. Class-A ranks depend on n eigenvalue gaps. The Class-B 2x2 minor vanishes at n2*n3=-9a^2. The physical velocity moment differential is 2[v,(n_hat)v,(n_hat)^2v]^T; its rank depends on occupied eigenspaces, unlike the squared-component Vandermonde rank. Stabilizer azimuth is correctly distinguished from a physical orbit degeneracy.

For untilted V, sigma*a=0 and det(sigma)=0 have the claimed momentum-only scope. For geodesic homogeneous normals, Fermi frame and pi_N=0, the I/V tracefree spatial curvature vanishes and shear has the fixed-shape history sigma=b^-3*S. The reconstruction of intrinsic Ricci restores c consistently when H and sigma use inverse seconds and density/stress are energy per volume. The physical observation-to-shear map remains absent, as explicitly reported. The legacy opposite-sign constraints path is preserved as known migration debt; this release must not claim that path was repaired.

The saved first classification failure is an implementation exception before class outputs. Attempt2 has a different corrected script hash and completed successfully. It is neither an unresolved live script error nor evidence against the scientific classes.

## Inherited SN reuse

The added reuse script preserves the qualified R36 source/status identities and the full cross-bin covariance. Independent process1587074 verified all four marginal/contrast means, covariance transport and zero distances:

| Sample | Carrier | q0 | Nominal p0 |
|---|---|---:|---:|
| Primary490 rows | STF10 | 10.156783041928293 | .42684760863763516 |
| Primary490 rows | DifferenceSTF5 | 2.9291930979243532 | .7109013290043967 |
| Lower-z sensitivity705 rows | STF10 | 6.925298018162785 | .732477961463922 |
| Lower-z sensitivity705 rows | DifferenceSTF5 | 2.2286833677864184 | .8166821878568882 |

Zero is inside every ellipsoid, so its explicit witness is sufficient for every structured-class intersection. A one-tensor common-frame restriction is vacuous and is correctly marked. Magnitude units, unknown physical sky/boost response, shared peculiar-velocity law, and empirical coverage remain unresolved. This is a conditional inherited comparator; it is not an independent physical-frame match or a CF4/SN joint likelihood.

## Novelty, source checks and readiness

I independently opened [Hewitt–Bridson–Wainwright, AppendixA](https://arxiv.org/pdf/gr-qc/0008037), including the general normal-frame equations before the II specialization; [Ferrando–Sáez2020, Theorem7](https://arxiv.org/pdf/2004.01877), with its algebraically general/maximal-G3 and derivative-concomitant conditions; and [Kwidzinski–Piechocki2019, SectionII](https://arxiv.org/pdf/1901.01790), supporting the established general tilted-dust IX setting. The candidate's corresponding source boundaries are appropriate.

GLS, variable projection, simultaneous diagonalization, confidence-set inversion and intrinsic Bianchi classification are established mathematics. The contribution demonstrated here is the covariance-preserving observational implementation, explicit operator counterexample, bounded historical reuse and project-level physical bug correction. These justify an inspectable research result. They do not yet establish a standalone methods paper's novelty or a new geometric theorem.

No additional downclaim is needed for the current CF4/SN reports. No stronger Bianchi detection claim is admitted. Manuscript readiness still requires the explicitly limited observable interpretation or an actual physical response, adequate covariance/calibration justification, exact comparison with standard methods, and independent scientific reproducibility at the paper's chosen claim level. Those are manuscript obligations already acknowledged in the plan, not new gates on this scoped research branch.

## Merge/release decision and next action

**The scoped results and repaired code may be published to the authorized research branch.** R62-FR-01 is closed against the final source identity above, with no remaining current blocker. Preserve journal status NOT_READY_TO_SUBMIT, original science-gate statuses, archived failures and all physical-response limitations. This review is complete; no further audit loop or optional rerun is requested.
