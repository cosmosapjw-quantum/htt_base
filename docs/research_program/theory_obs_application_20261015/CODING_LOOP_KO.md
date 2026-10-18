# 이론-관측 실행용 코딩 연구 루프 C1–C10

현재 실행 환경: 기존 primary checkout /home/cosmosapjw/Dropbox/bianchi/htt_base, 외장 raw /mnt/extdrive/workdir. 원시 입력은 읽기만 했고 이동·덮어쓰기·정리하지 않았다. 기존 이론의 과학적 gate 및 HOTT/MIO ownership을 변경하지 않았다.

## C1–C4: 범위, I/O 및 선택한 수치법

**CMB**: 이미 검증된 Planck FFP10 SMICA NSIDE64 source cache와 300 paired sky rows, 기존 six-processor의 source-bound 32-vector를 사용한다. 누락된 raw beam/component-separation의 물리 연산자를 임의로 구성하지 않고, cache 이후 관측 pixel-map OLS에서의 source reconstruction / conditional local boost derivative를 분석한다.

기존 함수 사용: obsstat.r7_cmb_product_response.real_design 및 pixel_fit_geometry; scripts/run_smica_reboot_pilot.build_ols_projector; obsstat.lorentz_sky_pullback.pullback_thermodynamic_temperature_field. 새 모듈: obsstat.processed_boost_theory_bridge. source cutoff ell5,8,12, mask>0.5/0.8, target ell0..5 동시 적합 후 ell2..5 32-vector 보존. 진짜 CMB monopole의 일차 ell1 response는 target에서 제거; 이 효과와 ell2+ nonlinear sky를 혼동하지 않는다.

**CF4**: raw table3/4.dat.gz를 해시-인증하는 기존 PR179 loader 사용. source allowlist와 1PGC join 고정. 선택 0.01<=Vcmb/c<=0.1. E4/E9/13-column model은 cosmographic source-배치 검정; published e_DMzp에 기초한 row-weight experiment는 모의 Gaussian likelihood를 의미하지 않는다. 새 모듈 obsstat.optical_depth_design_bridge.

확장하지 않은 것: native Bianchi solver, FFP10 raw high-res reprocessing, full CF4 physical latent likelihood 및 posterior, 모든 172 historical theorem candidates의 재검사.

## C5–C6: 구현 및 회귀

- htt/obsstat/processed_boost_theory_bridge.py: SciPy spherical-harmonic angular derivatives, exact linearized generator, source-contracted pixel Jacobian, bounded high-mode Fisher stress.
- htt/obsstat/optical_depth_design_bridge.py: E4+E9 observational design, principal-angle/rank, positive design weights, categorical method-offset nuisance.
- scripts/run_htt_theory_observation_bridge_20261015.py: gated Planck observation cache -> six matched source/processing runs -> covariance sensitivity and conditional bootstrap -> JSON/Markdown/PNG/PDF.
- scripts/run_htt_cf4_optical_theory_bridge_20261015.py: hashed external CF4 raw -> source-bound directional-depth subsets -> rank/principal-angle comparison -> JSON/Markdown/PNG/PDF.
- scripts/verify_htt_theory_observation_oracles_20261015.py: Healpy independent spectral derivative path, actual observed-map exact finite boost central-difference comparison, Fisher stress monotonicity check.
- 이전 대화에서 수정하고 검증한 htt/obsstat/catalogs/cf4_raw.py의 gzip 원시 input path와 그 회귀검사를 그대로 보존했다. 이번 연구 CLI는 손으로 재작성한 SHA 대신 기존 실제 CF4 subset receipt의 SHA-256을 사용하여 기존 원본을 인증한다.

실행한 전체 영향권 시험:

    PYTHONPATH=htt:htt/src:scripts OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 \
      /usr/bin/python3 -m pytest -q \
      tests/obsstat/test_processed_boost_theory_bridge.py \
      tests/obsstat/test_optical_depth_design_bridge.py \
      tests/obsstat/test_cf4_raw_catalog.py \
      tests/test_smica_reboot_pilot.py tests/r7/test_cmb_product_response.py \
      tests/obsstat/test_reboot_tensor_features.py \
      tests/htt/test_r2_cmb_product_bridge.py --disable-warnings --maxfail=1

결과: **49 passed**. 추가 표적 Healpy·Wolfram·원시 gzip/비압축 쌍의 항목별 검사는 해당 source/results에 보존. pytest PASS는 실제 E2E 방정식의 물리적 참을 뜻하지 않는다.

## C7–C8: 물리적 oracle, 실제 실행 성능, 통계 민감도

CMB 최신 authoritative run:

    PYTHONPATH=htt:htt/src:scripts OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 \
      /usr/bin/python3 scripts/run_htt_theory_observation_bridge_20261015.py \
      --output-dir docs/research_program/theory_obs_application_20261015/results/cmb_processed_boost_v2

결과: 6 source-mask rows, 13.00 s, peak RSS 619.4 MiB. 입력 cache identity sha256:86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb. peak와 runtime은 한 로컬 실행의 측정값이지 하드웨어 전체 벤치마크가 아니다.

CF4 run:

    PYTHONPATH=htt:htt/src:scripts OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 \
      /usr/bin/python3 scripts/run_htt_cf4_optical_theory_bridge_20261015.py \
      --input-root /mnt/extdrive/workdir/raw/cf4_full \
      --output-dir docs/research_program/theory_obs_application_20261015/results/cf4_optical_design_v1

결과: 38,053 raw groups 중 35,970 matched rows, 1.32 s, peak RSS 95.1 MiB. 원시 table3/table4의 SHA-256과 ID census를 결과 JSON에 보존.

독립 과학 oracle:

    PYTHONPATH=htt:htt/src:scripts OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 \
      /usr/bin/python3 scripts/verify_htt_theory_observation_oracles_20261015.py \
      --output docs/research_program/theory_obs_application_20261015/evidence/scientific_oracles.json

결과: Healpy vs SciPy harmonic+gradient < 10^-12; actual observed-source analytic derivative vs exact Lorentz central finite difference 상대 오차 6.23e-7 -> 1.56e-7 -> 3.90e-8. Finite-sample 240 null row C의 조건수 ≈12.5; 250 row-resample bootstrap은 covariance estimation variability에만 사용. 기본 6 conditional Fisher traces는 가정한 추가 independent high-mode variance가 증가할 때 단조감소.

## C9–C10: 검사 범위, 인계, status

한 모델의 self-review 및 독립적인 계산 엔진(SciPy/Healpy/Wolfram)이 수행한 대조 검사만 확인되었다. **별도 native subagent 코드 review: NOT_RUN.** 이 때문에 독립 fresh-context review PASS를 주장하지 않는다.

기존 HEAD 및 역사적 최초 실행의 결과를 덮어쓰지 않았다. 최초 CMB v1은 부주의하게 physical_beta_reference_shift라고 표기했으나, source가 이미 관측된 SMICA sky surrogate라는 물리적 경계를 정밀화하여 v2에서는 reference_beta_tangent_shift로 정정했다. v1은 원래 실행기록, 현재 주장 근거는 v2. 개인 식별정보나 외장 raw bytes는 git 결과에 포함하지 않는다.

다음 실제 구현 의무:
1. 제대로 된 raw-sky component separation/beam/high-ell transfer에 닫힌 processed response를 구성하고, full product response와 surrogate Jacobian을 비교한다.
2. CF4 primary Vh 및 적색편이 절편, 거리/광학 remainder, shared-method calibration/selection의 joint latent likelihood를 작성하여 geodesicity identified-set을 생성한다.
3. 현재 결과의 PDF 그림/JSON, source hash, observed-source convention과 full-covariance rank를 source-matched 독립 fresh-context 심사에 제출한다.

현재 단독으로 재현 가능한 산출물은 두 실행 디렉터리의 result.json/REPORT_KO.md 및 scientific_oracles.json이다. 성능 및 숫자는 모두 본인이 실제 실행한 기록이며 원자료 보존은 SHA/소스 path identity에 근거한다. 새 코드와 원본 raw data는 구별한다.


## 중단 복구 이후의 추가 코딩 결과

실제 공통 mask를 통과한 finite 고차모드 연산자 K의 SVD 및
pivoted QR rank, 32차원 전체 관측공간에 대한 pseudoinverse identity,
국소 boost 세 성분의 quotient residual과 기준속도에 대한
최소-norm 상쇄 벡터 a_*=-K^+ J beta를 실제 계산했다.
코드: scripts/verify_htt_processed_nuisance_quotient_20261015.py.
결과: evidence/processed_nuisance_quotient.json.
그림: evidence/processed_nuisance_compensator.png.

mask 0.5 / 0.8에서 K의 수치 rank가 32/32이고,
mask 0.5 / source L12에서 상쇄 계수 norm 5.60170 microK 및
출력 잔차 1.43e-15 microK를 확인했다. 이 값들은 source coefficient
자유도를 완전히 허용한 이산 선형모형에 대한 것이며 관측물리
likelihood나 검출 통계량으로 승격하지 않는다.

중단 이후 원격 checkout의 HEAD, 작업트리, 경량 scientific_oracles,
source/result identity를 확인했다. 영향권 49개 표적 테스트를
실제로 재실행하여 49 PASSED, 0 FAILED, exit code 0을 얻었다
(로컬 /tmp/htt_theory_obs_tests_resume_20261015.log).
이전 source/결과물, 외장 관측 원본은 보존하였다.
독립 fresh-context reviewer와 native subagent는 노출되지 않아
실행하지 않았으며, 저장소 기존 독립 리뷰 절차를 통과했다고
주장하지 않는다. 최신 code/result가 허용받을 때에만
Git commit/push 및 PR 리뷰 절차를 계속한다.
