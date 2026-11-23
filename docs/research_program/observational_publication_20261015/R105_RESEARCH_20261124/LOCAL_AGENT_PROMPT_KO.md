# 실행 중인 로컬 에이전트에 추가할 프롬프트

현재 htt_base 작업을 이어서 맡아라. 대상은 `research/r69-observable-physics-bridges-20261118`이며 R104 출발점은 `5a5f3b44d4fa5be65b71c2f80e715ebf9d1abf0a`다. 이 파일이 들어 있는 R105 커밋과 원격 최신 HEAD를 먼저 확인하고, 더 최근 작업이 있으면 커밋 관계를 확인해 이어라. 이미 실행 중인 동일 시드·쌍·solver 설정은 재사용한다. 다른 사람의 변경, 로컬 `legacy/` 삭제, `data/external/` 및 대형 원자료를 별도 보존한다. 결과는 새 R106 분석 디렉터리에 쓰고, 소형 코드·근거·보고서를 연구 브랜치에 푸시한 뒤 로컬과 원격 SHA를 확인한다.

워크스테이션에서 다음 공통 변수를 쓴다. 아래 연속 예시는 첫 R106 실행용이다. 재개 시 완료된 run.json과 출력의 identity를 대조해 기존 결과를 재사용한다.

```bash
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
export PYTHONPATH=.:htt:htt/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
PY="$PWD/.venv/bin/python"
D=docs/research_program/observational_publication_20261015/R105_RESEARCH_20261124
FLOW="$HOME/Downloads/htt_r105_coras"
CACHE="$HOME/Downloads/htt_r106_analysis"
mkdir -p "$CACHE"
DONOR="$FLOW/deps/CORAS"
BIN="$FLOW/deps/pilot/coras_radial"
git -C "$DONOR" rev-parse HEAD
sha256sum "$BIN"
```

1. **H02와 SQ-CF4.** 원래 2M++ Manticore-Local 격자를 새로 확보하면 공식 manifest의 실현·축·속도 단위·프레임·크기를 검증한다. IAP의 기존 timeout은 `MANTICORE_ROUTE_PROBE.json`에 있다. 401개 은하단 Stockholm 카탈로그와 단일 2MRS-NN 오차지도에는 군 사이 속도장 사후공분산이 없다. 현재 실행 가능한 경로는 실제 2MRS 제약 CORAS다. 같은 설정에서 시드 129–256을 이어서 36계수 공분산, trace와 고유모드, 반분 상대 Frobenius 차이 및 관측 잔차 이차형식이 어떻게 변하는지 구한다. 아래 명령의 pilot 바이너리 SHA는 `a5450321da56b0ad46326ac74350bf9ddf641aed14458903b48228efb8c3da79`, donor는 `45ab25635aa32869ce207511d556ea257ab8a591`다. 재빌드본 `$FLOW/deps/build/coras_radial`은 별도 컴파일러 영수증에 묶여 있으며 seed 1의 출력이 pilot과 바이트 일치한다. 환원기는 다른 바이너리·격자·관측 지점의 실현을 따로 집계한다.

```bash
"$PY" -m scripts.r105.coras_flow --donor "$DONOR" --binary "$BIN" \
  --output "$CACHE/fine-129-256" --first 129 --last 256 --radial 36 --ell 8 --fft 24
"$PY" -m scripts.r105.coras_reduce \
  --runs "$FLOW/coarse" "$FLOW/fine" "$FLOW/fine-ext" "$CACHE/fine-129-256" "$FLOW/fft24" \
  --output "$CACHE/CORAS_H02_EXTENDED.json"
```

   같은 FFT와 시드에서 radial만 36→48, 이어서 고정 radial에서 ℓ만 8→12로 바꿔 창 투영의 변화와 seed scatter를 따로 보고한다. FFT 변경에서는 같은 시드 번호도 물리적 모드가 달라질 수 있다. 21,860개 군의 결과와 14,110개 결측 군을 분리한다. CF3와 CF4·6dFGSv의 공통 객체/거리 교정 계보, 공통 영점, fit에 들어간 2MRS 객체를 조사한다. 가능한 교차표·제외 fold를 만들어 동일한 상대 점수를 재산출한다. 표본 수준의 독립성을 확인하기 전에는 Q 및 예측 이득에 그 조건을 붙인다.

2. **6dFGSv.** R105의 8,885개 위치, 선택된 7,190개 대상, 기존 PGC/PGC1 fold와 ID 해시를 그대로 사용한다. 8개 실현의 가중치 집중을 128개로 재검사한다. 두 정책별 합과 각 fold, 상대 점수의 차, 유효 성분 수를 반환한다.

```bash
"$PY" -m scripts.r105.cf4_coras_marks generate --donor "$DONOR" --binary "$BIN" \
  --output "$CACHE/marks128" --last 128 --radial 36 --ell 8 --fft 24
"$PY" -m scripts.r105.cf4_coras_marks score --run "$CACHE/marks128" \
  --reference "$D/CF4_FIELD_HOLDOUT.json" --output "$CACHE/CF4_MARKS128.json"
```

3. **Commander와 L03.** R105는 PR3/FFP10 Commander의 같은 15계수 추정량으로 00000–00002까지 끝냈다. 00003–00006은 공개 noise 4개, 총 2,415,951,360 B를 받으면 7쌍이 된다. 이 범위를 먼저 실행하고, 수집·중단복구와 beam/마스크/입력 해시가 일치하면 300쌍까지 묶음별로 확장한다. 남은 전체의 현 재고 기준 신규 통신량은 356,352,825,600 B이다. 매번 같은 reductions 디렉터리를 쓰고 현재 재고로 남은 묶음의 예산을 산출한다. 각 단계에서 순위 해상도, 관측·모의 동일 추정량, HM/OE 검사 가능 여부를 남긴다.

```bash
"$PY" -m scripts.r105.commander_ensemble batch --start 0 --stop 7 \
  --include "$D/COMMANDER_TRANSFER.json" "$D/COMMANDER_PAIR_00001.json" \
  --directory "$HOME/Downloads/htt_r105_commander/reductions" \
  --max-download-bytes 2415951360
```

4. **BASS solver.** 광학깊이 하위 시간격자는 구현돼 있다. `SOLVER_AXES_PILOT.json`, `SOLVER_192.json`, `NATIVE_OPTICAL_REFINEMENT.json`에서 FLRW·예외적 VI₋₁/₉·VII_h·IX의 출발값을 읽고, 시간 96/192/384, ℓ=4/6/8, Picard 4/6, 고정 간격·Δτ 상한 1/0.5를 한 축씩 바꾼다. 네 계열 32개 고유 설정을 체크포인트로 재개할 수 있다. 먼저 SOLVER_COMMON_TIMES.json의 48개 일치 끝점 중 두 초기 끝점만 시간 세분화 때 잔차가 커진 원인을 조사한다. 첫 공통 ln(a)=−7.224667385642617에서 3.19355e−6→3.53970e−6→3.62928e−6이다. Δτ 상한만 1→0.5로 바꾸고 동일 시각의 signed 잔차로 비교한다. peak가 다른 셀로 이동하면 그 셀의 N·Δτ, 부호 있는 q/E 성분, 물질/하늘 π/E, Hamiltonian·Codazzi·Stokes reality, C₂를 출력한다. 줄지 않는 첫 잔차의 원인을 충돌, 기하 중점/전단 source, 물질 피드백으로 분해한다. 예컨대 기하 시간 고정이 원인이면 동일 REC 시계와 바리온 모델을 유지하고 기하·전단만 실제 SDIRK 단계로 옮겨 해석 특수해·FLRW·한 축 수렴·R105 기준과 A/B 시험한 뒤 반영한다. 계산 오류를 고친 범위와 독립 물질 모멘트가 있어야 진행되는 B03/B04를 구분한다.

```bash
"$PY" -m scripts.r105.solver_axes --preset local --workers 3 --timeout-seconds 1800 \
  --output "$CACHE/solver_axes.json"
```

5. **REC/REI, Gaia, NVSS.** `SOLVER_SOURCES_KO.md`에 지정한 REI z=4 원본 restart에서 다섯 전단 사례별 전하·온도·proper 시간·광자 재고를 확인한다. 끝의 두 출력 간격을 재생한 다음 z=0까지 연장 가능한 사례에서 두 적분 cσ_T∫n_e dt와 ∫cσ_T n_e/H dN를 대조한다. 공통 FLRW+tanh 전경은 민감도로만 보존한다. Gaia에서는 두 적색편이 곡률 행 사이의 공분산을 유지하고 패치 47·8을 제외한 결과와 독립 frame/sky null을 대조한다. NVSS는 R65와 같은 peak–integrated 비선형 추정량, 동일 마스크·삭제 블록으로 독립 LSS/선택 모의를 적용한다. 두 분석의 working 이차형식은 보정 모의가 확보된 범위에서만 유의도로 바꾼다.

6. **연구 산출물.** `"$PY" -m scripts.r105.program --node H02`와 `NODE60_EXECUTION.json`에서 원 60 노드/129개 의존 관계와 P1–P6/PHY-01–07의 해당 행을 조회한다. 대상·단위·프레임·코드/데이터 SHA, 성공과 실패, 데이터 재사용·중첩, CPU·메모리·수신량, 검정 가능한 물리 예측을 신규 결과와 함께 저장한다. H05는 CF4_LITERATURE_H05.md의 동일 cz 절단 W1 비교와 CF4_H05_AXES.json의 결측 민감도에서 출발해 공통 창·기준계·보정조건으로 재적합한다. 광자·물질 독립 소스, 보정된 공동 null, 선택과 영점이 충족된 범위만 physical Π/G_F 또는 Bianchi 계열 판정으로 올린다.
