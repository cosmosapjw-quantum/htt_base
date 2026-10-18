# PR #534–#559 검토

기준 2026-10-18, 이전 완료 #533 이후 26개 PR. 각 PR의 현재 head/base/state와 본문을 읽고, 핵심 scientific source를 선별하여 코드·결과·입력 계약을 검토했다. 아래는 전 diff에 대한 merge 승인이나 전체 재실행 감사가 아니다. 새 분석에 실제 사용한 source는 P1/P2/P3 보고서에 별도로 고정한다. 최신 #559 head는 `967ef7c8f0b132ecaaba343045d333d4ebf299c1`다.

| PR | 현재 head | 검토와 후속 조치 |
|---|---|---|
| [#534](https://github.com/cosmosapjw-quantum/htt_base/pull/534) HTT-STF-01 [DRAFT]: preserve CF4 apparent STF scalar normalization repair and dirty-loop evidence | `635e5e83a50f` | scalar 정규화 수정. apparent STF→physical shear bridge 미승인 유지. |
| [#535](https://github.com/cosmosapjw-quantum/htt_base/pull/535) HTT-C8-OBS-MES-EPS: source-locked Planck/FFP low-ell processing diagnostics and local handoff | `2752a927c191` | paired FFP 제품을 독립 skies로 세지 않는 처리 조건 확인. |
| [#536](https://github.com/cosmosapjw-quantum/htt_base/pull/536) C8-SMICA-FINITE-RESPONSE: source-bound masked harmonic response | `37db458319fd` | 실제 SMICA finite response 출발점; ell 범위의 한계 유지. |
| [#537](https://github.com/cosmosapjw-quantum/htt_base/pull/537) C8-ELL17-32 [DRAFT]: source-locked finite-shell bounds and streamed sandbox validator | `f85bb82ecdb3` | 17–32 finite shell은 전체 고차 tail bound가 아님. |
| [#538](https://github.com/cosmosapjw-quantum/htt_base/pull/538) C8-POWER-ENVELOPE [DRAFT]: real SMICA masked-response covariance and sharp finite power bounds | `fed86da78de1` | power-envelope는 허용된 covariance/범위에 조건부. |
| [#539](https://github.com/cosmosapjw-quantum/htt_base/pull/539) C8-POWER-LOCAL: source-locked finite tail and conditional envelopes | `b3ab923e6931` | local finite-tail 수치와 physical anomaly p를 구분. |
| [#540](https://github.com/cosmosapjw-quantum/htt_base/pull/540) HTT SIX-PAPER P3/H01: CF4 source-window Hubble working-law response and publication-DAG progress | `8e5bb45dddd5` | H_W survey-window 정의; Theta/3 대입 금지. |
| [#541](https://github.com/cosmosapjw-quantum/htt_base/pull/541) HTT Six-Paper P3/H03 [DRAFT]: source-locked redshift STF2 tomography and correlated windows | `2a5d47b2f6af` | 실제 H03 θ 및36×36 covariance를 이번 P1에 직접 재사용. |
| [#542](https://github.com/cosmosapjw-quantum/htt_base/pull/542) HTT Six-Paper P2/L01 [DRAFT]: source-locked Planck T/E/B response ledger and spin-2 masked leakage | `1d9222ec7240` | 공통 source T/E/B 비교; 9 products 독립 skies 아님. |
| [#543](https://github.com/cosmosapjw-quantum/htt_base/pull/543) HTT Six-Paper P1/S01 [DRAFT]: typed partial functionals and sharp missing-mass envelopes | `eac75859f38b` | signed/undefined functional contract 재사용. |
| [#544](https://github.com/cosmosapjw-quantum/htt_base/pull/544) HTT Six-Paper READY siblings [DRAFT]: source IDs, selection history, finite boosts and 1+3 radial identifiability | `da712f30605f` | source/selection/frame/radial 기초의 scoped 완료를 재사용. |
| [#545](https://github.com/cosmosapjw-quantum/htt_base/pull/545) HTT Six-Paper X02/K02 [DRAFT]: CF4 conditional rank, Planck leakage and physical input precursors | `c352bcfbf4d7` | prior-art/rank 비교의 완료가 논문 신규성 승인은 아님. |
| [#546](https://github.com/cosmosapjw-quantum/htt_base/pull/546) HTT Six-Paper [DRAFT]: exhaustive 3-week PR inventory and open-source physical-input gate research | `109a864989d1` | 입력 inventory의 존재와 실제 입력 적격성을 구분. |
| [#547](https://github.com/cosmosapjw-quantum/htt_base/pull/547) HTT seven physical input gates: legacy repair theory and open-data local download harness [DRAFT] | `b942c4dba6c8` | 일곱 physical gates는 데이터 없는 임의 prior로 해소 불가. |
| [#548](https://github.com/cosmosapjw-quantum/htt_base/pull/548) HTT six-paper idle-data theory [DRAFT]: shared selection, sky null, observer rank, exact Bianchi-I bridge | `be2e0ac32f9f` | selected-law/observer-rank/Bianchi-I benchmark의 제조 예제 범위 유지. |
| [#549](https://github.com/cosmosapjw-quantum/htt_base/pull/549) Fix HTT CF4 CDS 404 download: gzip candidates, verified VizieR fallback and immutable Planck masks [DRAFT] | `5a83a165449a` | 기존 CF4 endpoint 복구를 반복하지 않음. |
| [#550](https://github.com/cosmosapjw-quantum/htt_base/pull/550) HTT CF4 post-recovery H02/L01 [DRAFT]: full-source local auditor, 35,970 method-sky evidence and six PR3 mask gate | `d9089205c50d` | 35,970 selected groups의 실제 source/method/sky 근거 재사용. |
| [#551](https://github.com/cosmosapjw-quantum/htt_base/pull/551) HTT six-paper H02/L03 [DRAFT]: real CF4 angular calibration Fisher gauge and paired Planck finite-source scan | `6c97e3be2fae` | calibration gauge와 실제 Gram/Fisher 수치 직접 검토; 새 P3 범위 계산. |
| [#552](https://github.com/cosmosapjw-quantum/htt_base/pull/552) HTT six-paper L01/S02 [DRAFT]: sharp Planck T high-ell inverse and coupled CF4 signed interval functionals | `41178623ae9e` | 공동 source nuisance를 보존하는 inverse/interval 범위 재사용. |
| [#553](https://github.com/cosmosapjw-quantum/htt_base/pull/553) HTT six-paper L01/S02 [DRAFT]: real R8 T-mask spin2 pilot and source-coherent CF4 transfer bounds | `ad5dcaffd471` | coherent 2048 draw 근거를 이번 P1에서 재현. |
| [#554](https://github.com/cosmosapjw-quantum/htt_base/pull/554) HTT six-paper P2/L01 [DRAFT]: separate OE FITS byte provenance from PMASK semantics; masked spin-2 response theorem | `22fb82e4112c` | typed identity는 과학 법칙의 대체물이 아님. |
| [#555](https://github.com/cosmosapjw-quantum/htt_base/pull/555) HTT six-paper P2/L01 [DRAFT]: opt-in OE v2 source lock, source-tested PMASK geometry path | `d80309c542af` | 원본 PMASK ordering/support를 고정한 근거 재사용. |
| [#556](https://github.com/cosmosapjw-quantum/htt_base/pull/556) HTT P2/L01 [DRAFT]: native Planck PMASK spin-2 E/B spectral certificate and sharp finite leakage bounds | `cdfb86b8b9fb` | native finite K의 numerical rank와 exact certification 구분. |
| [#557](https://github.com/cosmosapjw-quantum/htt_base/pull/557) HTT P2/L01 [DRAFT]: real Planck POL mask difference decision and R8/C8 spectral stability | `c4cf4ec1bcf7` | ΔK geometry는 실제 연산자 결과이며 우주론적 검출 아님. |
| [#558](https://github.com/cosmosapjw-quantum/htt_base/pull/558) HTT P2/L01 [DRAFT]: R9 same-sky identification, C9 beam/covariance adapter and official PR3 source fetch | `5dc7ffefcfbc` | same-sky covariance/beam 순서 의무 유지. |
| [#559](https://github.com/cosmosapjw-quantum/htt_base/pull/559) HTT P2/L01 [DRAFT]: R10/C10 repo import recovery, checked SMICA HTTP resume and split-source handoff | `967ef7c8f0b1` | 최신 full matched fit 수치로 새 sharp geometry 계산; split 실행은 미수행. inherited CI 등록 오류 재현·수정. |

## 해결한 결함

1. `policy.strict_extension_cards`에 이미 존재하는 solver-free 카드 네 개가 빠져 실제 strict CI가 실패했다. 기존 validator에서 같은 실패를 재현한 뒤 네 항목만 등록했다. 카드245개, depends, completed/pending 상태, receipt는 바뀌지 않는다. 동일 strict 검증은 통과했다.
2. publication validator는 terminal node의 목표가 readiness decision인데도 어떤 terminal completion도 거절했다. 증거가 있는 HOLD/READY_FOR_OWNER_REVIEW와 submitted=false만 허용하고, 완료 prerequisite를 강제하도록 수정했다. 현재 실제42개 상태는 유지한다.
3. 기존 native runbook/guard의 새 worktree 권고는 현재 primary-checkout 정책과 충돌한다. 이번 실행 안내는 기존 checkout과 명시적 ref 검증을 사용한다.

## 남은 실행 제약

현재 Desktop Commander는 월 usage limit을 반환했다. 재연결·재시도로 우회하지 않았고 사용자 primary checkout은 읽거나 변경하지 않았다. Native full/split FITS 및 healpy 실행은 NOT_RUN이다. GitHub에 저장된 exact source와 충분통계를 scratch에서 계산한 결과만 이번 실행으로 표시한다.
