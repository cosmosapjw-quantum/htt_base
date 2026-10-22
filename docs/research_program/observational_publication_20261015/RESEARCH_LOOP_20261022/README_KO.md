# 이론·공개자료 연구 루프 — 2026-10-22

기존 checkout과 draft PR[#561](https://github.com/cosmosapjw-quantum/htt_base/pull/561)을
이어 작업했다. 재개 HEAD는`d66328b8d96ba9cc7bd8c1cbfd929be40903312c`다.
원래 과학 DAG는 **17/42**, 직접 외부입력8개와 의존노드17개가 남아 있다.
이번 제한 결과나 다운로드를 원래 acceptance 완료로 바꾸지 않았다.

## 실제로 진전한 부분

1. **과거 아이디어 재사용:** PR558개의 metadata를 수집하고 핵심 legacy 원문과
   코드를 연결한 [지도](LEGACY_MAP_KO.md)를 만들었다. 옛 공동상태·정규화·부분식별
   방법을 이번 계산에 사용했다. 모든 diff를 재검증했다는 주장은 아니다.
2. **선택법칙의 조건부 경계:** 공통 정규화를 유지하는 양의 중요도 가중치 집합을
   선형분수 최적화로 표현하고, [유도](THEORY.md)와 [실행 결과](selection/REPORT.md),
   [그림](selection/SENSITIVITY.png)을 생성했다. 기존2048개 joint draw의 결과를
   재사용했다. Gamma=2라는 가정에서 기존 working interval
   [0.146973,0.956543]은[0.041295,0.988770]로 넓어진다. Gamma는 측정값이 아니며
   물리Q의 domain과 물리Pi는 미확보다. 그 외부구간[0,1]을 유지한다.
3. **Pantheon 관측식 구별:** pinned 저자 likelihood는 zHD,zHEL,m_b_corr를 함께
   사용한다. 기존651행 중645행의zHD는zCMB와 다르고556행만SN-only zHD>0.01 cut을
   통과한다. 두-redshift chain rule을 유도·Wolfram 검산했다. 실제PV/standardization
   보정의 물리응답은 아직 필요하다. 공개total covariance를 중복 소비하지 않는다.
4. **실제PR4 A/B 관측자료:** 공식IRSA의R4.00 year-1-3/year-2-4 지도를 취득했다.
   각503,326,080bytes이며 header가npipe6v20A/B,Galactic,NESTED,COSMO,K_CMB를
   명시한다. 모든T/Q/U pixel의 유한성과 sentinel을 검사했다. 공식PR4 ns16 mask도
   취득했다. 공식 RIMO archive의 정확한 `030Ax030B` T/E/B beam과 spectrum window도
   검증했다. 신규 8개 payload는 총 **1,241,866,173 bytes**다.
   [자료 보고서](data/REPORT.md)와 [추가 manifest](data/ACQUISITION_MANIFEST.json)가
   실제 제품·hash·규약·실패경로를 기록한다. 이 spectrum window만으로 map 처리법이나
   foreground/null 법칙이 정해지지 않는다. 원래 PR3 L03과 PR4 coverage는 HOLD다.

## 필요한 관측자료와 물리 입력

| 노드 | 필요한 정확한 입력 | 확보·미확보와 다음 행동 |
|---|---|---|
| F04/V03 | zHD,zHEL,표준화magnitude의 물리변화에 따른 보정응답; normal/CMB/source frame; 유한 remainder | 저자필드·likelihood·rowcut 확보. PV보정과magnitude 표준화의 derivative 및 물리광학잔차를 자격화한 뒤 새투영 |
| H02/S02/S04/K04 | 전체HI parent targeting·검출·기각·quality, SN-ID→host→group 전체 contributor, 교차조사 calibration/velocity/selection joint law | 관측표·제한대상·노트북 재사용. 전체부모와공동법칙 또는 물리적으로 정당한 importance/support/event 경계 필요 |
| F06/별도PR4 | 정확한관측A/B, 같은처리beam·mask·foreground·CMB/잔차 정의와 통계량별공동null | 관측split·규약·mask·정확한AB spectrum window 확보. foreground/처리operator와 coverage는미확보 |
| B02/V03 | 기존계산의 물리T/E/B all-m와global-history, IC·frame·단위·source metadata | 적격숫자payload 미확보. 온도fixture·논문그림·chain·코드는대체하지않음 |
| K03 | 실제source support의PM/NNR/clock 물리응답, spatial/frame/selection 공동오차와drift remainder | 기존Gaia1614173행·radio713개 재사용; position covariance로대체하지않음 |
| H04/K04 | grouped64 flow의producer origin/spacing/component/estimator 계약 | 기존SOURCE_CONFLICT 유지; 격자재다운로드나관례추측으로해소하지않음 |

B02/V03의 마지막 transfer는 관측catalogue가 아니라 외부의 물리계산 산출물이다.
새solver/ODE를 실행하지 않고 이미공개된 적격제품만 intake한다. 선정된각경로의
근거와 실패는[검색기록](SOURCE_SEARCH.md)에 남긴다. 인증벽은 우회하지 않는다.

## 실행·재개

원자료는Git밖`/mnt/extdrive/workdir/htt_open_data/research20261022/`에 있다.
실제`/dev/sda2` mount와2.3T 여유공간을확인했다. 파일별·누적상한은없으며,
아래명령에는`--budget-gib`를주지않는다. 기본2GiB reserve와streaming공간검사는유지한다.
기존receipt/hash가맞으면재사용한다.

```bash
.venv/bin/python scripts/htt_open_input_packet.py
htt_loop_manifest=docs/research_program/observational_publication_20261015/RESEARCH_LOOP_20261022/data/ACQUISITION_MANIFEST.json
htt_loop_data=/mnt/extdrive/workdir/htt_open_data/research20261022
htt_loop_ids=(PANTHEON_DISTANCES_README PANTHEON_ONLY_COSMOSIS_LIKELIHOOD PANTHEON_SHOES_COSMOSIS_LIKELIHOOD CF4_SN_EDD_ALL_COMPILATION_NOTEBOOK PR4_LFI30_OBS_YEAR13 PR4_LFI30_OBS_YEAR24 PR4_LOLLIPOP_NS16_MASK PR4_RIMO_TF_ARCHIVE)
.venv/bin/python scripts/htt_fetch_open_inputs.py --manifest "$htt_loop_manifest" --data-root "$htt_loop_data" --ids "${htt_loop_ids[@]}"
.venv/bin/python scripts/htt_fetch_open_inputs.py --manifest "$htt_loop_manifest" --data-root "$htt_loop_data" --ids "${htt_loop_ids[@]}" --fetch
.venv/bin/python docs/research_program/observational_publication_20261015/RESEARCH_LOOP_20261022/data/verify_sources.py
.venv/bin/python docs/research_program/observational_publication_20261015/RESEARCH_LOOP_20261022/data/pr4/verify_pr4.py
```

새입력이확보되면해당F04/F06/F07/F08 packet의물리 acceptance와대조한뒤종속노드를
계속한다. source_ready와scientific_ready를구분한다. 과거Gaia/radio/PR3/SDSS/97LP/
54history/432optical 캠페인을반복하지않는다. main merge와journal submission은하지않는다.

## 루프와 독립 검토

`physmath-research-loop1.3.0`의R1–R10 및해당C1–C10을사용했다. R1현재상태·계약,
R2원전/legacy,R3규약,R4후보,R5유도,R7Wolfram/유한계산은새근거로연결된다.
R6/C9은별도의fresh Astra read-only reviewer가맡는다. 구체적finding은하나의repair
episode로수정후targeted closeout한다. R8–R10/C10의최종판정은아래검토와checkpoint를
참조한다. stage수나자료취득은과학진척률이아니다.

세child요청: 이론Astra/xhigh, 구현Sol/high, 자료Sol/high; 별도검토Astra/xhigh.
parent포함동시최대4명,no nested,disjoint writes,parent만publish했다.
관찰된runtime identity는모두UNKNOWN으로보존한다. [CHECKPOINT.md](CHECKPOINT.md)가
재개상태와검증결과를기록한다. [독립 검토](INDEPENDENT_REVIEW.md)는
**SCOPED_PASS_C0**로 종료했다. 발견한 수치·정규화·명령 오류를 수정했고,
기존 `.venv`의 선택경계 검사 12개와 packet 검사 7개가 통과했다.
