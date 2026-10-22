# G09-A source recovery: CAS-09 C01–C04 definitions

Task card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip::HTT_ALL_OBLIGATIONS_20261011/tasks/G09-A.json`
(card sha256 `cc96c7a4c2473574481ef1684ec9dc961f03f5ac9198a644adf691348208542f`,
package sha256 `2d0b6da9308ab43e070a620f49241640b5aa7c80c277e1f0857edea22bc4af6f`).
Checkout HEAD at recovery: `7bc52116b02feb543ee464ed6954773d555ef14b` (read-only; no git state changes).
Scientific admission: **HOLD**. This file recovers definitions; it promotes no claim.

All paths below are relative to `docs/research_program/gr_statistics_loops_20260930/` unless absolute.

## 1. Inputs read and their hashes

| role | path | sha256 |
|---|---|---|
| blocker inventory (start point) | `local_cas/GRSTAT-CAS-20260930-1308KST/CAS-09/input_definition_blocker_v1_20261011/RETURN.json` | `e8b4e50f483df69d95d89a3423f3bbe0dd5f09ccc2efbf7afe6dba2740caeee5` |
| published contract | `cas/contracts/CAS-09.json` | `4913de308fc006f3658a45a88cd1d8400b1aaf3d1249927e677cca74842e4a3b` |
| execution contract | `local_cas/GRSTAT-CAS-20260930-1308KST/CAS-09/EXECUTION_CONTRACT.json` | `c09019b055faa4be95d0d1d83a13431065d8730bc72b7cbca0493efac3070134` |
| historical adjudication (CAS_CONFLICT) | `local_cas/GRSTAT-CAS-20260930-1308KST/CAS-09/ADJUDICATION.json` | `a9ef157529e0b10b4e02173e103c7e8dd5bb3f048f9c9ddd0289da822494d063` |
| neutral conventions | `cas/COMMON_SPEC.md` | `4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897` (matches contract) |
| **primary source** (contract research provenance) | `statistics/NATIVE_INFERENCE_THEOREMS.md` | `e215836882047c50a1a5ae6da605d62aa2c553d0de055e279eee3ce35ec8e322` (matches contract `research_provenance_hashes`) |
| optical image theorem | `gr/OPTICAL_THEOREMS.md` | `5ae2b6a65a5704247bed3d7dc5f01924318063ee5443cfa95c30c452b0ea8c21` |
| finite-distance envelope | `gr/FINITE_DISTANCE_THEOREM.md` | `d499eb7fdc523926fd981c5b65a37d7b9dd894560973b6be3a2046972a5e50ac` |
| larger research claim list | `cas/CAS_TASKS.json` (entry `CAS-09`, lines 581–640) | `b5655092cc859b0a9aa410984aa3c82249b476696fcccffb95d94ff7a0bed511` |
| independent decision note | `reviews/STATISTICS_INDEPENDENT_DECISION.md` (line 40 N3, line 42 N4) | `f38cbf67f81f4f636943d113efd39b95801951d576abb4e5446d83a1124d93ac` |
| claim ledger | `statistics/STATISTICAL_CLAIMS_NATIVE.json` (N3/N4 entries, lines 64–86) | `286e699627a76c31278a9b0e005f5cda352b96ead26202dc006f6ca1911097d6` |
| missing-definition audit | `cas_corr_followup_20260930/intake/NEXT_INPUT_AUDIT.json` (`missing_neutral_definitions.CAS-09`) | `aa18337bea74b98ec34d69290d6664a4313cdc6a082b338614bb59adf993748d` |
| historical own-axis fixture (not source) | `local_cas/.../CAS-09/wolfram_xact/check.wl` | `64e0e57523ffb8bdf40f9a989a653c1bccb47946f96fc5d9ce24e0abbc7f04ab` |

Access note: the execution contract lists `statistics/**`, `gr/**`, `reviews/**` as forbidden
*for blind CAS axes*. This G09-A task is a source-recovery task whose card explicitly
directs reading theory docs and PR history; the original blind-axis independence of
CAS-09 is therefore not claimed for this unit (see AUTHOR_RETURN `not_claimed`).

## 2. Search trail

* `git log --all -- statistics/NATIVE_INFERENCE_THEOREMS.md local_cas/.../CAS-09` →
  `81505b983` (blocker), `04a8ed0ef` (CAS-01 recovery), `11602167b` (contract publication).
* `git log --all -S unisolvent` → `81505b983`, `04a8ed0ef`, `0db3cad2a`, `08429842d`, `11602167b`;
  `git grep unisolvent 0db3cad2a -- docs` returns only the contract/DAG paraphrases,
  `reviews/STATISTICS_INDEPENDENT_DECISION.md:40`, `statistics/STATISTICAL_CLAIMS_NATIVE.json:72`
  and the follow-up audit lines quoted below. No commit supplies concrete sample directions.
* `git log --all -S "R/(1+"` → only `04a8ed0ef`, `0db3cad2a`, `11602167b` (contract/DAG copies of (13)).
* `grep -rIl "unisolvent|radial.alias|mass.shell" htt/` → only
  `htt/src/common/relativistic_kinematics.py:101` (a docstring remark that noisy fits do not lie on
  a mass shell); no implementation of E4/E9, the intercept chart, the alias family, ρ_i or native means.
* Package `PR_INDEX_ALL.csv`: no row mentions CAS-09 / native inference.
* Other local CAS units scanned for reusable accepted Lean (`CAS-10/c02_mass_shell_invariant`,
  `CAS-10/g10a_*`, `CAS-07/*`): their objects (Sym4 rest-space positivity; Jacobi/η majorants)
  are different from the CAS-09 objects; nothing is imported (see §5).

## 3. Symbol table: source location → formal Lean type

Lean module: `lean/G09ADefinitions.lean`, namespace `G09A`.

### Shared (C01–C04)

| symbol | source | Lean |
|---|---|---|
| signature, observer tetrad o=(1,0,0,0), K=-o+n, n unit spatial | NATIVE l.9; COMMON_SPEC l.4–5, 14 | `V3 := Fin 3 → ℝ`, `dot3`, `IsUnitDir n : dot3 n n = 1` |
| sample directions n_i (known, unit) | NATIVE l.29 ("take their directions n_i as known"), l.124 | `dir : ι → V3` (index type `ι`, `[Fintype ι]`) |
| radii r_i>0, c>0, D=diag(r_i/c) | NATIVE l.29, l.124; contract `task_assumptions` | `r : ι → ℝ`, `c : ℝ`, `Dmap r c` |
| Z0(n)=ζ0+ζ·n, ζ0=√(1+|ζ|²) (future, positive branch) | NATIVE l.11; OPTICAL (7) l.70 (ζ0²−|ζ|²=1, ζ0≥1), l.104 (negative branch not allowed) | `zeta0 ζ := √(1+dot3 ζ ζ)`, `Z0 ζ n := zeta0 ζ + dot3 ζ n` |
| H(n)=h0+h1·n+h2:nn, h2 symmetric trace-free | NATIVE l.12; OPTICAL (6) l.61–62; COMMON_SPEC l.15 | `HPar := ℝ × V3 × (Fin 5 → ℝ)`, `stf q` (STF matrix from 5 coordinates), `quad q n`, `Hval h n` |
| physical parameter x=(ζ,h0,h1,h2), dim 12 | NATIVE l.17; OPTICAL l.75 ("dimension 3+9=12") | `PhysPar := V3 × HPar` |

### C01 (N3 rank identity and two-radius design)

| symbol | source | Lean |
|---|---|---|
| E4 rows (1,n_iᵀ) — exact normalization | NATIVE l.124 | `IPar := ℝ × V3`, `ipoly a n := a.1 + dot3 a.2 n`, `E4 dir : IPar →ₗ[ℝ] (ι → ℝ)` |
| E9: "any real basis of degree≤2 spherical polynomials … containing the degree≤1 basis" | NATIVE l.124–125 | `E9 dir : HPar →ₗ[ℝ] (ι → ℝ)` in the coordinate basis (h0, h1, STF coordinates q). The source leaves the basis free; all claims are ranks/ranges, invariant under a change of basis of the 9-dim coefficient space. Our basis contains the degree≤1 basis (h0,h1). `stf` is proved to be a bijection onto symmetric trace-free matrices. |
| X=[E4, D E9], 13 columns before intercept normalization | NATIVE l.126–128, eq.(10) | `Xmap dir r c := (E4 dir).coprod ((Dmap r c).comp (E9 dir))` on `IPar × HPar` (finrank 13) |
| rank criterion (11) | NATIVE l.130–136 (Theorem N3) | `rank13_iff`, `rank_concat_identity` |
| two-radius 9+4 design: nine unisolvent directions at R1>0, four of those repeated at R2>0, R2≠R1, E4 submatrix rank 4 | NATIVE l.150 | `twoRadiusDir dir9 σ := Sum.elim dir9 (dir9 ∘ σ)` on `Fin 9 ⊕ Fin 4`, `twoRadiusR R1 R2`; "declared nonzero determinants" = `Function.Injective (E9 dir9)` (9×9 E9 nonsingular) and `Function.Injective (E4 (dir9 ∘ σ))` (4×4 E4 nonsingular) |
| "unisolvent" convention | NATIVE l.138 ("unisolvent directions (rank E9=9)") | `Function.Injective (E9 dir)` |
| exact rational sphere-direction certificate | contract `canonical_form[0]` | NOT given in any source. Supplied as an explicit witness `dirStar`, `σStar` (rational unit vectors; same point set as the historical Wolfram fixture `check.wl` lines 9–12 but proved here independently). Status: a *witness*, not a recovered source definition. |

### C02 (mass-shell intercept chart and physical Jacobian)

| symbol | source | Lean |
|---|---|---|
| 13-variable unconstrained chart (ζ0, ζ, h) | NATIVE l.126–128 ("13 columns, before the one physical intercept normalization") | domain `IPar × HPar` of `Xmap` |
| 12-variable mass-shell embedding ζ ↦ (√(1+|ζ|²), ζ); deletion convention: ζ0 is eliminated, physical coordinates are (ζ,h) | NATIVE l.152 ("physical chart ζ0=√(1+|ζ|²)"); OPTICAL (7) | `massShell ζ : IPar := (zeta0 ζ, ζ)`; `physMean dir r c x i := Z0 x.1 (dir i) + (r i / c) * Hval x.2 (dir i)` |
| Jζ = Ndir + 1(ζ/ζ0)ᵀ, Jphys=[Jζ, D E9] | NATIVE l.154–155, eq.(14); contract `canonical_form[1]` | `dEmb ζ`, `chartDeriv ζ`, `Jphys dir r c ζ := Xmap ∘ chartDeriv ζ`; canonical form proved as `Jphys_apply`; derivative proved as `hasFDerivAt_physMean` |
| "Full rank X implies rank Jphys=12" | NATIVE l.157 | `rank12_of_rank13` |

### C03 (constant radius and radial alias)

| symbol | source | Lean |
|---|---|---|
| constant radius r_i=R>0 → col(E4)⊂col(DE9), rank X=rank E9≤9 | NATIVE l.138 | `const_radius_range_le`, `const_radius_rank`, `const_radius_rank_le9`, `const_radius_rank9` |
| exact degeneracy H′=H+(c/R)[Z0−Z0′] | NATIVE l.140, eq.(12) | `const_radius_exact_degeneracy` |
| rank Jphys=9 at constant R, unisolvent | NATIVE l.157 | `const_radius_Jphys_rank9` |
| r_i=R/(1+ε n_iz), 0<|ε|<1; positive denominator | NATIVE l.144–148, eq.(13); n_z = third component of unit n (frame axis z) | `aliasRadius R ε n := R / (1 + ε * n 2)`, `aliasDenom_pos`, `aliasRadius_pos` |
| (1+εn_z)p(n) has degree≤2 on the sphere; col(E4)⊂col(DE9); rank X=9 | NATIVE l.148 | `radial_alias_range_le`, `radial_alias_rank`, `radial_alias_rank9` |
| DESIGN-R1R2 equal fails | contract `singular_loci` | `two_radius_equal_fails` |
| DESIGN-ANGULAR rank deficient | contract `singular_loci` | `two_radius_fails_of_E4_deficient` |

### C04 (native means, ρ_i transform, remainder domain)

| symbol | source | Lean |
|---|---|---|
| Z_i = Z0(x,n_i) + (r_i/c)H(x,n_i) + ρ_i > 0 | NATIVE l.31, eq.(3) | `nativeZ dir r c x ρ` |
| m_zi = Z_i − 1 | NATIVE l.32 | `meanZ Z` |
| m_μi = 5 log10[r_i Z_i²/(10 pc)] (same length unit) | NATIVE l.33–35 | `meanMu r Z tenpc` with `tenpc>0`; argument positivity `meanMu_arg_pos` |
| native domain r_i>0, Z_i>0 | NATIVE l.29, l.31 | `NativeDomain r Z` |
| ρ_i(x)=Z_i−Z0(x,n_i)−(r_i/c)H(x,n_i) | NATIVE l.167; CAS_TASKS `exact_target[4]` | `rhoOf dir r c Z x` |
| η(s)=sinh(√Kc s)/(√Kc s)−1, η=0 if Kc=0; ηL=η(L)<1 | NATIVE l.52–54; FINITE_DISTANCE l.15–18 | `eta Kc s`, `EnvelopeParams` (Kc≥0, M2≥0, L>0, η(L)<1) |
| enlarged domain Ω, eq.(5): 0<r_i≤L(1+ηL), |ρ_i|≤E_i | NATIVE l.56–60 | `E5 P c Hn r`, `Omega5 P c dir x r ρ` |
| tighter latent-s domain, eq.(6) | NATIVE l.62–65 | `Omega6 P c dir x r ρ` (defined only) |
| physically realizable set (one smooth spacetime/congruence) | NATIVE l.67: "outer approximation … Sufficiency … has not been proved" | **deliberately not defined** (pitfall: the realizable remainder domain must not be identified with the enlarged Ω) |
| N4 strict slack neighbourhood | NATIVE l.163–169 | `strict_slack_local_identification` (in Ω5 only) |
| SLACK-BOUNDARY no neighbourhood conclusion | contract `singular_loci` | `slack_boundary_no_neighbourhood` |

## 4. Residual ambiguities (UNKNOWN branches only)

1. **Concrete sample directions / radii of any actual catalogue**: no source supplies them
   (NATIVE l.150 says "Take nine unisolvent directions"; l.193–202 the data recipe is "not executed").
   Searched: NATIVE, CAS_TASKS, contract, reviews, STATISTICAL_CLAIMS_NATIVE, git history (`-S unisolvent`, `-S "R/(1+"`), htt/.
   Resolution here: theorems are universally quantified over directions satisfying the source's
   nonzero-determinant hypotheses, plus one explicit rational witness. Unlock for a catalogue-specific
   statement: a frozen catalogue direction/radius table.
2. **A specific E9 basis normalization**: the source deliberately leaves it free (NATIVE l.124). Not an
   ambiguity for rank/range claims; a specific normalization (e.g. orthonormal real harmonics) would be
   needed only for conditioning/singular-value statements, which are explicitly out of scope
   ("Formal full rank is not adequate precision", NATIVE l.159).
3. **Physically realizable remainder set**: not defined by any source (NATIVE l.67). UNKNOWN by design;
   only the enlarged outer domain Ω (5) is formalized.
4. η at s=0: source fixes η(0)=0 by continuity (FINITE_DISTANCE l.18); the Lean `eta` is only used at
   s>0 (L>0, latent s_i>0), where the formula is the source formula.

## 5. Reuse

No accepted Lean source in CAS-09 exists (historical `CAS-09/lean/Main.lean` is a two-line placeholder,
`result.json` all components false). No other accepted module formalizes E4/E9, the intercept chart,
ρ_i or Ω; so `raw/imports` contains only this unit's compiled module.
