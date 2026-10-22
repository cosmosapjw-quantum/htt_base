# G17-A source recovery (CAS17-C02 constant scale, CAS17-C03 general conformal)

Author unit: single Lean author, 2026-10-22/23 UTC. Repository HEAD at start:
`a8fd176305fb475947a46f9dacb651805d323741` (branch `research/htt-open-input-theory-20261018`).
Run history: a previous author run for this card was cut off by a rate limit
before writing anything (T did not exist when this run started). This run
started fresh; nothing from the interrupted run is reused.

Paths below are relative to `docs/research_program/gr_statistics_loops_20260930/`
unless absolute. Line numbers refer to the files with the listed SHA-256.

## Source identities

| source | SHA-256 |
|---|---|
| `cas/contracts/CAS-17.json` | `123c73d56cf1c4d85acfce8536161011d4cb42b91f93e7bc0e3e67780296877e` |
| `cas/COMMON_SPEC.md` | `4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897` |
| `supplements/DOSSIER_POSITIVE_BRIDGE.md` | `00c1fcb0b786bb874f13e52442af4b7b8a125287d84decb799ea68fd03915ebd` |
| `statistics/NATIVE_INFERENCE_THEOREMS.md` | `e215836882047c50a1a5ae6da605d62aa2c553d0de055e279eee3ce35ec8e322` |
| `ADDED_BOOK_INTEGRATION.md` | `977125a6efe3dc38f2eabb833b5feebe8e203752c58e6273e51b01edb3009dbf` |
| `gr/OPTICAL_THEOREMS.md` | `5ae2b6a65a5704247bed3d7dc5f01924318063ee5443cfa95c30c452b0ea8c21` |
| `gr/FINITE_DISTANCE_THEOREM.md` | `d499eb7fdc523926fd981c5b65a37d7b9dd894560973b6be3a2046972a5e50ac` |

The first five hashes equal the reviewed freeze
`local_cas/GRSTAT-CAS-20260930-1308KST/CAS-17/c02_c03_source_definition_freeze_v1_20261011/SOURCE_DEFINITION_FREEZE.md`
(PASS_SCOPED review). The two `gr/` files are the upstream definitions that
NATIVE_INFERENCE_THEOREMS.md:25 names as its input source.

The historical receipt `c02_c03_scaling_conformal_input_blocker_v1_20261010/RETURN.json`
(BLOCKED_UNBOUND_GEOMETRIC_DEFINITIONS) is superseded for definitions only:
every item it lists as missing is recovered below from repository documents.
**No user-input blocker is declared by this unit.**

## Exact decision: `Z` means `1+z` (not `z`)

`Z` is the dimensionless endpoint frequency ratio `1+z`; its vertex value is
`Z0 = lim (1+z)`. Citations:

* `gr/FINITE_DISTANCE_THEOREM.md:7` — "`Z(s,n)=1+z=u.K`".
* `gr/OPTICAL_THEOREMS.md:22` — `Z(n)=lim_{d_A↓0}(1+z(d_A,n))`; `:40` `Z(n)=u(p)·K(p,n)`;
  `:44` `1+z(ℓ,n)=u(x(ℓ))·K(x(ℓ))` with reception denominator `o·K(p)=1`.
* `cas/COMMON_SPEC.md:16` — "Absolute vertex `Z0=lim(1+z)`".
* `statistics/NATIVE_INFERENCE_THEOREMS.md:31-33` — `Z_i = Z0+(r_i/c)H+ρ_i > 0`,
  `m_zi = Z_i - 1`, `m_μi = 5 log10[r_i Z_i²/(10 pc)]` (so `d_L = r Z²`, i.e. `(1+z)² d_A`).
* `ADDED_BOOK_INTEGRATION.md:95` — `1+z' = e^{φ_o-φ_e}(1+z)`, which
  `cas/contracts/CAS-17.json:271` writes as `Zprime=e^(phi_o-phi_e)Z`.
* Implementation consistency (not used as a definition): `htt/src/common/relativistic_kinematics.py:216-231`
  transforms `(1+z)` multiplicatively by the frequency factor `d`.

Lean: `G17A.onePlusZ ke Ue ko Uo := freq ke Ue / freq ko Uo` (emitted over observed
frequency, i.e. `Z = 1+z`), and `G17A.zOf Z := Z - 1`.

## Symbol-by-symbol recovery

| symbol | definition recovered | citation |
|---|---|---|
| signature, `U=c u`, `O=c o`, `u·u=o·o=-1` | `(-,+,+,+)`; physical velocity is `c` times unit velocity | COMMON_SPEC.md:4; OPTICAL:9; NATIVE:9; DOSSIER:10; CAS-17.json:61-62 |
| length-valued coordinates | `x0 = c t`; coordinates have length dimension | COMMON_SPEC.md:5; OPTICAL:9; NATIVE:9; CAS-17.json:65 |
| `Q`, `B` (coordinate covariant) | `Q_ab=∇_a U_b` (derivative first), `B_ab=Q_(ab)` | COMMON_SPEC.md:6; OPTICAL:31; ADDED_BOOK:73 |
| `A` | `A_b = U^a∇_a U_b` (covariant, units m s⁻²); the contravariant `A^a` is the index-raised field; the vector form `A^a=U^b∇_bU^a` is used in ADDED_BOOK:86 | OPTICAL:31-35; COMMON_SPEC.md:7; NATIVE:17 |
| `h` | `h^{ab}=g^{ab}+U^aU^b/c²` | ADDED_BOOK:87; COMMON_SPEC.md:8 |
| measured tetrad components | components on an orthonormal tetrad of the metric in use; tetrad `λ⁻¹`-rescales under `g→λ²g`; norms are declared positive Euclidean component norms | ADDED_BOOK:73; OPTICAL:35; COMMON_SPEC.md:19; CAS-17.json:67 |
| `o`, `n`, `K` | `K=-o+n`, `K²=0`, `o·K=1` (observer normalization) | OPTICAL:11-15; COMMON_SPEC.md:14; NATIVE:9; FINITE:7 |
| null affine parameter | `K=dx/ds`, `∇_K K=0`, length-valued `s≥0`, normalized by `K(0)=-o+n` | OPTICAL:17; FINITE:7; NATIVE:51 |
| `I = Z0` | `I(n)=g(K,u)=Z0(n)=ζ0+ζ·n` | ADDED_BOOK:59-64; OPTICAL:40; NATIVE:11 |
| `β` | from `γ=-u·N`, `β²=1-γ⁻²` (C01 objects); invariant under constant scale | ADDED_BOOK:61; CAS-17.json:119,269 |
| `d_A` | source-screen area / observer solid angle; `d_A=√det J` for the vertex Jacobi matrix in a parallel screen basis | OPTICAL:17,48; FINITE:7-9 |
| local optical slope `H` | `H(n)=c ∂z/∂d_A |_0` | OPTICAL:23; COMMON_SPEC.md:16; ADDED_BOOK:69 |
| `Kc` | `‖Ropt(s)‖_op ≤ Kc` on `0≤s≤L`, length⁻², `D''=-Ropt D` | FINITE:9-11; NATIVE:51 |
| `M2` | `|d²Z/ds²| ≤ M2` on `0≤s≤L` (affine `s`, not area distance `r`) | FINITE:11,59-63; NATIVE:51 |
| `L` | upper end of the affine segment `0≤s≤L` | FINITE:11; NATIVE:51 |
| `η` | `η(s)=sinh(√Kc s)/(√Kc s)-1`, `η=0` if `Kc=0`; equals `CAS07M01.eta Kc s` | NATIVE:53-54; FINITE:15-18 |
| domains (5),(6) | `0<r≤L(1+ηL)`, `|ρ|≤M2 r²/[2(1-ηL)²]+|H| r ηL/[c(1-ηL)]`; and `s(1-η(s))≤r≤s(1+η(s))`, `|ρ|≤M2 s²/2+|H| s η(s)/c` | NATIVE:56-65 |
| calibration offset `κ` | common free modulus offset; `κ'=κ-5log10 a` with `r'=a r`, `H'=H/a` | NATIVE:114-119; ADDED_BOOK:79 |
| calibration unit reference | `10 pc` in the same length unit as `r` (logarithm dimensionless) | NATIVE:33-35 |
| constant scale | `g_λ=λ²g`, `u_λ=λ⁻¹u`, `o_λ=λ⁻¹o`, `n_λ=λ⁻¹n`, `K_λ=λ⁻¹K`, `r_λ=λr`; Levi-Civita connection unchanged | ADDED_BOOK:46-56 |
| constant-scale laws | `I,Z0,β` fixed; `D_A,D_L→λ`; `H→λ⁻¹H`; `B_cov→λB`; tetrad `B→λ⁻¹`; `A^a→λ⁻²A^a`; `|A|→λ⁻¹`; `Kc,M2→λ⁻²`, `L→λL` | ADDED_BOOK:58-77; NATIVE:119; CAS-17.json:269-270 |
| general conformal | `g'=e^{2φ}g`, `U'=e^{-φ}U`, `A'^a=e^{-2φ}(A^a+c²h^{ab}∇_bφ)` | ADDED_BOOK:83-88; CAS-17.json:120,271 |
| null/observer rescaling for redshift | same eikonal covector; `ν'=e^{-φ}ν` at each endpoint; `1+z'=e^{φ_o-φ_e}(1+z)` | ADDED_BOOK:92-96 |
| Riemann convention | `R^a_bcd=∂_cΓ^a_db-∂_dΓ^a_cb+Γ^a_ceΓ^e_db-Γ^a_deΓ^e_cb` | COMMON_SPEC.md:23 |
| exclusions / singular loci | general-conformal same-calibrated-data excluded; `CONF-GRAD`, `SCALE-FIXEDBOUND`, `SCALE-INF` | CAS-17.json:78-88 |

## Recovered items that remain modelling inputs (not invented, not targets)

These are inputs the sources themselves declare as assumptions; they enter the
Lean statements as explicit hypotheses/structure fields, never as the
transformation being proved:

1. The measured endpoint frequency is `ν = -k_a U^a/(2π)` for the eikonal
   covector `k_a` (rad per length) and physical velocity `U`. The source fixes the
   endpoint convention "same eikonal covector" (ADDED_BOOK:92); the frequency
   definition itself is the standard contraction used by OPTICAL:44.
2. The `g_λ` parallel orthonormal screen frame along the ray is `λ⁻¹` times the
   `g` one at the same event (orthonormality is proved; parallelism follows from
   the unchanged connection but is not re-derived as an ODE statement here).
3. The identification of the G01-A frame-level `JacobiPremises.R` operator with
   the tidal matrix `g(E_A, R(E_B,K)K)` is a typed bridge hypothesis
   (`tidal_op_scale`), as in G01-A where `ScreenFrameData` is a recovered source
   definition not derived from a manifold.
4. `D_L` scaling requires the reciprocity/transparency conditions
   (COMMON_SPEC.md:18; NATIVE:35); only `d_L = r Z²` algebra is used.

No physical input needed by C02/C03 is absent from the repository.

## Reused reviewed Lean sources (compiled unchanged into `raw/imports`)

| module | path | source SHA-256 | review |
|---|---|---|---|
| `C01` (CAS17-C01) | `CAS-17/c01_gram_tilt_bridge_v1_20261010/lean/C01.lean` | recorded in `raw/compile_01_imp_c01.json` | REVIEW.md: PASS |
| `CAS07M05Accepted` | copy of `CAS-07/determinant_distance_bridge_v1_20261007/lean/Main.lean` | `0e10bfac397e7f5e5d67166425f0cda6273c2ecdafdb561396a9503a954704af` | accepted CAS-07 M05 |
| `G01AJacobiVertex` (G01-A, frame-level PARTIAL) | `CAS-01/g01a_jacobi_vertex_taylor_v1_20261014/lean/G01AJacobiVertex.lean` | `6c1f7a6614fbe1fae71072d8dde31596110fe93f3e7c33462a0458d5285cde57` | REVIEW.md: PASS_WITH_NOTES (frame level) |

CAS17-C04 (`PassiveTensorBridge`) is not imported: no C02/C03 statement uses a
passive coordinate change. P03-A (`VelocityJetDecomposition`) and P06-A
(`P06AOptics`, `P06ASphere`) are not imported: they fix `c=1` and a fixed
Minkowski frame, whereas C02/C03 need a general chart metric field and its
derivatives; their index convention (`U=c u`, derivative-first `Q`) is the same
one recovered above from COMMON_SPEC.md:4-7.
