# HTT R91 · 2차 연구 루프의 실행 인계

## 현재 정본
- Existing checkout: `/home/cosmosapjw/Dropbox/bianchi/htt_base`
- Active branch: `research/r69-observable-physics-bridges-20261118`
- R91 기준 부모: `96ea1f33af154f26e68acf7d39346ed86c67c87b`
- 과학 SSOT: R78 `INTEGRATED_DAG.json`, SHA256 `90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11`
- R78 과학 DAG: 60 original nodes / 129 hard edges / NEXT_ID SQ-CF4 / ORIGINAL STATE UNCHANGED.
- R90: 17 solver-free units + 5 external native-transfer units, source-conditional 84 Bianchi representative witnesses (not family discovery).

## 재현
```bash
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
export PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
.venv/bin/python -B scripts/r91/run_second_cycle.py --check
.venv/bin/python -B -m pytest -p no:cacheprovider -q tests/obsstat/test_r91_second_cycle_science.py
.venv/bin/python -B docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/validate_unified.py --strict-authority
```

## 실제 다음 연구 경로 (science first, not governance)

1. **SQ-CF4/P3:** R36의 이미 한정 승인된 `PV_FACTORS.npz`·`RESULT_MATRICES.npz`에서 `0.005≤k≤0.05 h/Mpc` 조건부 PV covariance를 source matched로 도입했다. R27 7 method quotient도 실제 재사용 가능하다. 이 두 **서로 다른 모델**을 추가 외부 source에서 얻는 MCMC calibration posterior 및 CF4++ velocity field와 대조하라. 기존 R36 hyperparameters를 empirical covariance라고 간주하지 말고, k 밖/비선형/selection/zero-point prior를 명시하라. 새 모델/소스가 없는 경우에는 published posterior를 재구성했다고 주장하지 말고 부분식별을 끝내라.
2. **P2/L03:** 새로 확인된 native Plik-lite 613-bin/LowE scalar data로 isotropic FLRW benchmark/control은 실제 실행 가능. R91 `PLIKLITE_BASELINE.json`은 published Planck best-fit theory를 사용해 scalar A_planck를 profile했다. **플랜크 CMB 사중극의 방향 형태**는 Clik/Plik만으로 식별 안 됨 (R91 exact isospectral STF Q2 counterexample). R89의 8 map/75 FFP pilot은 편광·selection-dependent anisotropy null로 승격 금지. Commander source-qualified matched null이 확보되는 범위부터 실행.
3. **P6/Gaia:** R91에서 실제 634233 QSO 전체로 4 working selection estimands 및 48-patch JK를 계산. R89의 `selection_weighted`가 selection (s) 가중인지 역선택 (1/s)인지 해석을 고정하라. 악천문 AGN/scan, source redshift·magnitude, Quaia G<20.5 독립 matching null을 대상으로 실제 finite-source calibration을 구성하라.
4. **P4/Radio:** R89에 있는 NVSS/RACS/SPICE/SUMSS/LoTSS 5개 자료 **전부 분석**한 결과를 재사용, 새로는 실제 survey-specific RMS/LSS clustered null 또는 independent random catalogs가 있을 때에만 실행. 비독립 방향 14개만으로 joint evidence를 만들지 마라.
5. **P5/Bianchi:** R49의 일반 Class A/B tilted 3-vector background 및 R90 84 canonical compatible witnesses를 이용해 **finite-z Sachs/Jacobi/Ehlers 1+3 optics 및 curvature STF**에 대해 실제 forward map을 계산하라. 이 경로는 native all-m polarized hierarchy 없이 실행 가능하다. 단, Lie family 수를 정당한 equivalence/continuous h strata로 세고, `q_a=0` 대 `q_a≠0`, multiple fluid EOS, frame rotation/tilt, selection을 정확히 처리하라. R62 실제 source tensor와 물리 normal shear 사이의 transport가 없으면 confidence witness만 인정.
6. **P1/PHY:** R89 P1 2048 coupled windows and partial-ID와 R90 seven PHY physical/geometric diagnostics를 정확한 source SHA로 재사용. Conditional (x,Q,F)가 존재해도 physical (Pi,G_F)는 matched null/physical measure/finite-z transport가 없으면 null.
7. **External Native Lane:** `SQ-NATIVE`, `B02..B05`의 외부 all-m polarized Bianchi T/E/B atlas, high-l transfer/family posterior는 원래 scientific acceptance에서 필요하다. CAMB/Cobaya/Clik **기준 ΛCDM** 모듈로 대체할 수 없다. 이 외부 lane을 P5 morphology geometry의 전제조건으로 올리지 마라.

## 데이터/코드의 소유권
- Private complete 349,040-file index: `~/Downloads/htt_r91_local_inventory`, repo로 업로드하지 않는다.
- 새 downloads 필요할 때만 공식 release/파일·허가·SHA 확인 후 `/home/cosmosapjw/Downloads/` 안에만 수신. 외장하드 `/mnt/extdrive/workdir`은 read-only source. PR4/NPIPE 전체 대량 다운로드 금지.
- Cobaya native PlanckPlikLite 공개 구현과 Planck 2018 dataset가 이미 외장하드에 있음. 고정 theory baseline은 실제 계산 완료. 외장하드의 CAMB 설치 흔적이 있더라도 실행 가능한 native 환경이라고 가정하지 말고 독립 smoke test 후 쓰라.
- Branch는 기존 `research/r69-observable-physics-bridges-20261118` 계속. 기존 R78/R89/R90 원본, 사용자 unrelated dirty/untracked 데이터, `main` 변경/merge/force-push 금지.
- 새 검증된 물리 계산·source identity·계측 성능·물리적 한계를 실제 파일과 commit으로 남겨라. 과학적 acceptances의 unconditional PASS/60 science complete 금지.

## 반환
각 P1–P6, PHY-01..07, SQ source qualifier 별 `actual scientific result`, `source version/SHA`, `reference formula`, `calibration|null`, `test command/exit`, `next actionable input`을 제출하라. R91은 2차의 **실행 가능한 한정 범위**만 완료했고 60개 논문의 물리적 제출 완료가 아니다.
