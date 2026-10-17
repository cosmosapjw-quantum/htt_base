# HTT six-paper L01/S02 실측 source-mask 파일럿과 coherent-stf 연구 패키지

2026-10-17 KST · 제안 PR #552 후속 scoped 실험 · `native_subagent: NOT_RUN`.

## 재현 (샌드박스 또는 Ubuntu local)

```bash
unzip HTT_SIXPAPER_L01_S02_R8MASK_COHERENT_20261017.zip -d research_replay
cd research_replay/htt_20261017_next
python -m pip install numpy scipy pytest matplotlib
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python -m pytest -q tests
python src/r8_spin2_source_pilot.py --mask-source source/r8_cmb_controls.npz --output results/R8_T_MASK_SPIN2_PILOT.json
python src/s02_coherent_stf.py --source source --output results/S02_COHERENT_STF_SOURCE_BOUNDS.json
python src/plot_results.py
python scripts/verify_manifest.py .
```

`source/r8_cmb_controls.npz`는 사용자 Dropbox 연결의 실제 PR3 R8 *temperature common intersection* source이며, 공식 POL mask는 아니다. 마스크는 native RING64, 36,433개. spin2 injection은 제조된 신호다.

## 로컬 원본 PR3 Polarization mask 전용 실행

이미 로컬에 검증된 세 FITS를 사용한다. 이 명령은 공식 native NESTED2048를 RING64로 변환하고 Q/U 수학적 Wigner-d low/high operator K (64×90)를 계산한다. 이 마스크 결과는 원본을 제공한 컴퓨터에서만 실제 실행 가능하며 샌드박스 run과 구별한다.

```bash
python -m pip install healpy astropy
ROOT=/mnt/extdrive/workdir/htt_open_data
python src/native_planck_pol_response.py --root "$ROOT" --verify-only
python src/native_planck_pol_response.py --root "$ROOT" --out "$ROOT/provenance/L01_NATIVE_PR3_POL_K64x90.json"
```

결과 `L01_NATIVE_PR3_POL_K64x90.json`, 같은 경로에 `L01_NATIVE_PR3_POL_K64x90_common.npz` 및 `_three_way_intersection.npz`. `healpy`와 pure-Numpy ring 좌표 교차검증, full FITS SHA 교차검증을 수행한다. 주의: POL masking만으로 physics transfer/beam/E2E는 통과하지 않는다.

## 메모

S02 `source/h03_source_original.zip`은 H03 재현의 immutable input으로 유지한다. 실제 CF4 physical signed Q posterior는 계산되지 않았다. 연구 보고서 `research/SCOPED_RESULTS_KO.md` 참조.
