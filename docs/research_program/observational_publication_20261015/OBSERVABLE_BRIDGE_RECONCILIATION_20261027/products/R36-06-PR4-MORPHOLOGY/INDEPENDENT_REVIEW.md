# Independent Review: PR-R36-06-PR4-MORPHOLOGY

**Task ID**: `R36-06-PR4-MORPHOLOGY`  
**Review Mode**: Independent fresh-context verification of processed-map morphology null ensemble  
**Claim Tier**: `C0_DIAGNOSTIC_ONLY`  
**Verdict**: **PASS** (Diagnostic-only null qualification; no native Boltzmann solver or Bianchi family identification)

## 1. Scope & Verification

Independent verification of the aggregated 100 Planck PR4 (NPIPE) Commander Monte Carlo simulation outputs (`mc_0300` to `mc_0399`) against the observed full-mission Commander polarization map (`observed.json`):
- All 100 simulation records and observed record in `/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual/analysis/` verified present, non-corrupt, and bound to `CONTRACT_SHA` (`fa08a55c...`).
- Exact empirical p-values verified via independent mathematical calculation:
  - $p(J_{234} \ge \mathrm{obs}) = (43 + 1)/101 = 0.43564$ ($k=43$)
  - $p(|J_{234}| \ge |\mathrm{obs}|) = (74 + 1)/101 = 0.74257$ ($k=74$)
  - $p(\mathrm{alignment}_{23}^2 \ge \mathrm{obs}) = (22 + 1)/101 = 0.22772$ ($k=22$)
- Clopper-Pearson 95% interval half-width on $|J_{234}|$ empirical frequency is $0.08996 \le 0.105$, satisfying the registered simulation accuracy bound.
- Low-$\ell$ morphology features ($J_{234}$, alignment) are consistent with the processed Commander null ensemble within Monte Carlo resolution.

## 2. Test Verification

- `test_pr4_commander_morphology.py`: 9/9 tests PASSED (polarization header roles, unit rejections, NaN handling, interval bounds, axis abstention, aggregate JSON integrity, result consistency, and plot existence).
- `test_pr4_observed_pilot.py`: 3/3 tests PASSED (mask mapping, linear coadds, order/falsification checks).

## 3. Claim Firewall Compliance

- **No Overclaim**: Result is strictly diagnostic ($C_0$). No assertion of Bianchi geometry detection, family identification, or model-independent truth certificates.
- Transfer source is explicitly declared as none (direct processed observational data and matched pipeline simulations; no Bianchi transfer or beam deconvolution).
- All generated plots (`null_distribution_histograms.pdf`, `null_distribution_histograms.png`) feature appropriate scientific caveats and claim ceilings.

## 4. Reviewed Artifact Hashes

```json
{
  "COMMANDER_MC100_AGGREGATE.json": "7d267f0b1fc4d5d48a4a40b166bfa3498e890a5e37b2df7c33173644da100814",
  "null_distribution_histograms.pdf": "e2ba0471430156a7553877e2e24dbea3c8a4a6ce814b97b5e4989f5a337f5303",
  "null_distribution_histograms.png": "87bf9e1ddb2dd8acfca67c4b843cc364711e60160f5a709757a60b71e653d1d6",
  "RESULT.json": "a07d8ed5999f76a96e8cce9d47f0ee79a4d53265f1b549d3ec023b04fd7f77e5",
  "REPORT_DELTA.md": "0935500c8c672159c24f9f3a35e4010281db0c10dddb17a5bd1765d9a193392f",
  "aggregate_mc_morphology.py": "7316f0cb1549b70cf1639f735c4d2043dff6bcefee3d891caf8e16abfd93edd2",
  "ARTIFACT_MANIFEST.json": "updated_with_review",
  "test_pr4_commander_morphology.py": "b8731eaaaca6e16fbd89ef50f68a1839a4bacb6f4d01246368eb2ec916c19d7e"
}
```
