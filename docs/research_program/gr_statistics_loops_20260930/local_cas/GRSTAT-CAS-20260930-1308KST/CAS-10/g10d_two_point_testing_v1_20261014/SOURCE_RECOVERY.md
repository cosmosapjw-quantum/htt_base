# G10-D source recovery

Written in the resumed run (2026-10-14). The first run was cut off by a rate limit after
`FROZEN_TARGETS.md` and compile receipts 01–12 had been written; this file had not been written
yet although `FROZEN_TARGETS.md` refers to it. Its content records the sources the frozen targets
were taken from; it does not change any frozen target.

## Card

* `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip :: HTT_ALL_OBLIGATIONS_20261011/tasks/G10-D.json`
  (read with `unzip -p`). Relevant fields: `scope_original` (two-point probability conclusion of
  the original cutout / morphology non-identifiability), `existing_reuse` (G10-B laws / KL, G10-C
  smooth fields), `lean_steps` 1–4, `acceptance` 1–4, `pitfalls` (no KL constant without a testing
  bound; no change of loss/target metric), `source_snapshot` a30d84c7….

## Original statements

Source document `docs/research_program/gr_statistics_loops_20260930/statistics/INFORMATION_LIMIT_THEOREMS.md`
(sha256 `775b7d151d894dc33e3896e9e00674a8de6e2432c7bf96ad5ee70d64f2b63b1a`).

| item | lines | used for |
|---|---|---|
| (I9) Gaussian block experiment, `d_j=(1,3,1,3,5)`, `σ_j>0` | 109-114 | M-part laws (via G10-B `obsLaw`) |
| Theorem II, equal compressed laws, powers-only tests, (I10) KL `225H²/(64σ_p²)` | 116-127 | M1, M2, M3, M4, M4e, N5 |
| Theorem III statement 1–3, (I11) `δ = min(1,Ma²)/25` | 133-145 | C1, C3, C3e, C4, C5, C7 |
| cutoff construction, `|q'|≤15/(4a)`, `|q''|≤40/(√3a²)`, mollifier on `[-a/8,a/8]` | 147-153 | reused G10-C |
| (I12) `u1 = (cosh χ, sinh χ, 0, 0)`, `χ = δ q(|x|)` | 155-160 | `u1`, C1, C1s |
| (I13) `Z_1 = cosh χ + n_x sinh χ`, `|Z_1''| ≤ e^δ/a² (40δ/√3 + 225δ²/16)` | 161-167 | C2, C4a |
| (I14) and rational certificate `e^{1/25}<25/24`, `√3>12/7`, `1147/1152` | 168-176 | C4b, C4 |
| fixed-observer remark, test congruence (not Einstein–dust) | 178 | encoding, not-claimed |
| §6 equal complete data laws when data depend only on exterior data | 184 | C3l (`obs : ExtData a → Measure Ω`) |
| Corollary (I15) confidence-set floor, union bound, `D = sinh δ ≥ δ` / `D = δ`, `max_i E_i d ≥ D/2` | 186-193 | G1–G8, C6r, C6d, C6e |

Contract `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-10.json`
(sha256 `03dd5c3c8e3d8c30cf75058b48138a5208ac5f664a51533fb5d945ffee06f43f`): lines 15-19 (owned
obligations STAT-INFO-1..5), line 43 / 113 (two-point probability bounds remain analytical
obligations), line 202 ("formalize finite algebra and two-point events").

## Reused definitions (imported unchanged; byte-identical to reviewed originals)

| module | original path | sha256 |
|---|---|---|
| CAS10C01 | `CAS-10/c01_tuple_separation_v2_20261008/lean/CAS10C01.lean` | 3cf35a9a… |
| CAS10C03 | `CAS-10/c03_block_rotation_kl_v2_20261008/lean/CAS10C03.lean` | 2ab3b8b9… |
| P12GaussianLaw | `CAS-10/g10b_gaussian_kl_v1_20261013/lean/reused/P12GaussianLaw.lean` | 5a6ce15d… |
| G10BGaussianKL | `CAS-10/g10b_gaussian_kl_v1_20261013/lean/G10BGaussianKL.lean` | 1993257d… |
| G10CSmoothCutoff | `CAS-10/g10c_smooth_cutoff_v1_20261013/lean/G10CSmoothCutoff.lean` | 1cbf4738… |

Lemmas relied on (file:line in the reused copies under `lean/reused/`):

* G10BGaussianKL: `obsLaw` 154, `powers` 157, `measurable_powers` 182, `blockDim` 377, `Obs` 379,
  `ofMean` 390, `compressed_laws_equal` 447, `powersOnly_tests_agree` 455, `full_kl_eq` 477,
  `full_laws_ne` 514.
* CAS10C03: `p` 31 (`![15H/8,0,0]`), `pPrime` 32 (`![0,15H/8,0]`), `first` 55, `second` 58.
* G10CSmoothCutoff: `IsMollifier` 497, `exists_mollifier` 501, `smoothCutoff` 511,
  `smoothCutoff_contDiff` 544, `smoothCutoff_plateau` 550, `smoothCutoff_support` 565,
  `smoothCutoff_mem` 580, `smoothCutoff_deriv_bound` 613, `smoothCutoff_deriv2_bound` 619,
  `radial_contDiff` 649, `radial_plateau` 664, `radial_ray` 672.

## Mathlib at the pin (fabf563a7c95a166b8d7b6efca11c8b4dc9d911f)

* Present and used: `InformationTheory.klDiv`, `klDiv_of_not_ac`
  (`Mathlib/InformationTheory/KullbackLeibler/Basic.lean:68`), `klDiv_eq_lintegral_klFun_of_ac`
  (:138), `mul_log_le_klDiv` (:360); `ProbabilityTheory.minimaxRisk`
  (`Mathlib/Probability/Decision/Risk/Defs.lean:60`, infimum over Markov kernels of the maximal risk);
  `Metric.ediam`, `Metric.diam_univ_of_noncompact`, `Metric.ediam_univ_of_noncompact`;
  `contDiff_infty_iff_deriv` (`Mathlib/Analysis/Calculus/ContDiff/Deriv.lean:103`).
* Absent: no Bretagnolle–Huber and no Pinsker inequality (`grep -rli "bretagnolle\|pinsker" Mathlib`
  returns nothing). The needed Bretagnolle–Huber special case is self-proved in-module
  (K1–K4: KL additivity over a two-cell partition, two-cell data processing, Bernoulli BH via
  concavity of `log` and Cauchy–Schwarz, then BH on the actual laws).

## Not recoverable / not needed

* The source fixes no estimation metric for the morphology pair (Theorem II is a testing
  statement). The generic M2/M3 targets therefore quantify over every pseudo-metric target space;
  the slope dipole with Euclidean distance is a labelled worked instance (M2s, M4e), not a
  source-mandated metric.
* PR #493/#494/#495 (card `source_paths`) were not re-read in this resumed run; nothing in the
  frozen targets depends on content found only there. Unlock: if a reviewer finds a stricter
  original loss/target metric in those PRs, M2/M3/M4e must be re-checked against it.
