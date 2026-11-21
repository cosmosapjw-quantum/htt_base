# R93 -> 다음 실제 과학 루프 인계: 999 SMICA harmonic / BASS–HTT / CF4

## 정확한 현재 지점

HTT checkout: /home/cosmosapjw/Dropbox/bianchi/htt_base
기존 연구 브랜치: research/r69-observable-physics-bridges-20261118
R93 시작 R92 HEAD: dd715302300d8f9f6c3e8a198c6ba768d694a43c.
SSOT R78: SHA256 90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11, 60 nodes/129 edges, NEXT SQ-CF4, 원래 science 상태 유지.

## 이미 실제 실행한 것

- R93 SMICA FFP10 signal realization 999개 (0..999, 970 누락), noise realization 300개. PR-150에서 source-to-reduction exact 검증된 512 MB NSIDE64 캐시를 재사용해 신호 999개 모든 I(T) masked a_lm (lmax48)와 4 구간의 20D signed L=2 off-diagonal Gaunt statistic을 계산. Private 전체 a_lm: ~/Downloads/htt_r93_ffp999_alm_biposh/SMICA_999_NSIDE64_MASKED_ALM_L48.npz, SHA receipt는 R93 JSON 참조. PR3 SMICA common mask, weighted mono/dipole 동일, noise[id%300].
- 300개 unique-noise MC가 제공한 exploratory global rank p=97/301=0.322259; 999개 재사용 noise 민감도 rank p=249/1000=0.249. 이는 pre-registered cosmological detection/Bianchi model probability가 아님.
- 원본 NSIDE2048에서 동일 mask/저차모드 적용한 단일 signal+noise T-pair와 NSIDE64 high-ell 프록시의 a_lm 차이: ell2..8 0.46%, 9..16 1.30%, 17..32 2.23%, 33..46 4.09%. Full high-ell 정확도를 캐시에서 자동 주장하지 말 것.
- 원본 관측 SMICA (NESTED)와 FFP10 한 CMB+noise (RING)의 NSIDE2048 Q/U로 spin-2 E/B 시범 변환. mask/beam E-to-B 누설과 source polarization convention이 미확정; 999 E/B ensemble 분석은 안 했음.
- BASS Codazzi vs HTT R49 normalized physical momentum constraint는 12 strata×5 sample 60 cases에서 2.7e-15 내외로 일치. Matter q/EOS/DEC 및 optical transfer는 아직 진짜 관측 모형으로 연결되지 않음.
- Mayukh legacy z inverse의 SR gamma 누락을 35,970 real CF4 source에서 정량검산. Legacy BiPoSH fake A20은 모든 999 MC에서 양수, 정확 Gaunt centered MC는 부호 균형. Old code는 compatibility layer로만 채택.
- Legacy 재딥스캔: 실물 2,913 / ZIP24 / member4,320 / AST Python1,005 / private FTS5 항목5,325. 주력 ZIP 추출물 1,294개 byte-identical. Private 전체 index: ~/Downloads/htt_r93_legacy_index/legacy_search.sqlite. 원본 archive/read-only.

## 계속할 세 갈래 연구

1. SQ-CF4 source reconstruction: R36 source low-k Fourier PV + R27 7-channel quotient, Mayukh corrected SR gamma and original 35,970 source를 함께 비교. Upstream MCMC calibration/selection/independent heldout이 없으면 physical acceptance는 BLOCKED_INPUT 유지.
2. P5 Bianchi conditional attribution: BASS Class A/B and HTT R49 Codazzi 동일성 위에 physical tilted EOS/DEC 및 finite-z Sachs/Jacobi/source-transport를 연결. 처음에는 Type I/V/VI_-1/9/VIIh/IX representative, counterexample와 full frame sign tests. Native polarized Boltzmann full all-m 은 별도 lane.
3. P2 real high-ell: 원본 FFP10 NSIDE2048 999개 T/Q/U를 파일당 한 번씩 읽는 streaming T/EB harmonic reducer를 source ID, mask order, beam, signal+noise pairing, exact file SHA/QA와 함께 구현한다. NSIDE64 캐시를 full-resolution 결과라 하지 말 것. Primary matched 300개의 **unique noise IDs**와 별도의 999 repeated-noise sensitivity를 보존한다. Commander 실제 release-matched null은 SMICA 999를 대체할 수 없음. Masked BipoSH estimator는 exact Gaunt/coupling + qualified E2E covariance; old \(1/fsky\) proxy 폐기.

## 재현 명령

- cd /home/cosmosapjw/Dropbox/bianchi/htt_base
- export PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
- .venv/bin/python -B scripts/r93/smica_ffp999_biposh.py --check
- .venv/bin/python -B -m pytest -p no:cacheprovider -q tests/obsstat/test_r93_third_loop.py
- .venv/bin/python -B docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/validate_unified.py --strict-authority
- .venv/bin/python -B scripts/r92/prepare_third_loop.py --check

## 실행·클레임 경계

- Original R78 60-node acceptance, R89 historical 18 reused/4 diagnostic/9 input blocked/29 dependency blocked, R90 17 solver-free/5 transfer work units를 그대로 둔다. R93 WORK_DAG_60_EVIDENCE는 새로 수행한 P2/P3/P5의 수치 증거와 P1/P4/P6/7 PHY 재사용을 정확히 구분.
- 원본 603 GB CMB/181 GB noise와 raw Planck obs/mask는 read-only. 파일 00818은 원래 FITS padding이 1218B 부족하지만 data HDU accessible, registered SHA and cache direct array match; ID970 누락. 이번 turn 새 대량 다운로드/외장하드 mutation 없음.
- BASS/REC/REI owner repo, original legacy, main, 다른 사용자의 tracked/untracked 파일은 수정하지 않는다. 검증된 R93 파일만 연구 브랜치에 게시.
