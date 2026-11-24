# R112 Native Bianchi Rust bounded development

원본 세 연구 브랜치에서 직접 구현하고 원격 게시한 결과를 기록한다.
기존 R111 핀과 기존 증거, R78 과학 DAG 및 htt_base 작업 디렉터리의
관련 없는 변경은 수정하지 않았다.

| owner | commit |
|---|---|
| BASS | 40626723bcee34b3c02d1827344b2ee5ac3b368d |
| REC | 3752213099ccb35998c22f1aaf0d42fb674184e4 |
| REI | 503508f1c82a968bebc57900d43a65135c3db185 |

BASS 연구 기록: research/r112_native_bianchi/README.md, run_smoke.py,
results.json (위 BASS commit). BASS manifest/lock이 위 REC/REI를 정확히 핀한다.

R1–R10/C1–C10: bounded stage ledger는 BASS README 참조.
구현: 비대칭 normal-frame rest-mass baryon/CDM fraction, 일반 Lie
characteristic을 이용한 tilted material Sobolev rate, native REC
two-temperature pointwise source와 matched hydrogen RHS, REI 명시적
저적색편이 history 접합. REC/REI의 기존 default 경로를 유지한다.

BASS 197, REC 127, REI lib/tests 271 PASS. REI unrestricted tests는
기존 paired_history 예제의 누락된 science_scenario_v1.json 때문에
blocked; bass_ionization 예제는 빌드·실행되었다.
12 Bianchi families + FLRW control + generic class B custom Lie,
VIstar 16/32/64 step refinement. All-m finite, product/reality exact
in emitted values; five legacy output files byte identical in one case.
Synthetic REI tail was consumed by BASS; not a physical ionization solution.

Status: implementation-verified for the stated bounded cases.
Frequency-resolved radiation, stiff self-consistent hydrogen/helium/Tm
feedback, low-z source/SED/absorber evolution, long/high-l convergence,
general inhomogeneous covariance remain open. No native subagent reviewer.
No scientific DAG promotion.

Next ID: R113-NATIVE-MATERIAL-REC-COUPLED-01.
