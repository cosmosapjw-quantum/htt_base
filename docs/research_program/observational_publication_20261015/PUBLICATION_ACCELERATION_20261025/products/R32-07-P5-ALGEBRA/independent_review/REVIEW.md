# R32-07-P5-ALGEBRA independent scientific assessment

**Decision: SCOPED_PASS for `bianchi_algebra_note` only.** No unresolved blocking finding remains in the repaired candidate. This assessment is complete; a formal controller review packet and its binding remain pending. It does not constitute a fabricated dispatch, ACK, controller qualification, publication decision, or completion of an original campaign acceptance.

The reviewer is `/root/r35_p5_fresh_independent_review`, independent of the science author `/root/rc_1f2400c98c81ce56`, source framer `/root/r35_p4_p5_source_contract_intake`, and builder `/root/r35_p5_prescribed_numeric_build`. Requested route: `gpt-6-astra/xhigh`. Observed model and effort: `UNKNOWN`. The reviewer made no repository, Git, campaign-state or production-artifact changes and spawned no child. All reviewer outputs are under the directory containing this report.

## Candidate binding

Repository: `/home/cosmosapjw/Dropbox/bianchi/htt_base`. Observed branch: `research/htt-adaptive-methods-20261023`; HEAD: `427f7b5dda53e4cee1f1189ae78fdd0ce494ec1c`. Existing dirty and untracked state was preserved. Product prefix: `docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-07-P5-ALGEBRA/report/`.

| Current candidate object | SHA-256 |
|---|---|
| `RESULT.json` | `018cf0d1f4ab322813da519106f3aa94a80f07e6fb1179362c7151c6c84df3db` |
| `OUTPUT_MANIFEST.json` file | `517850abb322271d6653552c2af5681e0f0ac2ff368c591f02e29eb12fef7f09` |
| `manuscript.pdf` | `427ef5a1fc7786d4c02de70f74afc1d2b86433239c54f303938d09147ae5d0ac` |
| `arrays.npz` | `fda6f716e751c44cf24cff6d96ed70a3f25bb4976f4c068c27864f69ea41d1d9` |

All 38 current manifest entries match their file sizes and hashes. All nine immutable retained-source entries matched. The four science documents were checked by the actual read-only consumer invocation; source notation repair and the nine-versus-ten counting typo are explicitly recorded by the author. Source identity was checked, without rerunning historical metric/CAS work. The manifest-file hash above is not represented as a separately defined canonical embedded-object identity.

## Evidence read

Read `AGENTS.md`, `docs/harness/CURRENT_CODEX_RUNTIME.md`, and the repository physics/math, claim-firewall, manuscript/figure, LaTeX-build, and x/Q/Pi/F/G guidance. These instructions supplied scope and conventions, not a qualification oracle. Read all four `science/` documents, the consumer's numerical and rendering code, generated claim map, arrays, full joint CSV, selected table, inventory, builder receipts, first-failure logs, final compile log, and notation correction record. Read the relevant mathematical sections of retained S1–S4; no previous verdict on this candidate was supplied or used.

The analytic results are assessed from their actual assumptions and proofs. No external literature novelty assessment is made. The source monograph is a secondary locator only; no fresh monograph inspection is claimed.

## Assumptions and conventions

Signature `(-+++)`; proper time; explicit `c`; dimensionless coordinates and positive oriented `A0`; `X,Y>0`; mean normal expansion `H>0`; normal orthonormal axes `(x,y,z)`; signed matter velocity along positive `z`. The Bianchi V sector has exactly one perfect fluid, `0<=w<=1`, nonnegative rest energy and cosmological constant, `0<K<=1`, and `abs(beta)<1`. Rest-frame energy is normalized using normal-frame H and is distinct from normal-observer energy. Negative directional expansion is permitted. The history example instead belongs to a separately declared smooth kinematic Bianchi I class with isotropic initial Planck radiation, collisionless transport, and no added observer or emission terms.

## Equation and definition audit

| Obligation | Assessment and reason |
|---|---|
| Oriented shear–tilt identity | The stated `G_0z` and `T_0z`, normal-energy normalization and curvature definition yield `2 sqrt(K) z_s=(1+w) Omega beta/(1-beta^2)`. Squaring gives the required coefficient `[(1+w)Omega]^2 beta^2/[4K(1-beta^2)^2]`. Signed information is retained separately. |
| Complete instantaneous region | With `A>=0`, `B>0`, `f(Omega)=A Omega^2+B Omega` is strictly increasing on nonnegative rest density. Its rationalized root is regular at `A=0` and `D=0`. This proves the exact interval and converse constraint witness. `K>1` is empty. The witness is explicitly an instantaneous constraint witness. |
| Degenerate sectors | At beta zero, density may be positive while the LRS shear is zero. At K=1 only vacuum remains. At Omega zero, all finite-beta fluid tensor components and shear vanish, while physical matter velocity is undefined and chart beta is retained. No branch divides by A or beta. |
| Joint tensor image | Full STF shear and stress, flux, pressure and density share one tuple. Shear/flux are odd under signed-beta reversal; density/stress/pressure are even. The separate projection intervals cannot be recombined independently. |
| Fixed positive matter | Substitution `t=beta^2/(1-beta^2)` gives `a t^2+b t<=d`, with positive a,b. Monotonicity gives exactly the advertised interval; d<0 is empty and d=0 permits beta zero. Fixing Lambda as well changes the remaining d and imposes equality, selecting one speed magnitude. |
| Compact envelope | The flux/normal-energy ratio r increases with speed and with w on the stated domain. Saturating Lambda=0 gives the positive shear root. It agrees with `sqrt(A)*Omega_max`, including its continuous zero-speed extension. |
| Limiting envelope | Since r<1 for every finite timelike speed, nonzero shear obeys the strict limit for 0<K<1. The limit has vanishing rest density and finite normal energy, and is not a finite-beta vacuum substitution. The K=1 zero-shear endpoint is correctly separated. |
| Conservative tilt implication | Equation (17) follows by monotonic inversion of `v/(1-v^2)` using a common-frame shear ceiling, curvature ceiling and positive matter floor. The note preserves the nonempty compatible-domain requirement and does not obtain this shear ceiling directly from a CMB quadrupole. |
| Bianchi I histories | The two polynomial deformations have identical initial/final B and different derivatives; `sigma/H=dB/dtau`. Final amplitude ratio 9/5, squared ratio 81/25, and intermediate B values are correct. |
| Full final temperature equality | Spatial translation invariance conserves covariant photon momenta. The ratio of emitted to observed energy depends only on shared scale-factor ratio and endpoint B. Liouville transport then yields the entire directional temperature function, without a quadrupole truncation. This is an exact kinematic noninjectivity result. |
| Error geometry | Full STF tensor separation is `alpha*sqrt(6)*epsilon`. Equal closed Frobenius balls are disjoint below half that distance, meet at their midpoint at equality, and intersect above it. No probability or confidence claim is introduced. |

## Actual numerical verification

`inspect_candidate.py` executed the existing consumer once with `--validate-only`, exit 0, against the old sealed numerical candidate. It verified saved arrays against its deterministic recomputation and the old 31-entry manifest. No production file was written. The later rendering repair changed none of the 15 numerical/table/figure files; their exact prior identities were verified before reusing the numerical evidence.

Independent code in `independent_probes.py` made 89 checks without calling the producer's `compute()` or `metrics()`. It used the flux/normal-energy boundary root as an alternate parameterization for all 280 joint and 58,282 heatmap tuples; checked full signed tensors and flux; compared all scalar/vector/tensor CSV values and the exact eight rounded table rows; recovered fixed-density bounds by bisection of the original Hamiltonian; checked all 1,300 boundary tuples and 316 empty grid positions; and tested zero/invalid sectors. Twenty-one invalid input cases returned typed statuses with reasons. A negative directional-expansion witness was explicitly verified.

Two hundred twenty-five Decimal-80 cases checked the actual consumer's closed-form branch at K from 1e-6 through 1, zero and signed near-unit tilt, three w values, and three u values. Their largest absolute discrepancy was `4.440892098500626e-16`. A Decimal limiting sequence verified positive decreasing gaps to the unattained envelope and decreasing rest density. Full-domain validity comes from the analytic proof; these finite checks are not a certification of every machine-singular binary64 input.

The history checks used independent polynomial coefficients and exact rational endpoint identities, tested all saved times and angles, and additionally tested off-axis directions and unequal intermediate-time temperatures. Endpoint rates, normalized squared shear, sphere-axis checks, full-tensor distance, touching midpoint and symbolic threshold were verified. `supplementary_probes.py` added 13 successful checks of fixed-density full scalar/vector carriers, independent envelope evaluation, fixed-Lambda equality cases and claim ceilings. Total independent checks: **102**, in addition to the producer's read-only validation. Frozen tolerances were unchanged.

Detailed numerical outcomes are in `raw/independent_probes.json` and `raw/supplementary_probes.json`. The only runtime warning was unavailable optional Matplotlib Axes3D; all reviewed figures are 2D.

## Rendering and resolved finding

The reviewer rendered and visually inspected all nine original pages, including all six figures, the eight-row table and all 30 numbered equations. All were legible, with correct displayed support, signed mirror branches, fixed-density gaps, compact versus limiting envelope labels, coincident-temperature markers and deterministic error labels. The author surfaced a rendering defect at `report/manuscript.tex:285`: the source limit `B->infinity` acquired a doubled TeX slash and displayed literal `to` instead of the arrow on page 6. The reviewer independently reproduced that defect. It was resolved by the controller-authorized builder's single-token repair before this decision.

The reviewer verified that reversing exactly that one literal replacement reconstructs the prior sealed hashes of `build_product.py`, `manuscript.tex`, normalized Markdown and Pandoc body. The repaired PDF was rendered again: pages 1–5 and 7–9 are pixel-identical to the inspected originals; only page 6 changed. Page 6 was inspected again and now correctly displays `B->infinity`, with no clipping. All 15 numerical/table/figure artifacts are byte-identical. The final producer compile log records exit 0 with nine pages and no missing figures, unresolved references or overfull boxes. The reviewer independently rendered the resulting PDF; it did not rerun the full build or claim a new LaTeX compilation.

The initial producer's numeric lookup-key error, syntax error and LaTeX failures remain in raw logs. They are not disguised as successful first runs. The frozen-source `all ten` wording is an author-confirmed counting typo: the immutable list has nine complete verified entries. Neither correction changes a physical formula, domain, tolerance or conclusion.

## Claim-tier decision and remaining boundaries

Safe scope: conditional instantaneous LRS Bianchi V constraint-image algebra and exact kinematic Bianchi I full-temperature noninjectivity, represented by `bianchi_algebra_note`. No remaining blocking finding was found for that product.

An Einstein-perfect-fluid Bianchi V equal-radiation history pair remains `NOT_ESTABLISHED`; it requires its own declared dynamical family, valid solutions, compatible radiation/observer boundary conditions and response map. No ODE or native solver was run. Native/all-m T/E/B atlas, empirical family identification, likelihood, posterior, null coverage, or original 42-node scientific acceptance are not admitted. Normal vorticity is an exact zero; matter-vorticity remains unevaluated. `x_C`, `Q`, `F`, `Pi`, and `G_F` remain null with their actual missing comparator, denominator, measure, probability-law or depth-support inputs.

Proposed changes: none. Required bounded repair plan: none after the resolved renderer token. Reopen this assessment only for changed science/source identities, changed numerical artifacts or claim scope, a concrete mathematical counterexample, or a substantive rendering change. Exact final candidate binding is required for the controller's future formal packet; this report supplies no invented packet ID or ACK.
