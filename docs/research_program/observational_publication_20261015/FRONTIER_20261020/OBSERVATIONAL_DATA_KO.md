# 필요한 관측자료와 추가 다운로드량

2026-10-20 기준. 이미 처리한 Gaia전체표본, PR3split/beam, CF4/SH0ES/Pantheon, SDSS원천은 재사용한다. 전체 연구를 위한 추가 데이터 총량은 **아직 확정할 수 없다**. 미확보 물리 atlas와 공동오차 제품의 실제 파일이 정해지지 않았기 때문이다. 아래 수치는 전송량, Git 파일 크기와 최종 디스크 사용량을 구분한다. MB는10⁶bytes다.

| 자료 / 필요한 내용 | 해당 노드 | 공개 경로와 현재 확보 범위 | 추가량·조건 |
|---|---|---|---|
| CF4 SN contributor 원천: SN-ID→PGC→1PGC, 전체계보 | H02,S02,K04 | [저자 notebook](https://github.com/ekourkchi/CF4catalog/blob/2f4c23c8810c35b494bf4d7c86b38e114109a022/SNIa_groups-catal.ipynb), [새 NumCosmo fixture](https://github.com/NumCosmo/NumCosmo/blob/91ecab49a0b3c48846fd128cd8ada8c7ca6e0620/tests/python/conftest.py). 정확한6개 identity를 안전하게 추출 | 기본 source3파일75,833bytes. 전체 contributor export는 아직 없음, 크기미정 |
| 전체 HI parent targeting·검출·기각·품질 및 공동 보정·속도법칙 | H02,S02,S04,K04 | 기존628대상/TF/CF4 원천 재사용. 최근 joint forward model은 조건부 계약으로 활용 | 기존 원천 추가0bytes. 완전 parent·joint-law 신규제품 크기미정. EDD 인증벽 우회 안함 |
| Pantheon magnitude covariance와 velocity 모형의 일관된 결합 | H02,S04,K04 | 공개 total covariance를 한 번만 쓰는 deterministic-mean 연구 가능. 최근 논문의 latent-PV replay에는 별도로 제공받은 PV-removed 행렬 사용 | 조건부 연구 추가0bytes. 정확한 논문 replay용 공개 행렬/분해는 확보 못함 |
| Planck PR4 LoLLiPoP EE/BB/EB spectrum·covariance | P2의 별도 spectral 비교 | [공식6.22MB archive](https://portal.nersc.gov/cfs/cmb/planck2020/likelihoods/planck_2020_lollipop.tar.gz), 실제299×4표와897×897행렬 확인 | 6,217,890bytes. all-m morphology/qualified null을 대신하지 않음 |
| Planck PR4 NPIPE 동일00200의30GHz CMB A/B와 residual A/B | L03의 별도 release 연구 | [정확한4URL와header](cmb_astrometry/minimal_acquisition_candidate.json), 모두무인증HTTP200 prefix. CMB NESTED, residual RING | 첫 table extent합604,005,120bytes. 전체파일길이는미측정;4파일다운로드상한800MB. observed maps/mask/beam/foreground는별도이므로 전체실험 총량아님 |
| Gaia/radio proper-motion의 spatial·NNR·frame·clock 공동오차 및 비방사 response | K03 | 기존1,614,173Gaia/713radio 재사용. 공개 Karbon–Nothnagel position covariance도 찾았지만 PM공동오차가아님 | 현재분석추가0bytes. 필요제품미확보/크기미정; 약388–397M position행렬은 이목적으로받지않음 |
| 기존 계산의 물리적 polarized T/E/B all-m 및 global-history subset | B02,V03 | 새 Sung–Coles source도확인했으나64PS그림등71파일에serialized atlas없음. 해석적 제한 이력은별도유도 | 적격수치제품·크기미정. 그림·코드·chain을atlas로전환하지않음 |
| grouped64 flow producer origin/spacing/component/estimator contract | H04,K04 | 기존8convention비교실패재사용; 새공식계약미확보 | 격자재다운로드0bytes. 문서/기계metadata규모는미정 |

## 기본 자율획득 묶음

[현재 manifest](ACQUISITION_MANIFEST.json)은 기존 `scripts/htt_fetch_open_inputs.py`에서 그대로 읽힌다. 추가계정·로그인·결제 없이 공개HTTPS로 취득한다. 기존receipt와hash가맞으면재사용하고, 원본은Git밖에둔다. source코드와notebook은읽기/AST검사대상이며실행하지않는다.

- 원천3파일 + LoLLiPoP = **6,293,723bytes, 약6.29MB**. 모두없을때의실제확인길이합계다.
- 같은4제품의전송상한은 **8,300,000bytes,8.3MB**다. 압축해제·작업메모리는별도다.
- 모든파일이기존cache에있다면추가전송은 **0bytes**다. 소유자PC의cache존재는이세션에서확인하지않았다.
- PR4 quartet은기본목록에서빠져있다. Codex가frame/Q-U·제품정의·같은처리계약을스스로확인한뒤필요하면`--ids`로선택한다. 별도허가를다시묻는단계가아니다.
- 원전arXivHTML은자료제품이아니므로web/source도구로읽는다. raw-productdownloader는HTML오류페이지를거절한다. 거리worker의663,269bytes 재확인목록은HTML포함수치이므로여기기본묶음과같지않다.

```bash
.venv/bin/python scripts/htt_fetch_open_inputs.py --manifest docs/research_program/observational_publication_20261015/FRONTIER_20261020/ACQUISITION_MANIFEST.json
.venv/bin/python scripts/htt_fetch_open_inputs.py --manifest docs/research_program/observational_publication_20261015/FRONTIER_20261020/ACQUISITION_MANIFEST.json --fetch
```

이번 source조사에서 CMBworker가실제로읽은성공응답은12,695,326bytes였다(논문source·metadata·prefix포함, connector내부/실패응답전송량미측정). 거리worker의원천저장량1,181,937bytes는metadata와파생텍스트를포함하는디스크수치이며네트워크총량이아니다. 이번조사전체전송량을정확히측정했다고주장하지않는다. 이미완료된10.643GBSDSS나약2.416GBPR3split을새다운로드예산에다시넣지않는다.

후속 [frame binding](cmb_astrometry/FRAME_BINDING_ADDENDUM.md): pinned 공식 producer 코드에서 Galactic/COSMO 의도와 ordering 변환을 확인했다. 이는 header fingerprint를 포함한 source-supported inference이며 exact cache→PLA packaging 검증은 아니다. Codex는 이 가정을 명시한 탐색적 pilot 여부를 스스로 결정할 수 있다. full physical null 자격은 별도다.
