# 남은 원래 acceptance와 실제 입력 — 2026-10-23

수정 V03 범위18/42, 원래 외부 산출물 기준17/42. 여섯 논문 모두
NOT_READY_TO_SUBMIT이다. A22 하위 결과의 scoped PASS는 원래 노드 완료가 아니다.
과거 HOLD/UNKNOWN/R9, 실패와 one-use allocation을 보존한다.

| 원래 frontier | 정확한 missing payload/formula | 확인·재사용한 경로 | 입력 후 소비자 |
|---|---|---|---|
|S02|같은 congruence/frame의 optical→kinematic 응답, finite-z/flow remainder, 방향·선택 공동오차|기존2048coupled draws/minimax, V03 제한 볼로미터 광학식, A22-04; physical Q unknown mass1|S03–S06|
|S04|동일 상태의 선택 likelihood 또는 정당화된 physical outer interval|A22-06의 mark-only likelihood와 released-DM completion은 물리 거리 요인·parent법칙을 공급하지 않음|S05–S06|
|H02|parent targeting/탈락/검출/관측 history와 shared calibration/PV/group·기여자 중복 공동법칙|20fitblocks,628HI outcome,CF4join,새6dF8885/11102membership;5460parent inclusion확률 미확보|H04–H06,K04–K06,V04–V06|
|L03|PR3full/HM/OE 동일 operator의 processed total CMB+foreground+noise 공동법칙과 whole-sky realizationIDs,해당 통계량 coverage|4split/8paircache,기존FFP10,별도PR4A/B+QuickPol spectrumwindow; A22-07출력 counterpair는 null 아님|L04–L06,B03–B05|
|B02|기존 physical T/E/B all-m family/history atlas,IC/mode/frame/단위/equivalence,동일 source calibration|Sung–Coles71archive/64PS/수치map0,Planck2015 private VIIhtemplate,온도-only코드;solver새실행금지|B03–B05|
|K03|same-latent-state PM/NNR/clock kernel와 spatial/selection 공동오차 또는 bound|Gaia/Quaia755850PM,A22-02observer a_obs,A22-05조건부E/B; cosmic A/omega/beta와 구분|K05–K06|
|K04|CF4 apparent STF→physical kinematics common-frame map,selection/calibration/finite-z법칙|A22-06과groupedCF4 64^3; producer origin/spacing/components/estimator SOURCE_CONFLICT|K05–K06|
|V04/V05|V02CMB와V03광학 공통operator/단위/frame, 전체SALT2/BBC kappa 및 PV/group eta remainder,선택공분산/주입 coverage|A22-04합성source의pairedfit+Carr성분bound. 전체경험적remainder UNKNOWN|V06,H04|

새 primary 확인(기존 검색을 반복하지 않은 product 가설):

- [Planck2018 component separation](https://arxiv.org/html/1807.06208)은 처리와
  FFP10 문서이며, 요구한5product의 full joint total/null payload 자체가 아니다.
- [ESA Component Maps DOI](https://esdcdoi.esac.esa.int/doi/html/data/astronomy/planck/Component_Maps.html)
  route는503을 반환했다. 관측 foreground map의 존재와 matched joint null law는 별개다.
- [Planck2015 XVIII](https://doi.org/10.1051/0004-6361/201525829)의 polarized VIIh
  templates는 private communication이며 공개 all-family/history atlas를 확인하지 못했다.
- [고정 Pantheon+ release](https://github.com/PantheonPlusSH0ES/DataRelease/tree/c447f0fea703fcd0fff57de5000947b5ca81286b/Pantheon%2B_Data)는
  실제 multi-band lightcurves,filters/KCOR,header overrides,MODEL000와Pippin을
  공개한다. 이는 새로 실행 가능한 per-SN 조건부 경로다. **진행 중이며 blocker로
  닫지 않는다.** 모델 directory B21 이름과 논문 B22b 이름은 exactfiles로 구별한다.
  전체BBC biascor는README가저자연락을 요구하고Pippin에localproducerpath가있다.
  전체global alpha/beta/host/bias/selection및PV/group response는별도미확보이다.

64라는 수를 혼동하지 않는다: 기존64SDSS fit은 C0 source-only 진단이고,
별도groupedCF4 64^3grid의8convention비교는0/6printed-row 일치를 보존한다.
둘 다 변화 없이 재실행하지 않는다. EDD authentication/challenge를 우회하지 않는다.

재개 명령은 입력을 얻은 뒤 해당 packet의 실제 acceptance와 identity를 먼저 읽는다:

```bash
.venv/bin/python scripts/htt_open_input_packet.py
.venv/bin/python scripts/htt_open_input_packet.py --node S02
.venv/bin/python scripts/htt_open_input_packet.py --node H02
.venv/bin/python scripts/htt_open_input_packet.py --node K03
.venv/bin/python scripts/htt_open_input_packet.py --task A22-04
.venv/bin/python scripts/htt_open_input_packet.py --task A22-08
.venv/bin/python scripts/htt_open_input_packet.py --task A22-09
```

Parent-only writer/publisher. Source research requested Sol/high; observedUNKNOWN.
다운로드는 기존receipt우선,공식/저자/CDS무인증 경로이며raw는Git밖에 둔다.
추가신규payload가실제수용기준을충족하면원래node와종속ready노드를계속한다.
