# G08-C source recovery — four-way geodesicity decision

Recorded 2026-10-14 against checkout HEAD `4dbe588698f15eb0a93df657d5bc7b5d0acd1e06`
(read-only; no state-changing git command was run).

## Card and blocker

- Card `HTT_ALL_OBLIGATIONS_20261011/tasks/G08-C.json` inside
  `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip`
  (zip sha256 `2d0b6da9308ab43e070a620f49241640b5aa7c80c277e1f0857edea22bc4af6f`,
  card bytes sha256 `88722a696c2fee3e6ac8bcf3cd732054c5d7611019fdaedf944759e986023843`).
- Contract text `CAS-08-C03` (`cas/contracts/CAS-08.json`, sha256
  `3a89149e4e025298b35e5db550142c5b25351dc5aef5ee1071f29977030f8d3e`;
  local `EXECUTION_CONTRACT.json` sha256
  `22584699a7c72c2cb56ee15d2640fb021895d961bc4368af12706dd36cdc415a`):
  "Express the four-way geodesicity decision as finite set-containment
  implications, preserving full-model feasibility. Gaussian law, quantile
  coverage and measurable projection/union theorems remain outside this
  component."
- Prior blocker `../c03_four_way_decision_input_blocker_v1_20261011/RETURN.json`
  (sha256 `2bd30c25c09ed50319dfc594a7e039d97cd10846be881524c5857048a5943558`)
  listed four missing items: (i) four outcome predicates, (ii) finite
  candidate/full-model sets and domains, (iii) acceptance regions, thresholds
  and boundary conventions, (iv) directed containment implications and the
  full-model feasibility convention. That blocker was correct for its
  *permitted* inputs (contract + COMMON_SPEC only; the blind CAS protocol
  forbade `statistics/**`). The contract itself names the owning source as a
  research-provenance hash with `access: orchestrator_identity_only`:
  `statistics/NATIVE_INFERENCE_THEOREMS.md`,
  sha256 `e215836882047c50a1a5ae6da605d62aa2c553d0de055e279eee3ce35ec8e322`.

## Recovered owning source (verbatim; hash matches the contract's provenance hash)

File `docs/research_program/gr_statistics_loops_20260930/statistics/NATIVE_INFERENCE_THEOREMS.md`
(working-tree sha256 `e215836882047c50a1a5ae6da605d62aa2c553d0de055e279eee3ce35ec8e322`;
`git show 11602167b:<path> | sha256sum` gives the same hash; `git log -S "computationally unresolved"`
returns only commit `11602167b64e4f0c50c1f57c37fe9df2292f9725`
"PR-GR-STATISTICS-CAS-HANDOFF: Publish research and local CAS contracts", i.e.
the section has never been revised).

| Missing item (blocker) | Recovered text | file:line |
|---|---|---|
| geodesic null subset | "G = {x : B_ab(x)u^b(x)=0}. (2)"; three independent constraints | NATIVE_INFERENCE_THEOREMS.md:19-23 |
| kinematics of x, u, S, B | "Z0(n)=ζ0+ζ·n, ζ0=sqrt(1+|ζ|²) … u=(ζ0,ζ), S00=h0, S0i=-h1i/2, Sij=h2ij, B=S+S(u,u)g, A_a=2cB_ab u^b (1)"; x=(ζ,h0,h1,h2), dimension 12 | NATIVE_INFERENCE_THEOREMS.md:9-17 |
| (cross-check) same lift | "u^α=(ζ0,ζ_i), S00=h0, S0i=-½h1i, Sij=h2ij (8); B=S+S(u,u)g (9)"; "A(p)=0 … is equivalent to Bu=0" | gr/OPTICAL_THEOREMS.md:76-81, 226 (sha256 `5ae2b6a6…8c21`) |
| full candidate set / domain | θ (contains x, latent r_i, ρ_i, nonlinear nuisances) in the declared enlarged domain Ω, eq. (5) or (6) | NATIVE_INFERENCE_THEOREMS.md:41-43, 56-67 |
| statistic, threshold, boundary | "Q_y(θ)=‖PW[y-m(θ)]‖², Cα(y)={θ∈Ω : Q_y(θ)≤qν,α} (7)" — **non-strict** acceptance; "If ν=0 set q=0; Cα=Ω" | NATIVE_INFERENCE_THEOREMS.md:77-80, 90 |
| null subset of the full set | "Define Cα,G={θ∈Cα : x(θ)∈G}" | NATIVE_INFERENCE_THEOREMS.md:107 |
| four outcome predicates | "1. Cα nonempty and Cα,G empty: geodesicity rejected within the declared observation/remainder model. 2. Both nonempty: geodesicity not excluded by this confidence procedure. 3. Cα empty: declared model class incompatible at this acceptance threshold; do not call this acceleration detection. 4. Feasibility or exclusion not certified: computationally unresolved." ("mutually distinct reports") | NATIVE_INFERENCE_THEOREMS.md:107-112 |
| directed implications (N2) | "Under every true parameter satisfying (4), θ*∈Ω and x*∈G, the probability of report 1 is at most α. Under every true parameter in Ω, the probability of report 3 is at most α. … the union of reports 1 and 3 has probability at most α under a true geodesic parameter." Proof: "each erroneous event, and their union under the null, is a subset of {θ*∉Cα}" | NATIVE_INFERENCE_THEOREMS.md:114-116 |
| certification conventions | "A feasible point with Q≤q certifies nonemptiness. Null exclusion requires a rigorous lower bound inf_{Ω∩G}Q>q, or another verified proof of infeasibility. Failure of a local optimizer to find a null point is not that proof. Infimum equality q can be inconclusive if the infimum is not attained. … exclusion of zero need not imply a positive infimum for a noncompact set." | NATIVE_INFERENCE_THEOREMS.md:120 |
| projection containment (N1a) | Xα, Aα, Iα images; "simultaneous coverage for every prespecified deterministic function of θ. Infimum/supremum intervals enclosing Iα retain coverage, including infinite endpoints." Proof: θ*∈Cα implies containment of each deterministic image | NATIVE_INFERENCE_THEOREMS.md:96-103 |
| union of scenarios | "take the union of their confidence sets. Intersecting them asserts all scenarios simultaneously and has no such guarantee. Bounds obtained from a separate confidence procedure with failure probability δ give at least 1-α-δ coverage by the union bound" | NATIVE_INFERENCE_THEOREMS.md:69 |
| general-law acceptance regions | "{(θ,β): y∈R_θ,β} and all its projections have ≥1-α coverage" | NATIVE_INFERENCE_THEOREMS.md:180 |
| review-accepted N2 statement | "Rejecting pointwise geodesicity only when the total set is nonempty and its geodesic intersection empty has type-I error at most alpha; total-set emptiness is separately model incompatibility"; conditions "Alternative feasibility and null exclusion certified", "Total-model emptiness separately reported"; STAT-F03 "PASS: four-way decision includes empty and unresolved cases." | reviews/STATISTICS_INDEPENDENT_DECISION.json:69-80, 212-215 (sha256 `4b4f7800…a9c7`); statistics/STATISTICAL_CLAIMS_NATIVE.json:56-60 (sha256 `286e6996…97d6`) |
| contract singular loci | "CONF-RANK0 coverage1", "CONF-EMPTYMODEL not acceleration", "CONF-OPTFAIL not certified infeasibility" | cas/contracts/CAS-08.json `semantics.singular_loci` |

Also searched (no additional or conflicting definition): `supplements/DOSSIER_POSITIVE_BRIDGE.md`,
`supplements/*.json`, `cas/COMMON_SPEC.md` (no four-way text),
`RESEARCH_HANDOFF.json:160` (S04 only requires "Four-way status" in a later
catalogue run), `local_sequential_verification_20261001/PROOF_DAG.json:560-590`
and `PROOF_VERIFICATION_PLAN_KO.md:424-430` (restate C03 text only),
`htt/` (four-way hits only in unrelated PR13AH observables code).

## Formalization decisions taken from the source (not invented)

1. Report names: `geodesicityRejected` (1), `notExcluded` (2),
   `modelIncompatible` (3), `computationallyUnresolved` (4) — abbreviations of
   the bold source phrases at lines 109-112.
2. Acceptance is non-strict `Q θ ≤ q` (line 80). Exclusion certificate is a
   strict bound `q < b ≤ Q` on Ω∩x⁻¹G (line 120: "inf … > q").
3. Reports 1-3 are semantic set predicates (lines 109-111); report 4 is the
   certification state (line 112 with line 120). The delivered report is
   therefore a function of proof-carrying certificates: a feasible point
   (`θ ∈ S`) or a verified emptiness proof (`S = ∅`) or none. Since
   Cα,G ⊆ Cα (line 107), a feasible null point certifies both sets nonempty
   (report 2). Report 1 needs both a full-set feasibility certificate and a
   null-exclusion certificate (review condition "Alternative feasibility and
   null exclusion certified"). Report 3 needs a certificate that Cα = ∅.
   Every other certificate combination is report 4.
4. Generic types: Θ (complete parameter), X (physical first jet), x : Θ → X,
   Ω ⊆ Θ, G ⊆ X, Q : Θ → ℝ (or Y → Θ → ℝ for event statements), q : ℝ.
   Theorems are universally quantified over these, which includes the
   specific Q_y of eq. (7) and the specific Ω of eq. (5)/(6). The concrete
   G of eq. (1)-(2) is additionally formalized on a 12-component first-jet
   type for non-vacuity witnesses.
5. The probabilistic N2 bound (≤ α) depends on N1 coverage (8), which is
   outside C03. It is stated only as a corollary *conditional* on an explicit
   coverage hypothesis `μ {y | θ* ∉ Cα(y)} ≤ α`; the unconditional N2
   probability statement is not claimed.

## Imports

No earlier CAS-08 module is needed: C03 is generic in Q and does not use the
projector/GLS algebra of ProjectionBridge or G08-A. G08-B
(`g08b_projected_gaussian_law_v1_20261013`) has only an AUTHOR_RETURN (no
reviewed RETURN.json), so it is not imported; its coverage theorem would be
the natural discharge of the coverage hypothesis in item 5 after review.

## Residual ambiguity

None for the four predicates, sets, domain, threshold and implications. One
interpretive point is recorded rather than resolved: the source does not
specify how certificates for Cα = ∅ are produced (it only names a lower bound
or "another verified proof of infeasibility"); the formalization accepts any
Lean proof of emptiness, plus a lemma that a strict lower bound > q is such a
proof.
