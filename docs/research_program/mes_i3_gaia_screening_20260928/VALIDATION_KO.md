# I3 Gaia-CRF3 screening 검증

I3에서 참조한 I1·I2 원문과 독립 검토는 [체크포인트 통합 안내](../mes_verified_checkpoints_20260928/README_KO.md)에서 Git 추적 파일로 읽을 수 있다. I2의 동봉 I3 프롬프트는 역사적 지시이며 이 폴더의 I3 결과가 현재 후속 상태다.

2026-09-28. Owner: HTT research; scope: I3의 이상적 전천 방향 응답과 대표 입력의 적합성. Claim tier C0, `DIAGNOSTIC_ONLY`; transfer source 없음. 생성 절차: 원본 ZIP의 manifest/CRC와 선행 I1/I2/R3 SHA-256을 확인하고, 동봉된 CAS 스크립트를 아래 명령으로 실행하며, Gaia 공식 문서와 원 논문을 읽어 field와 빠진 nuisance 계약을 대조했다. 이 문서는 독립 CAS4 등록 판정, 관측 적합, 일반 finite tilt 물리 검증이 아니다.

## 입력 identity

- 원본 `HTT_MES_I3_LOCAL_RETURN_20260928_1511.zip`: SHA-256 `5f7809bdaecd6c241af42181293ff1c4e2a586e8d5dead15169f894cfc0e2016`; ZIP CRC 통과, 4개 member의 SHA-256이 원본 `MANIFEST.sha256`과 일치한다. 원본 ZIP과 풀린 원본 파일은 수정하지 않았다.
- I1 `TARGET_RESPONSE_THEORY_KO.md`: `666db799914911ba5824d6dd46e4ae01296106e67c1c4c7a433d846a2786d161`.
- I2 `PHYSICAL_RESIDUAL_AND_IDENTIFIED_SET_KO.md`: `4976e5785a66616180ed73ccd5e7e3065a5e7bfb6315122649a2dffd025e1d5f`.
- R3 `R3_2026-09-27_MES_R3_OBSERVABLE_JET_AND_SOURCE_BOUNDS_20260927_KO.md`: `31b55cfaf7e3f0c40907ee4386a5fc424cd7066c1d989d55019de41a956227aa`.

## 실행한 검산

| 도구 | 확인한 명제 | 결과 / 한계 |
|---|---|---|
| Wolfram exact symbolic | 일반 STF 두 행렬의 전천 bilinear 적분, 임의 회전 벡터와의 cross term, tilt STF Gram | 세 잔차 모두 0. 원본 `WOLFRAM_LIGHT_RAW.txt`에 원래 계산 코드·출력이 보존되어 있으며, 현재 범위별 재검산 출력도 0이었다. xAct 설치는 확인했으나 이 유한차원 구면 대수에는 xTensor가 필요하지 않았다. |
| `python3 -B validation/sympy_check.py` | 같은 적분과 Gram 및 determinant | 네 잔차 0, SymPy 1.14.0. |
| `PYTHONDONTWRITEBYTECODE=1 sage -python validation/sage_check.py` | 같은 유리수 다항식 identity | 네 항목 모두 True. |
| `Singular validation/singular_check.sing` | Gram determinant 다항식 | 0과 `SINGULAR_TILT_GRAM_DET_PASS`. 최초 명령에서 분수식 괄호 해석 오류가 발생했고, `(p1^2)/6`으로 고친 뒤 통과했다. 최초 실패는 결과 판정에 포함한다. |
| `cd formal_mathlib && PYTHONDONTWRITEBYTECODE=1 lake env lean ../docs/research_program/mes_i3_gaia_screening_20260928/validation/HTTMESI3Optical.lean` | 구면 moment를 **가정한** 계수 환원과 Gram determinant | Lean 4.31.0/mathlib에서 컴파일 통과. 구면 moment 정리, R3 optics, Gaia 선택/공분산은 Lean으로 증명하지 않았다. |

이들은 Host가 수행한 범위별 교차 검산이다. 저장소의 등록된 동일 `CAS_CONTRACT.json`에 따른 독립 4축 실행·adjudication은 없으므로 `CAS_4AXIS_PASS`를 부여하지 않는다. 이상적인 `M^*M=I/5`와 `√5 ε` 외접구는 선언된 전천 정규화 및 독립 nuisance bound가 있을 때만 성립한다. 실제 `ε`는 없다.

## 과학·출처 판정

[Gaia DR3 공식 `gaia_source` 문서](https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_main_source_catalogue/ssec_dm_gaia_source.html)는 `ref_epoch`가 TCB Julian year, `ra/dec`가 ICRS 위치, `pmra/pmdec`가 mas/yr, `pmra_pmdec_corr`가 개별 상관계수임을 명시한다. [Gaia-CRF3 원 논문](https://doi.org/10.1051/0004-6361/202243483)은 QSO 선택, frame rotator의 spin, 큰 각도 proper-motion systematic을 논한다. Catalog proper motion은 astrometric solution의 적합 계수이므로 순간 optical drift와 연결할 관측 시간 window/solution response도 필요하다. 이 자료만으로 근거리 동일 congruence의 물리 거리, source motion, Fermi–ICRS frame 변환, cross-source covariance, 선택 response, Taylor remainder를 채울 수 없다. 따라서 `HOLD_INPUT_INCOMPLETE`다.

원본 보고서의 누락된 표 backtick과 Fermi/catalog frame 혼용을 정정하고 catalog 시간 적합 response를 명시한 사본이 `REPORT_KO.md`다. 속도·거리·frame 항을 함께 명시한 **모델 계약**이며 Gaia 적용성 또는 실제 shear 측정이라고 해석하지 않는다. 원본 ZIP은 byte-preserved evidence로 남는다.

| Claim | Owner | 상태 | 근거 | 승격 차단 사유 |
|---|---|---|---|---|
| 이상적 전천 STF 응답 Gram | HTT | `DERIVED`, C0 조건부 | 직접 유도와 범위별 CAS 검산 | 관측 mask/selection/nuisance law 없음 |
| Gaia-CRF3를 I3의 동일 상태 optical 입력으로 채택 | HTT | `HOLD_INPUT_INCOMPLETE` | 공식 schema 및 원 논문 | distance, congruence, motion, frame, covariance, remainder 결손 |
| 실측 shear / `Z` / Bianchi family | HTT | `NOT_RUN` / 금지 | 없음 | 물리·관측 gate 미충족 |
| I2 radiation-only Bianchi I 조건부 결론 | HTT | `DEFENDED_CONDITIONAL` 유지 | I2 독립 decision | 일반 finite tilt 또는 실측으로 확장 불가 |

독립 I3 decision reviewer는 실행되지 않았다. 이 문서와 스크립트의 통과는 source/method screening을 등록할 뿐 claim promotion을 승인하지 않는다.
