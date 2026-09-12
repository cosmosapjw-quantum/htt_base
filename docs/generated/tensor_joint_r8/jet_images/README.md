# Unit D — conditional jet-set images, resumed execution

The interrupted `R8-D-20260910` work unit resumes from `ea0305fa9e5f23e4d22a40ab826155202e76b574` in the existing R8 worktree. It now implements and executes the declared ellipsoid/remainder image, shared-state set composition, target-specific outer projections and fixed-grid sensitivity frontier. **The direct implementation delivery is complete. Independent P/J four-axis acceptance and empirical physical confidence remain unfulfilled; full R8 remains incomplete.**

Owner: `htt` (`common` owns the jet-set map). Scope: deterministic mathematical fixtures and conditional methods, claim tier C0, transfer source none. The mock6 identity map is not a physically realized radiation history, a covariance, or an observed confidence region. Scientific source: the unchanged R8 SCIENTIFIC_CONTRACT items 1, 6–10, THEORY J1/P1/P2 and VALIDATION_MATRIX V05/V07/V08/mock6. P1's geodesic, collisionless, first-order-about-FLRW premises are retained. The referenced [Maartens–Gebbie–Ellis paper](https://arxiv.org/html/astro-ph/9808163v2) was consulted for the distinction between nonlinear hierarchy and FLRW linearization; this execution does not rederive the full hierarchy.

## Implemented behavior

- `p1_operator(Theta)` gives the 8-by-24 outward normalized derivative map for `(S,W)=(sigma/Theta,omega/Theta)` in orthonormal STF5 and antisymmetric3 coordinates. Inputs include the derivative of normalized temperature, not just the derivative of its numerator. The user of a physical map must supply the same expansion, event/frame and admitted premises to the domain.
- `jet_image` retains `K j0`, `K L`, deterministic radius, expansion and both rate remainder balls. `support` encloses the signed P2 support with exact rational arithmetic and outward 256-bit square-root brackets. `normalize=True` encloses the exact normalized direction, including the irrational all-ones direction; no rounded unit vector is substituted.
- `outer_region` intersects candidate-state acceptances within each supplied compatible tuple and unions alternative tuples. Missing scopes remain the whole domain and retain their fixed alpha allocation. The production integrated allocation is four times 1/80; shared nuisance values are passed unchanged to every acceptance. Compatibility and real marginal coverage remain caller-supplied scientific premises, not facts established by the `PhysicalRegion` type.
- `project` returns signed linear support intervals and conservative `s2=S:S/2`, `w2=W:W/2` bounds from the same joint set. It retains unresolved candidates in a domain-box outer relaxation. The existing exact affine-ratio/positive-denominator implementation is reused on its actual supported domain. Other nonlinear targets and uncertain expansion return an unresolved outer result.
- `recession_certificate` verifies an actual feasible affine local ray, unchanged observation and nonzero target slope. A compact coordinate constraint removes the supplied witness. This proves only a statement inside that local affine domain.
- `closure_frontier` brackets a declared target crossing on the fixed rho grid. It requires the same center, factor, map, expansion and remainder domain at every query. A changed family or mismatched radius is refused; a general nonlinear family without a nesting proof is unresolved.

## Executed results

[results.json](execution_20260912/results.json) binds all executed source files and configuration; [execution.json](execution_20260912/execution.json) records the invocation and timing. The fixed mock6 uses `K=I8`, `j0=0`, `L=diag(1,2,1,2,1,2,1,2)`, Theta=3, rho=0, 1/4, 1/2, 1, 2, 4, and remainder rate radii (0,0) and (3/10,3/5). Its seed label is 81010, but it makes no random draws.

All **204 finite support queries** (12 cases, each with 16 signed coordinates and the normalized all-ones direction) enclose the separate 110-digit Decimal reference. All **34 unrestricted-radius queries** return unbounded support. The zero-center, zero-radius case with nonzero remainders retains S-coordinate extent 1/10 and W-coordinate extent 1/5, rather than returning the center alone. The norm-squared outer bounds there are 1/200 and 1/50 respectively.

Four generated frontier records bracket the crossing of coordinate value 1. The fixed grid gives S1 brackets [1/2,1] and W1 brackets [1/4,1/2] for both remainder families. These are conservative grid brackets, not fitted radii or posterior intervals. Both [PNG](execution_20260912/jet_support_frontiers.png) and [PDF](execution_20260912/jet_support_frontiers.pdf) were opened as rendered images; labels and plotted values agree with the saved records.

The illustrative set-composition and affine-ratio fixtures exercise the actual APIs. They are not observed laws. No CMB candidate-state radiation jet, physical distance-to-jet map, same-state tilt/curvature contribution, or F/G_F denominator/depth domain is supplied. Therefore `x_C`, `F`, `G_F` remain `OUTER_RANGE_UNRESOLVED`, and empirical physical confidence remains `INPUT_UNAVAILABLE`. No old scalar bound or DESI qiso interval is substituted as a physical jet constraint. The historical qiso result and all R7/R8 failed or incomplete outcomes remain unchanged.

## Validation and direct review

Original missing-module RED and interrupted 5-pass/1-fail GREEN logs are preserved in `.agent-harness/runs/R8-D-20260910/raw_logs/`. The resumed RED records five failures: float/Fraction coverage-view mismatch (two tests), missing half-contraction normalization (two), and failure to refuse a changed frontier family. Fixes preserve the declared thresholds and old tests. New tests cover signed normalized support, several expansion values, shared nuisance consistency, positive/zero denominators and feasible-ray restrictions.

The selected D and dependent R7 tests passed **21/21**. The final R8 suite plus those R7 regressions passed **70/70 in 3.45 s**:

```bash
PYTHONPATH="$PWD/htt/htt:$PWD/htt/src:$PWD/htt:$PWD" PYTHONDONTWRITEBYTECODE=1 \
/mnt/sn850x2t/htt_base_e2e/venvs/htt_base-py312-20260829/bin/python -B -m pytest \
  -o addopts='' --import-mode=importlib tests/r8 \
  tests/r7/test_mes_region.py tests/r7/test_joint_experiment.py -q
```

The staged whitespace check reports two trailing-space lines emitted by pytest in the preserved failed-run transcript; those raw bytes are retained. Authored code and documentation pass the whitespace check. The existing canonical DAG validates (194 PRs); PR-247 remains in progress and its mirrored status is unchanged. No full-repository test claim is made, and no unchanged R7 Gaussian campaign or A/B/E numerical run was repeated.

Direct engine records are in `.agent-harness/runs/R8-D-20260910/artifacts/direct_execution/engine_results.json`. Wolfram 15.0+xAct, SymPy 1.14 and pinned Lean 4.31.0/mathlib pass their **limited supporting algebra** checks: P1 coordinate normalization, mock6 squared norms, J1 pointwise set logic/alpha arithmetic and the supplied V08 ray. The initial Lean vector-simplification failure is preserved; the unchanged proposition compiles after replacing that closed rational reduction with `decide`, with no `sorryAx` in the successful axioms output.

Sage/Singular is **BLOCKED / NOT EVALUATED**: importing the installed Sage started a Ninja/Meson rebuild in `/home/cosmosapjw/opt/sage/build/sage-distro` and exceeded the predeclared 180 s limit before algebra executed. Its raw timeout is retained, and the observed build children were absent afterward. No environment installation, pin substitution or additional Sage attempt was made. The direct check brief is not an independently registered CAS contract or an aggregate CAS admission. Generic probability coverage, a full P2 formalization and independent four-axis acceptance are not claimed by these supporting checks.

Host reviewed correctness, regressions, test adequacy, claim scope and maintainability against the frozen D1–D4 criteria. This is direct self-review under the owner's request to avoid subagents, not an independent reviewer. The concrete normalization and family-identity defects have regression coverage; unresolved scientific inputs remain typed. The claim firewall and x/Q/Pi/F/G distinctions were checked. Residual limits are explicit domain/coverage premises, conservative Frobenius/box relaxations, unsupported nonlinear outer optimization, and the independent CAS ceiling. No new solver, posterior, family identification or scientific promotion is issued.

## Reproduction and continuation

Execute a new changed-source attempt with:

```bash
PYTHONDONTWRITEBYTECODE=1 \
/mnt/sn850x2t/htt_base_e2e/venvs/htt_base-py312-20260829/bin/python -B \
  scripts/observed_runs/run_r8_jet_images.py --run-dir <new-directory>
```

The producer refuses an existing output directory. The saved successful results are sufficient for review; the original failures remain separate. The direct engine runner supports `--axis lean` and other single-axis selections so successful unchanged engines are not rerun. Its nonzero aggregate exit persists while Sage is blocked.

This closes the existing Unit D direct-delivery acceptance only. Its frozen scope excludes restricted-provider dynamics and final campaign wiring. Unit F and full G implementation/synthesis, plus the documented A/C and independent B/D acceptance limitations, remain follow-up work under the original R8 plan.
