# G08-D source recovery — measurable confidence inversion and certified optimization

Written 2026-10-14 (UTC ≈ 02:50Z) by the single G08-D Lean author, before FROZEN_TARGETS.md.
All paths are relative to the repository root `/home/cosmosapjw/Dropbox/bianchi/htt_base` unless
absolute. Line numbers come from `cat -n` on the files at the hashes below.

## 0. Interruption record

A previous G08-D author run was cut off by a rate limit at about 2026-10-13T22:04Z
(07:04 KST). It left `lean/`, `raw/imports/` and `raw/probes/` empty and one file,
`raw/run_compile.py` (sha256 `ba1561873c1b1b2f02e048993e493f61b6e72053dc695b365a62b1d62073429c`).
That file is preserved byte-for-byte as `raw/run_compile.prior_interrupted_run.py.txt`. This
run starts fresh: `raw/run_compile.py` is rewritten here (same design), and no output from the
interrupted run is reused.

## 1. Card and package

| item | path | sha256 |
|---|---|---|
| package zip | `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip` | `2d0b6da9308ab43e070a620f49241640b5aa7c80c277e1f0857edea22bc4af6f` |
| card | `HTT_ALL_OBLIGATIONS_20261011/tasks/G08-D.json` (inside zip) | `55e37a28f17fe92e822363940438e0048a47d028f3403bf2676a5cbad7de8f02` |

Card fields used verbatim:
- `scope_original`: "상위 measurable projection/union coverage 및 future numerical certificate 의무."
- `existing_reuse`: "G08-B probability law", "G08-C exact decision predicates and containments".
- `lean_steps`:
  1. "confidence set의 graph와 projected events가 measurable인 충분조건을 원래 parameter space에서 증명한다."
  2. "관측 event containment와 coverage theorem을 합성해 each certified decision의 error guarantee를 증명한다."
  3. "optimization 결과를 exact witness/dual bound/interval certificate 등 검증 가능한 object로 정의한다."
  4. "certificate checker soundness를 증명하고 unverified solver outcome은 UNKNOWN으로 반환하도록 source-level decision adapter를 연결한다."
- `acceptance`: optimizer failure strictly distinct from certified emptiness; replay all
  certificates of an actual data run if one exists, otherwise separate the universal checker
  theorem from its pending application; compile, `#print axioms`, raw exit/stdout/stderr;
  fresh independent review.
- `pitfalls`: "uncountable union/projection은 자동 measurable이 아니다."; "solver status code가 수학 증명은 아니다."

## 2. Owning sources

| source | sha256 | role |
|---|---|---|
| `docs/research_program/gr_statistics_loops_20260930/statistics/NATIVE_INFERENCE_THEOREMS.md` | `e215836882047c50a1a5ae6da605d62aa2c553d0de055e279eee3ce35ec8e322` | statements N1, N1a, N2, general inversion, certification rules |
| `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-08.json` | `3a89149e4e025298b35e5db550142c5b25351dc5aef5ee1071f29977030f8d3e` | component boundary; open analytic obligations |
| `docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-08/c03_four_way_decision_input_blocker_v1_20261011/RETURN.json` | `2bd30c25c09ed50319dfc594a7e039d97cd10846be881524c5857048a5943558` | historical C03 blocker (resolved by G08-C) |
| `docs/research_program/gr_statistics_loops_20260930/reviews/STATISTICS_INDEPENDENT_DECISION.md` | (read only; same file the G08-C review hashed) | review wording of certification |

NATIVE_INFERENCE_THEOREMS.md is the file at commit `11602167` (`git log` on that path returns only
`11602167 PR-GR-STATISTICS-CAS-HANDOFF`); the hash equals the contract's research-provenance hash.

### 2.1 Verbatim statements recovered (NATIVE_INFERENCE_THEOREMS.md)

- l.41 model (4): `y = m(θ*) + F β* + ε, ε ~ N_m(0,C)`; l.43 C known positive-definite, F fixed.
- l.79-80 eq. (7): `Q_y(θ) = || P W [y-m(θ)] ||²`, `Cα(y) = {θ∈Ω : Q_y(θ)≤qν,α}`.
- l.84 eq. (8): `Pr_{θ*,β*}{θ*∈Cα(y)} = 1-α`, uniformly in β* (l.86). l.90: ν=0 ⇒ q=0, coverage one.
- l.98-101 Corollary N1a: `Xα={x(θ): θ∈Cα}, Aα=…, Iα={sqrt(g^{ab}A_a A_b): θ∈Cα}` … "the true x, A,
  and acceleration norm are contained in these sets jointly with probability at least 1-α. The
  same event gives simultaneous coverage for every prespecified deterministic function of θ.
  Infimum/supremum intervals enclosing Iα retain coverage, including infinite endpoints."
- l.103 proof: "θ*∈Cα implies containment of each of its deterministic images; taking
  probabilities proves the result."
- l.107-112 four reports (formalized in G08-C).
- l.114 Theorem N2: "the probability of report 1 is at most α … the probability of report 3 is
  at most α … the union of reports 1 and 3 has probability at most α under a true geodesic parameter."
- l.116 proof: "each erroneous event … is a subset of {θ*∉Cα}. Apply (8)."
- **l.120 (certification rules, the owning text for "certified optimization")**:
  "A feasible point with Q≤q certifies nonemptiness. Null exclusion requires a rigorous lower bound
  inf_{Ω∩G}Q>q, or another verified proof of infeasibility. Failure of a local optimizer to find a
  null point is not that proof. Infimum equality q can be inconclusive if the infimum is not
  attained. Compact parameter boxes give attainment only when the domain and objective are also
  closed/continuous there; arbitrary boxes can destroy coverage unless independently justified. A
  confidence set of sampled solutions is an inner approximation and cannot establish coverage or
  null exclusion. A certified outer enclosure can. A strictly positive lower bound on Iα is
  sufficient for exclusion; exclusion of zero need not imply a positive infimum for a noncompact set."
- l.15, l.17: `A_a = 2c B_ab u^b`; `a(x)=sqrt(g^{ab}A_a A_b)` real and nonnegative.
- l.21 eq. (2): `G = {x : B_ab(x)u^b(x)=0}`.
- l.69: union of scenario confidence sets; "Bounds obtained from a separate confidence procedure
  with failure probability δ give at least 1-α-δ coverage by the union bound".
- l.180 general native likelihood inversion: "If a fully specified family p_θ,β … admits
  acceptance regions R_θ,β with Pr_θ,β(y∈R_θ,β)≥1-α, then the set {(θ,β): y∈R_θ,β} and all its
  projections have ≥1-α coverage."
- l.182: "For a deterministic covariance uncertainty set S that is known to contain C*, a union of
  valid sets Cα,C over C∈S retains ≥1-α coverage, because the union contains Cα,C*. If S covers C*
  with probability ≥1-δ, the same event-intersection argument gives ≥1-α-δ under valid fixed-C*
  calibration."
- l.200 (recipe, not executed): "compute certified enclosures/lower bounds if an exclusion claim is
  sought. Record parameter domain, units, tolerances, all solver certificates, and whether a
  minimizer is attained. Report unresolved optimization honestly."

### 2.2 CAS-08.json (contract)

- l.41/107 (pretty-printed): C03 "… Gaussian law, quantile coverage and measurable projection/union
  theorems remain outside this component."
- `full_theorem_boundary.additional_analytic_obligations` (l.246-250): "Gaussian invariance and
  chi-square quantile", "Measurability/containment proof", "Future numerical optimization
  certificate separately required".
- `singular_loci`/`invariants`: "CONF-EMPTYMODEL not acceleration", "CONF-OPTFAIL not certified
  infeasibility", "CONF-RANK0 coverage1", "CONF-ESTIMATEDC no exactchi2".
- `exclusions`: "Inner sample set not confidence enclosure".
- `uncontracted_research_targets`: "Projection simultaneous coverage>=1-alpha", "General-law
  inversion and uncertainty unions retain declared coverage".

### 2.3 Review wording (STATISTICS_INDEPENDENT_DECISION.md l.50; .json l.73)

"To report rejection, a feasible alternative point and certified null infeasibility are needed. A
local optimizer's failure is insufficient. Inner samples of a confidence set are insufficient for
coverage or exclusion. An outer enclosure may support exclusion only together with the appropriate
feasibility certificate and rigorous enclosure relation. Noncompactness matters …" and the N2
condition "Alternative feasibility and null exclusion certified".

## 3. What "certified optimization" means in the source (recovered, not invented)

The source does **not** prescribe a concrete optimizer certificate file format, solver, or
interval-arithmetic encoding. It specifies *which mathematical objects certify what*:

| certificate kind (source wording) | certifies | formal object in this unit |
|---|---|---|
| "A feasible point with Q≤q" (l.120) | nonemptiness of Cα or Cα,G | `WitnessCert` (point + membership + `Q θ ≤ q`) |
| "a rigorous lower bound inf_{Ω∩G}Q>q" (l.120) | emptiness of Cα,G | `LowerBoundCert` (b > q, ∀θ∈Ω', b ≤ Q θ) |
| "A certified outer enclosure can" (l.120); card: "interval certificate" | emptiness via an enclosure of the domain | `CoverCert` (cells covering Ω', a strict bound on each cell) |
| card: "dual bound" | emptiness of a constrained set Ω0 ∩ {g=0} | `DualCert` (Lagrangian weak-duality multipliers) |
| "another verified proof of infeasibility" (l.120) | emptiness | `ExclCert.proof` (any Lean proof of emptiness) |
| "A strictly positive lower bound on Iα is sufficient for exclusion" (l.120) | emptiness of Cα,G | theorem `accel_lower_bound_excludes` |
| "Failure of a local optimizer … is not that proof" (l.120); CONF-OPTFAIL | — | `SolverRun`/`SolverStatus` carry no proof; adapter ignores them |
| "A confidence set of sampled solutions is an inner approximation" (l.120) | nothing about emptiness | negative control `inner_samples_not_exclusion` |

The dual-bound and cover formats are the card's own named object kinds ("exact witness/dual
bound/interval certificate"); their exact field layout is this unit's definition, chosen as the
weakest data that makes the source's l.120 sufficiency claims provable. No acceptance threshold,
outcome name, or report criterion is invented: reports and `Cert` are imported unchanged from
G08-C.

## 4. Reused, reviewed Lean sources (imported unchanged)

| module | path | sha256 | review |
|---|---|---|---|
| ProjectionBridge | `…/CAS-08/c01_c02_projection_bridge_v1_20261011/ProjectionBridge.lean` | `440e3820a53a1bc12465975eaed331db2e9b4f7fbdc4e97d9d5c58a4c1cc2219` | RETURN status FORMALLY_CHECKED_SCOPED_BRIDGE |
| G08AWhitening | `…/CAS-08/g08a_whitening_gls_v1_20261013/lean/G08AWhitening.lean` | `e62280213d23063cf4309aa8bdc814b2925f44f50cb81859f6b91bcb976bf045` | FORMALLY_CHECKED_SCOPED |
| G08ACorollaries | `…/CAS-08/g08a_whitening_gls_v1_20261013/lean/G08ACorollaries.lean` | `225e46da37dd6a8841c1dfae9e32488712c1dfdc548213a01d5d91653704b34e` | FORMALLY_CHECKED_SCOPED |
| G08BGaussianLaw | `…/CAS-08/g08b_projected_gaussian_law_v1_20261013/lean/G08BGaussianLaw.lean` | `472178ed275c772f1b6c9d276df7387dc44336254c66d364a0cf6604f440c122` | FORMALLY_CHECKED_SCOPED, review PASS_WITH_NOTES |
| G08CFourWay | `…/CAS-08/g08c_four_way_decision_v1_20261014/lean/G08CFourWay.lean` | `17a8411e770776fdf584486ed7564121a3e65990d46327df6fd6795dd9c58225` | FORMALLY_CHECKED_SCOPED, review PASS_WITH_NOTES |

All five hashes equal the hashes recorded in the corresponding RETURN.json / AUTHOR_RETURN.json.
Definitions reused: `G08C.confSet`, `G08C.nullConfSet`, `G08C.Cert`, `G08C.Report`,
`G08C.fourWayReport`, the three report predicates, `G08C.Bu`, `G08C.geodesicNull`,
`G08C.minkowski`; `G08BGaussianLaw.Qstat`, `threshold`, `coverage`, `coverage_rank_zero`,
`measurable_Qstat`; `G08AWhitening.IsMoorePenrose`.

The G08-C reviewer's scratch probe `bridge_hcov`
(`/tmp/claude-1000/…/scratchpad/g08-c_rerun/bridge/BridgeProbe.lean`) was read as a hint that
G08-B discharges G08-C's `hcov`; it is not imported or copied; the discharge is re-proved here.

## 5. Implementation search

- `grep -rn "computationally.unresolved|geodesicity.rejected|null.exclusion|four.way" htt/ scripts/ tools/`
  (Python): no hit. There is no implementation of the four-way decision or of an optimizer
  certificate in `htt/`.
- `git log --all --grep "certified optim"` finds `5aa4e7f96 PR-189 … certified optimizer`; that is
  the HTT/Bianchi joint-feasible-set LP lane (`docs/generated/pr189_cas/*`), not the GR-statistics
  geodesicity decision; it defines no certificate format for this source and is not used.
- `cas/COMMON_SPEC.md`: no certificate/optimizer/measurability wording (grep empty).

## 6. Items that cannot be recovered (recorded, not invented)

1. **Concrete optimizer certificate file format / solver identity**: absent from every source
   above. Unlock: a source-bound data-run contract naming the solver and its certificate output.
   Until then only the universal checker theorems are claimed; application is pending.
2. **Actual data run / certificate replay** (card acceptance item 2): no data run exists in the
   repository for this decision (`NATIVE_INFERENCE_THEOREMS.md` l.193 "not executed", l.195 "no
   bytes … inspected"). Status: universal checker theorems only; replay pending a data run.
3. **Topology on the physical parameter type**: G08-C's `FirstJet` carries no topology, so
   closedness of the concrete `geodesicNull` (needed by the σ-compact measurability theorem) is a
   hypothesis `IsClosed G` on a generic topological `X`, not proved for `FirstJet`.
4. **Compactness of the source domain**: Ω in (5) has `0<r_i` (open end) and unbounded `x`; it is
   not compact. The measurability theorem therefore takes σ-compactness (countable union of compact
   pieces) as an explicit hypothesis rather than asserting it for the source Ω.
