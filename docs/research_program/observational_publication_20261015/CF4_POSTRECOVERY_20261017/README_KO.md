# CF4 원본 수집 후 연구 인계

기준: user-local CF4 55,877 + 38,053 + 38,053 row SHA 원본 검증, six-paper 14/42, physical blockers 7 유지.

## 설치 및 local full source audit

```bash
cd /mnt/extdrive/workdir
unzip -q HTT_CF4_POSTRECOVERY_SOURCE_RESEARCH_20261017.zip -d /mnt/extdrive/workdir
cd /mnt/extdrive/workdir/htt_cf4_postrecovery_20261017
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/verify_manifest.py
python -m pytest -q tests
ROOT=/mnt/extdrive/workdir/htt_open_data
python src/cf4_raw_audit.py --root "$ROOT" --selected-npz data/selected_source_observables.npz
python src/planck_mask_gate.py --root "$ROOT"
python -m pip install healpy astropy
python src/planck_mask_gate.py --root "$ROOT" --analyse --out-nside 64
```

The full raw audit **rehashes the three original CDS .dat files** and refuses wrong counts. Published counts and 0.001 mag histogram are not inserted by hand into the generated full-source result. It audits 1PGC joins, missing calibration hosts, method overlaps, Table3/4 identity and conditional method+angular rank. Outputs are in `$ROOT/provenance/` and must be supplied to publish source-qualified H02 results.

Planck `--analyse` is separately optional. It reads six ~201 MB masks one-by-one, requires NSIDE2048 and converts to NSIDE64 RING for support-only analysis. It is not a validated Planck E2E likelihood; no unit-test PASS upgrades L01 or L03 physics by itself.

## Light sandbox replay without local raw

```bash
python src/prior_selected_source_sky.py --npz data/selected_source_observables.npz \
  --output results/CF4_35970_METHOD_SKY_REAL_RESULT.json
python src/method_mix_sensitivity.py \
  --source-result results/CF4_35970_METHOD_SKY_REAL_RESULT.json \
  --output results/CF4_METHOD_MIX_GAMMA2.json --gamma 2
python -m pytest -q tests
```

The bundled NPZ originates from prior PR #545 and has exact SHA `86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c` with 35,970 selected groups. Do not confuse it with 38,053 groups in complete official source, or publish its method label sky anisotropy as cosmological signal.

## Resume after local full audit

Read `$ROOT/provenance/CF4_RAW_FULL_SOURCE_AUDIT.json` and `PLANCK_MASK_SUPPORT_AUDIT.json`. Look at `direct_without_galaxy_cal_link_ids`, `group_DMzp_vs_DMav_0p001_histogram`, `individual_method_overlap_counts`, `angular_conditional_linear_rank`, and T/Pol intersection. Then implement source-selected W1-TF selection likelihood with parent survey data, common calibration and velocity law; for L01 generate real source-matched spin-2 mask/beam injection and, for L03, source-matched Planck null simulation IDs. Never treat 999 CMB and 300 noise maps as 299700 independent draws.
