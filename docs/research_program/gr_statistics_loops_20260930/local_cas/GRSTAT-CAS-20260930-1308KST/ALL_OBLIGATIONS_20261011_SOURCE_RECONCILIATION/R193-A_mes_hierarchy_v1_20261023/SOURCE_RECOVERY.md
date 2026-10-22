# R193-A source recovery — MES primary source, erratum, covariant hierarchy

Task card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip:HTT_ALL_OBLIGATIONS_20261011/tasks/R193-A.json`
(package sha256 `2d0b6da9…af6f`; extracted copy `raw/card_R193-A.json`, sha256 `ace3eddc…6efb`).
Repository HEAD at recovery time: `d256ed4669b1ded62fa0db606929af108160ccf6` (read-only; no git state change).
Scientific admission: **HOLD** (nothing here admits a physical claim).

## 1. Card sources (as named by the card)

| file | lines | sha256 | content used |
|---|---|---|---|
| `docs/codex_handoff/pr_backlog.yaml` | 6150–6233 | `5cf688f2…b935` | PR-193 target: re-derive geodesic/non-geodesic coefficient surfaces from MES raw inequalities; ε1,intrinsic free; DoD: "primary source/erratum과 coefficient가 불일치하거나 hierarchy ordering이 물리적 필요조건으로 유도되지 않으면 해당 admissibility claim 실패"; kill: OCR/transcription unresolved; forbidden: print-only coefficient as anchor, "ε1=0 unique by hierarchy" |
| `docs/codex_handoff/remaining_pr_crosswalk.csv` | 27 | `92b7332a…b496` | PR-193 PARTIAL_REMAINDER: "MES attribution and geodesic source branch exist"; remainder "full covariant hierarchy intrinsic-dipole surface and non-geodesic closure" |
| `docs/codex_handoff/REMAINING_PR_EXECUTION_PLAN_KO.md` | 138–142, 176–178 | `fdffc914…924f` | reuse finite witnesses/source attribution; "non-geodesic MES" requires general treatment; residual image is not an origin-centred MES anchor |

## 2. Primary sources (archived in repo, SHA-pinned)

Directory `docs/audits/mes_primary_sources/` (`SHA256.txt` there; re-hashed now, all match):

| tag | reference | local file | sha256 |
|---|---|---|---|
| MESa | Maartens, Ellis, Stoeger, PRD 51, 1525 (1995), arXiv:astro-ph/9501016v1 | `mesa_astro-ph_9501016_layout.txt` | `4ffe1173…a6c` |
| MESa (plain extraction) | same | `mesa_astro-ph_9501016_PRD51_1525.txt` | `d500ffee…217e` |
| companion | MES, "Anisotropy and inhomogeneity of the universe from ΔT/T", arXiv:astro-ph/9510126 | `companion_astro-ph_9510126_layout.txt` | `95f30a3c…bdab` |
| SAG 1997 + erratum | Stoeger, Araujo, Gebbie, ApJ 476, 435 (1997); erratum (ApJ Sept 1999) incorporated in arXiv:astro-ph/9904346 TeX | `sag1997_astro-ph_9904346_ApJ476_435.tex` | `00bb2c7c…370e` |
| MESb | MES, PRD 51, 5942 (1995) | **not in repo (print-only)** | — |

Provenance dossiers: `docs/audits/mes_primary_sources/PROVENANCE_M4.md`, `PROVENANCE_M4b.md`;
`docs/research_program/mes_verified_checkpoints_20260928/I1/recovery/research/readable_research/MES_GENERALIZED_TENSOR_R2/sources_agent/MES_BOUND_SOURCE_REVIEW.md` (R2 source review).

### 2.1 MESa conventions (layout file line numbers)

- c = 1, signature (−,+,+,+), h_ab = g_ab + u_a u_b, Θ = 3H > 0, |Q| = (Q_{a..b}Q^{a..b})^{1/2} (full contraction) — lines 117–131.
- Matter = non-interacting dust ⇒ geodesic u̇_a = 0 — line 134, eq (11) line 215.
- Moment normalisations: q_a = (4π/3)∫E³F_a (5) l.158; π_ab = (8π/15)∫E³F_ab (6) l.162; ξ_abc = (8π/35)∫E³F_abc (7) l.168.
- Linearised Boltzmann harmonics (8)–(10), ll.187–196 (collision-free, **zero acceleration**): divergence couplings 1/3, 2/5, 3/7; gradient coupling 1 on E∇̂_<a F_b>.
- (12) μ̇ + (4/3)Θμ + ∇̂^a q_a ≃ 0 l.218; (13) q̇_a + (4/3)Θq_a + (1/3)∇̂_aμ + ∇̂^bπ_ba ≃ 0 l.220;
  (14) π̇_ab + (4/3)Θπ_ab + (8/15)μσ_ab + 2∇̂_(a q_b) − (2/3)h_ab∇̂^c q_c + ∇̂^c ξ_cab ≃ 0 ll.222–225.
- (26) ∇̂_aΨ̇ ≃ (∇̂_aΨ)˙ + (1/3)Θ∇̂_aΨ (zero acceleration) l.280; (27) ∇̂_[a∇̂_b]ψ = −ψ̇ ω_ab (exact) l.286.
- (36) Ṫ/T = −Ṡ/S + O[1] l.417; (40) τ_{A_L} ≃ (1/4μ)4π∫E³F_{A_L} l.446; (41) τ_a ≃ 3q_a/4μ, τ_ab ≃ 15π_ab/8μ, τ_abc ≃ 35ξ_abc/8μ l.452.
- B1 (42) |τ_{A_L}| < ε_L l.482; B2 (43) |τ̇| < ε*_L Θ, … l.487; B3 (44)/(45) |∇̂τ| < ε'_L Θ, |∇̂∇̂τ| < ε''_L Θ², |(∇̂τ)˙| < ε'*_L Θ², … ll.494–509.
- (46) |q| < (4/3)με1, |π| < (8/15)με2, |ξ| < (8/35)με3 l.524; (47)–(49) derivative limits ll.531–539.
- **(51)** |σ_ab|/Θ < (8/3)ε2 + ε*2 + 5ε'1 + (9/7)ε'3 l.565; **(52)** |ω_ab|/Θ < 9ε'1 + 3ε'*1 + (6/5)ε''2 l.574.
- C1 (spatial ≤ temporal) l.657; C2 (Θε*_L ≃ ε_L/t_R, Θt_R ≃ 3 via (36)) ll.664–668; (57) t_R = T/|Ṫ| l.649.
- **(59)** |σ|/Θ < (5/3)ε1 + 3ε2 + (3/7)ε3 l.681; **(60)** |ω|/Θ < (10/3)ε1 + (2/15)ε2 l.685.

### 2.2 Companion and SAG

- companion l.167–171: "(MESb, Eq. (24))" raw shear bound identical to MESa (51); eq (7) l.207 = MESa (59); l.212 "remaining limits are given in MESb (Eq. (30)–(36))"; eq (8) l.232 reduced σ, ω limits with ε1 → 0.
- SAG TeX l.150–157: eq (3) = MESa (59), eq (4) = MESa (60) (clean LaTeX: `\frac{5}{3}`, `\frac{3}{7}`, `\frac{10}{3}`, `\frac{2}{15}`); eq (12) l.280 ε1 = 0.
- **SAG erratum** (TeX header l.1–4, markers l.401/408/415/431, note l.604–611): corrected eq (17)
  ⟨τ_{A_ℓ}τ^{A_ℓ}⟩ = (2ℓ+1)(2ℓ)!/(2^ℓ(ℓ!)²) ΔT_ℓ², hence (18) |τ_ab|² = 7.5 Q²_rms, (19) |τ_abc|² = 17.5 O²_rms, (20)–(27) revised.
  The **pre-erratum printed form of eq (17) is not in the repository** (the archived TeX already contains the corrections).

## 3. Transcription points checked against the source text

| point | extraction | adjudication | basis |
|---|---|---|---|
| MESa (51) leading term | layout "38 ǫ2" (fraction order ambiguous: layout prints both num-first "10 3" and den-first "73") | **8/3** | (i) C1/C2 reduction to triple-sourced (59) forces c+1/3 = 3 ⇒ c = 8/3 (3/8 fails); (ii) independent derivation route (this packet, Lean S1) produces 4/3+4/3 = 8/3 |
| MESa (51) octopole term | layout "97 ǫ′3" | **9/7** | (i) c/3 = 3/7 ⇒ c = 9/7 (7/9 fails); (ii) Lean S1 route: (∇ξ coupling 1)·(8/35)/(8/15)·(slice-wise contraction factor 3) = 9/7; the same factor-3 convention reproduces the 72/5 ε'2 coefficient of MESa (50) |
| MESa (52) ε''2 term | "65 ǫ′′2" | **6/5** printed (reduction c/9 = 2/15 ⇒ 6/5) | printed value consistent with (60) and SAG (4); **derivation gap**, see §5 |
| MESa (14) ∇q coupling | "2∇̂(a qb) − 2/3 h_ab ∇̂·q" (no "5"/"15" glyph in either extraction) | printed **2** | **source-internal inconsistency**: (10) coefficient 1 with normalisations (5),(6) gives (8π/15)/(4π/3) = 2/5 (Lean `eq14_grad_coupling`); flat free-streaming check ∫e_m e_k e_<i e_j> = (4π/15)(…) also gives 2/5 (prose check only). MESa (51)'s "5ε'1" is reproduced from the printed 2; the Boltzmann-consistent 2/5 gives coefficient 1 ≤ 5, so (51) stays a valid (conservative) bound under either reading |

Originals (PDF / arXiv TeX of MESa and companion) are **not** in the repository (search of the filesystem
for `*9501016*`/`*9510126*` returned only the archived text files above); the glyph-level OCR question
for (14) can therefore not be settled against the typeset original here. Per acceptance, only that
coefficient branch is marked; both readings are carried in Lean as the parameter `kq`.

## 4. Existing reuse (cited unchanged; nothing imported into Lean)

- MES attribution surface: `htt/src/common/revival_mes_attribution.py` (sha256 `a0bad4d4…d25d`) l.16–31 (frozen geodesic W2 anchor 3.3789…e-13; geodesic SAG branch σ=(5/3,3,3/7), ω=(10/3,2/15,0); unsourced NG ω (3/4,2,2/7)), l.51–53 ε1_crit = (43/25)ε2 + (9/35)ε3, l.78–82 ε1=0 is a branch choice.
- Geodesic source branch / authority: `htt/src/common/mes_theorem_authority.py` (sha256 `d149d859…87af8`) l.86–239 (MES_G_SIGMA/OMEGA/ACCEL VERIFIED; MES_NG_* UNVERIFIED_PRINT_ONLY), l.490–504 strict hierarchy B_σ > B_ω > 0, l.68–83 conventions (W² = ω_abω^ab/(6H²), ceiling (3/2)B²).
- In-repo C1/C2 reduction lineage: `htt/obsstat/egs3_mes_rederivation.py` (sha256 `8051e61e…ec6f`) l.75–82 raw (51)/(52) tables.
- I1/I2 materialized source: `docs/research_program/mes_verified_checkpoints_20260928/I2/HTT_MES_I2_REPORT_20260928_KO.md` (π̇ = −(8/15)ρσ in radiation-only Bianchi I: the same (14) structure; snapshot-only data cannot bound absolute shear) and the R2 source review cited above (norm translation (2l+1)!!/l!).
- No reviewed Lean module covers this content. R191-A (`RotatingRestBundleGauss.lean`) is optional reuse per the card and is **not** needed: no step here uses the rotating Gauss identity (only MESa (27), taken as a source relation). Therefore `raw/imports` contains only this packet's own build products.

## 5. Independent tensor derivation (summary; Lean is the record)

Setting: one event, orthonormal triad of the u^a rest space (h_ab = δ_ab), rest-space tensors typed as
`EuclideanSpace ℝ (Fin 3)^k` with the Frobenius norm = MESa |·|. Only the linearised ("≃") relations
are used; O[2] remainders are not controlled.

- **Shear (51).** From (14): (8/15)μσ = −[π̇ + (4/3)Θπ + k_q STF(∇̂q) + ∇̂^cξ_cab], π = (8/15)μτ_2,
  π̇ = (8/15)(μ̇^{(0)}τ_2 + μτ̇_2), μ̇^{(0)} = −(4/3)Θμ, q = (4/3)μτ_1, ξ = (8/35)μτ_3.
  Triangle inequality *without* using the cancellation π̇ + (4/3)Θπ = (8/15)μτ̇_2 gives
  (8/3)ε2 + ε*2 + (k_q·(4/3)/(8/15))ε'1 + (κ·(8/35)/(8/15))ε'3 with κ the contraction factor.
  k_q = 2 (printed) and κ = 3 (slice-wise triangle) reproduce **(8/3, 1, 5, 9/7) exactly**. Using the
  cancellation and the Cauchy–Schwarz factor κ = √3 gives the sharper ε*2 + (5/2)k_q ε'1 + (3√3/7)ε'3.
- **Vorticity (52).** From (27): μ̇ω = −∇̂_[a∇̂_b]μ; ∇̂_b of (13); (26) for ∇̂q̇. No-cancellation triangle
  gives 9ε'1 + 3ε'*1 exactly (source-equal), and (9/4)(8/15)κ ε''2 = (6/5)κ ε''2 for the π term.
  The printed 6/5 needs κ = 1, i.e. ‖∇̂_b∇̂^cπ_ac‖ ≤ ‖∇̂∇̂π‖, which is **false**: the contraction has
  operator norm √3 on unconstrained tensors, √(5/3) on tensors STF in (a,d), √(5/4) after additionally
  imposing symmetry in the two derivative indices (numerical probes `raw/probes/opnorm.out`).
  A formal counter-witness (Lean W3) satisfies every relation used to derive (52), with
  |ω|/Θ > 9ε'1 + 3ε'*1 + (6/5)ε''2. Valid replacement: (6√3/5)ε''2 (Lean W1/W2).
- **Non-geodesic terms.** With u̇ ≠ 0 the dipole harmonic gains −E²u̇_a ∂F/∂E, so (13) gains
  +(4/3)μu̇_a (coefficient 4·κ_1/κ_0 = 4/3, Lean `accel_coupling`); (14) gains nothing at O[1]
  (u̇ multiplies the O[1] dipole); (26) changes only for scalars (−ψ̇u̇_a). Consequences: (51) is
  congruence-independent; (52) acquires +3·|∇̂_[a u̇_b]|/Θ²; the radiation hierarchy bounds only
  ∇̂μ + 4μu̇, so no acceleration ceiling follows from multipole bounds alone (Lean A2).
- **Erratum.** κ_L = L!/(2L+1)!! underlies MESa (5)–(7), (41), (46) and the corrected SAG (17):
  (2L+1)(2L)!/(2^L(L!)²) = (2L+1)!!/L! = 1/κ_L for all L (Lean `sagFactor_eq`), 7.5 and 17.5 at L=2,3.
  The angular identity ⟨e^{<A_L>}e_{<B_L>}⟩ = κ_L Δ itself is **not** derived in Lean (Mathlib has no
  sphere-moment theory used here); it enters only as the shared constant of both sources.

## 6. Missing items (exact) and unlock conditions

| missing | searched | unlock |
|---|---|---|
| MESb (PRD 51, 5942) full text (non-geodesic ω/A coefficients (3/4,2,2/7), (3/4,1,3/14)) | repo tree, `docs/audits/mes_primary_sources`, mes_verified_checkpoints, git log (REV-R155/R166/R190 commits `b9d3ce0b1`, `a830a2a3c`, `135a0e341`) | archived PDF of PRD 51 5942 with sha256 |
| typeset original of MESa (14) (glyph "2" vs "2/5") | same; filesystem search for `*9501016*` | arXiv source TeX or journal PDF of astro-ph/9501016 |
| pre-erratum SAG eq (17) | archived TeX contains corrected form only | ApJ 476, 435 printed page |
| derivation of the angular moment constant κ_L | Mathlib (no spherical-moment library located) | Lean proof of the sphere moment identity, or CAS axis |
