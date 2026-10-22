# G11-D source recovery (GR-CAS-11: uncertain moment matching and measured entropy inputs)

Written 2026-10-14 before `FROZEN_TARGETS.md` and before any proof compile. Paths are relative to the
repository root unless absolute.

* Card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip:HTT_ALL_OBLIGATIONS_20261011/tasks/G11-D.json`
  (source_snapshot `a30d84c7918b54238a48fa62e2ef482f7e6d36fa`; status PLANNED_NOT_EXECUTED; requires G11-C).
* `S` = `docs/research_program/gr_statistics_loops_20260930/supplements/TEFF_POSITIVE_BRIDGE.md`,
  sha256 `f04d96fe4b7dbee5fc946e10863d602c46399ca15723226ce6b63d4ab53ff21b` (equals the CAS-11 contract
  `research_provenance_hashes` entry, `C` raw line 29).
* `C` = `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-11.json`,
  sha256 `6588ac42ca6724e58b2f673b0ee2c3234b7a3a6ab1df35a6d1f942c03f860025` (raw line numbers).
* `D` = `docs/research_program/gr_statistics_loops_20260930/DECISIONS.json`, sha256 `a05b30535a63c9b83f449042dfd767c673f1f16f232a1e7493027e011bcd8c6c`.
* `R` = `docs/research_program/gr_statistics_loops_20260930/reviews/POSITIVE_EXTENSION_DECISION.json`, sha256
  `8d2a2f4d8872638a9714d703aa6c676fa77e97b27b9e56ec27c66b508fffff9e`; `Rmd` = same stem `.md`, sha256
  `d2d2f02ab78a6c21799148f3d7591157f9720a84b2e10ee7303fac946d642a99`.
* `L` = `docs/research_program/gr_statistics_loops_20260930/supplements/TEFF_CLAIMS.json`, sha256
  `9654e73ecab0aeaca12009eb6f81aa860e27131daca2d77e19d7fdfe8309f541`.

## 1. Recovered statements (verbatim gist with location)

| Item | Source | Lean (this unit, `G11D`) |
|---|---|---|
| Uncertain matching: for every coefficient vector a, \|ΔO_K\| ≤ √(2ε)‖K − a·φ‖_W + \|a·Δm\| (A6) | S:108-114 | D1 split identity + D2 composite bound (no matching hypothesis) |
| "A simultaneous confidence set for Δm supplies its support function in the final term. This separates deterministic kinetic error from measurement uncertainty." | S:116 | D2 (deterministic, Δm ∈ S ⇒ bound with σ_S) and D5 (coverage, separate) |
| A6 sign correction: printed form multiplied instead of added; corrected to a SUM of two terms "with different sources" | R:385-390 (POS-F01), Rmd:25 | D2 uses the sum; D4 negative control shows the support term cannot be dropped |
| Δm = moment mismatch of δ = f − g on retained scores φ_a (A1 with matching relaxed) | S:41-46 (A1 defines ∫φ_aδ dν = 0; A6 relaxes it) | `dm μ φ f g a = ∫ φ_a (f − g) dμ` |
| ‖K − a·φ‖_W = L²(W dν) norm | S:53, S:58 | `‖hk.toLp k − Σ c_a • (hφ a).toLp (φ a)‖` in `Lp ℝ 2 (wmeas μ W)`; D1c identifies its square with ∫ W (k − Σ c φ)² dμ |
| exact-matching bound (A3)/(A4) is the special case Δm = 0 | card existing_reuse; S:55-74 | D2f via reviewed `G11C.single_kernel_dist_bound`, `G11C.weighted_residual_ellipsoid` |
| joint residual set must not be replaced by independent per-channel bars ("would discard its shared constraints") | S:143 | D2d/D2e joint form: e − BΔm in the (A4) ellipsoid; support term at Bᵀa |
| acquisition: "retained moments and calibration; a valid occupation/tail envelope; an independently certified ε for the unknown shape or total divergence; and the actual channel kernels. Retained moments or the entropy of a fitted reference alone do not certify ε. Multi-frequency spectral constraints plus an explicit uncertainty class can supply it." | S:104 | D4: typed inputs; negative control `eps_not_from_moments`; application status INPUT_REQUIRED (§3) |
| contract exclusion "No epsilon from fittedentropy alone" | C:70 | D4 negative control |
| contract singular locus "ENT-MISMATCH add momenterror" | C:76, C:95, C:111 | D2 (the added term is the support function of the declared moment-error set) |
| contract assumption "D_H(f\|\|g)<=epsilon; exact retained moments" (the G11-C regime) | C:46, C:61, C:82 | relaxed here only through an explicit Δm ∈ S hypothesis |
| "Number refinement decreases the true nested divergence by II (29)–(31), and enlarging V reduces the distance term. The two improvements may be combined only when one common envelope is valid and the divergence bounds are actually available." | S:106 | D3a-b (span monotonicity, distance decrease), D3c (combination with the common envelope and the refined budget as EXPLICIT premises), D3d (discharge of the refined budget from reviewed `G11A.nested_budget` under its own exact-matching hypotheses) |
| A5 photon envelope: 0 ≤ f,g ≤ F_b(E) = 1/(e^{bE} − 1), b > 0, W = F_b(1+F_b) | S:93-98; D:537-555 (TEFF-A4 conditions "fine state AND reference satisfy the envelope", "b>0 is independently certified"; limit "not inferred from bolometric CMB data alone") | D4a (general ξ ≥ 0 upper-envelope ⇒ (A2)), D4c (Planck instance on ν) |
| "T_max is additional prior information, not inferred from bolometric energy alone" | S:102 | b > 0 is an input of D4c, never derived |
| Prop. B moment uncertainties \|Δm₃\| ≤ d₃, \|Δm₄\| ≤ d₄ add \|c₃\|d₃ + \|c₄\|d₄ (per-moment box) | S:220 | D2c box support function Σ \|c_a\| r_a (shape reused for A6; Prop. B itself not formalised here) |

Probabilistic/interval hypotheses are NOT stated in the source beyond "simultaneous confidence set" (S:116)
and "independently certified ε" (S:104). Their typed form in this unit (frozen in `FROZEN_TARGETS.md` §D5) is:
the true state f is fixed; the reference g(ω), the entropy upper bound ε̂(ω) and the moment set S(ω) may
depend on the measurement outcome ω ∈ Ω; the three failure events (envelope, entropy budget, moment
coverage) have declared outer-measure bounds α_W, α_ε, α_m under a measure P on Ω; no independence and no
measurability are assumed; combination is by the union bound only (no double counting of the same
outcome, no product of coverages).

## 2. Reused accepted Lean sources (imported unchanged; recompiled from their original paths into `raw/imports`)

| Module | Path | sha256 | Status record |
|---|---|---|---|
| `BregmanThreePoint` | `.../CAS-11/c01_bregman_three_point_v2_20261008/lean/BregmanThreePoint.lean` | `12f3dd682db93f0966fd3547f10f25eb4fca9e8506ff58fc7c1ba6ac7cf9975c` | C01 v2 (dependency of G11-A) |
| `G11AIntegralBregman` | `.../CAS-11/g11a_integral_bregman_v1_20261013/lean/G11AIntegralBregman.lean` | `85993ce761d3d5546e362ec3debd765617da1cfb542675c6da2aea3e85b11e9a` | G11-A FORMALLY_CHECKED_SCOPED |
| `G11AGuarded` | `.../CAS-11/g11a_integral_bregman_v1_20261013/lean/G11AGuarded.lean` | `92758d9a0be6ba596461eddb322dd49f397d067ca52b5fe8e656aded10752b77` | idem (`finite_budget_stat`) |
| `G11BHessianEnvelope` | `.../CAS-11/g11b_hessian_envelope_energy_v1_20261013/lean/G11BHessianEnvelope.lean` | `ba1bc644a2b13ac82fff23b5c66645efa596ef72f6e132da2fd76a018be68f27` | G11-B FORMALLY_CHECKED_SCOPED |
| `FiniteGram` (`CAS11C02`) | `docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C02-20260930T090559Z/lean/FiniteGram.lean` | `af91ec609dbd79746f148e67c40cbe39eb0405ea390432b44eb1102918468ffc` | CAS11-C02 CAS_4AXIS_PASS |
| `WeightedProjection` (`CAS11C03`) | `docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C03-20261001T020800Z/lean/WeightedProjection.lean` | `94f8b2139782f21f0b1455079d018a831bb357055b0029c2164512eca7df29da` | CAS11-C03 CAS_4AXIS_PASS |
| `G11CWeightedEllipsoid` | `.../CAS-11/g11c_weighted_residual_ellipsoid_v1_20261014/lean/G11CWeightedEllipsoid.lean` | `732645ad657b32fd32b2c8bb58332f70d0b3c48e1eebab581bdf1493ab976081` | G11-C FORMALLY_CHECKED_SCOPED, review PASS_WITH_NOTES (`RETURN.json`, `REVIEW.md`); committed in `0b0003ff` |

All seven hashes were recomputed on 2026-10-14 and equal the G11-C SOURCE_RECOVERY / RETURN values.
Compile receipts: `raw/compile_01..07_dep_*.json` (all exit 0).

## 3. Items that are NOT recoverable from the repository (application inputs, not mathematics)

| Missing item | Where searched | Unlock condition |
|---|---|---|
| an independently certified ε (or ε̂ with a stated coverage α_ε) for an actual CMB/kinetic pair (f, g) | S:104, D (TEFF-A1/A4), L, `reviews/`, `evidence/`, grep of `docs/research_program` and `htt/` for "certified eps"/"entropy budget" | a multi-frequency spectral acquisition with an explicit uncertainty class producing ε̂ and its coverage |
| a simultaneous confidence set S for the actual retained-moment mismatch Δm with its coverage α_m | S:116; none in repository | calibrated retained-moment measurements with a declared simultaneous confidence region |
| an independently certified envelope parameter b (or T_max) and the fugacity/η ≤ 0 check | S:102, D:546 | prior information on T_max and the reference fugacity |
| the actual channel kernels K_j and retained scores φ_a with their L²(W dν) membership | S:104 | declared instrument/channel kernels |

Per card pitfall: only the application is INPUT_REQUIRED; the mathematical targets below do not depend on these
inputs and are proved for arbitrary declared inputs.
