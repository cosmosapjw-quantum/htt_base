# htt_base 직접 실행: P2/L01 R9 / C9

새 ZIP이나 별도 소스 다운로드 없이 GitHub Draft PR의 repo 코드를 사용한다. 기존 original Planck FITS / R7-C7 NPZ / C8 JSON은 변형하지 않고 기존 /mnt/extdrive/workdir/htt_open_data에서 읽는다.

## 기존 checkout 미커밋 작업 보존

~~~bash
REPO="$HOME/Dropbox/bianchi/htt_base"
BR=research/htt-sixpaper-p2-l01-r9c9-beam-same-sky-20261017
cd "$REPO"
git remote -v
git fetch origin "$BR"
git worktree add /mnt/extdrive/workdir/htt_l01_repo_r9c9 "origin/$BR"
cd /mnt/extdrive/workdir/htt_l01_repo_r9c9
~~~

원래 uncommitted repo를 reset하지 않는다. 이미 worktree가 존재하면 새 디렉터리를 선택한다.

## 같은 repo의 기존 분석 코드를 재사용

~~~bash
S=docs/research_program/observational_publication_20261015/L01_R8_C8_TWO_MASK_STABILITY_20261017
ROOT=/mnt/extdrive/workdir/htt_open_data
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m pytest -q "$S/tests"

python "$S/src/l01_r9c9_same_sky_beam.py" \
  --native-receipt "$ROOT/provenance/L01_NATIVE_PR3_POL_K64x90_v2.json" \
  --spectral-receipt "$ROOT/provenance/L01_NATIVE_SPECTRAL_CERT_20261017.json" \
  --c8-receipt "$ROOT/provenance/L01_R8_C8_TWO_MASK_STABILITY_20261017.json" \
  --out "$ROOT/provenance/L01_R9_C9_SAME_SKY.json"
~~~

기대 결과: delta_norm 약 0.4396287723908507, delta_E_to_B_norm 약 0.2564294649638681, beam_status NOT_RUN_NO_FULL_SMICA (beam 파일을 아직 사용하지 않는 경우).

## 추가 공식 관측자료 (코드는 이미 repo에 push)

Planck PR3 SMICA full IQU FITS는 약 1.9 GiB로 POL_BEAM(ell0..4096) extension을 포함한다. HM1/HM2/OE1/OE2는 각각 약 576 MiB다. 먼저 충분한 디스크 공간을 확인한다. 원본 바이너리는 repo 밖에 저장한다.

~~~bash
python "$S/src/fetch_planck_pr3_smica.py" --root "$ROOT" --products full --dry-run
python "$S/src/fetch_planck_pr3_smica.py" --root "$ROOT" --products full
# 선택: 분할맵도 다운로드
python "$S/src/fetch_planck_pr3_smica.py" --root "$ROOT" --products hm1 hm2 oe1 oe2
~~~

다운로더는 HTTP Range가 정확히 일치할 때만 이어받고, Range 무시는 새 파일로 시작하며, 기존 소스 파일을 덮어쓰지 않는다. 출력 SHA-256은 로컬 다운로드 바이트 지문이지 공식 서명 digest가 아니다.

## 조건부 SMICA beam 적용

~~~bash
python -m pip install astropy
python "$S/src/l01_r9c9_same_sky_beam.py" \
  --native-receipt "$ROOT/provenance/L01_NATIVE_PR3_POL_K64x90_v2.json" \
  --spectral-receipt "$ROOT/provenance/L01_NATIVE_SPECTRAL_CERT_20261017.json" \
  --c8-receipt "$ROOT/provenance/L01_R8_C8_TWO_MASK_STABILITY_20261017.json" \
  --smica-full "$ROOT/planck/PR3/cmb/COM_CMB_IQU-smica_2048_R3.00_full.fits" \
  --out "$ROOT/provenance/L01_R9_C9_SMICA_BEAM_CONDITIONAL.json"
~~~

CONDITIONAL_POL_BEAM_DIAGONAL_ONLY는 full beam/foreground/mapmaking transfer 검증이 아니다. 관측 Q/U, ell>=9 tail, FFP10 matched null은 미실행이다.

## 단계별 게시와 6개 논문 DAG

| 단계 | 게시물 | 범위 | 공식 DAG |
|---|---|---|---|
| R9 | Same-sky covariance, minimum-norm source, beam conjugation 정리와 사용자 실행 영수증 | Derived; Wolfram exact rational example | 14/42 |
| C9 | 기존 K reader 재사용, source-bound beam/covariance adapter와 회귀 테스트 | GitHub 게시 + byte readback; native user execution NOT_RUN | 14/42 |
| Data | allowlisted official IRSA SMICA full/HM/OE fetch 코드 | 공식 URL 검증; 실제 대용량 다운로드 NOT_RUN | 14/42 |

P1 1/6, P2 0/6, P3 2/6, P4 1/6, P5 1/5, P6 2/6, COMMON 7/7 = 14 completed_scoped + 28 pending. READY L01/S02, six papers all NOT_READY_TO_SUBMIT. Canonical DAG/queue, main, unrelated backlog, journal untouched.

원격 Desktop Commander는 현재 월간 사용 한도로 차단되어 있으므로 사용자 로컬 명령은 이 대화에서 실행되지 않았다.
