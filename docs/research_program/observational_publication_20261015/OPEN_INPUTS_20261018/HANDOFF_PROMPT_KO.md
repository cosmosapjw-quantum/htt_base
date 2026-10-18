# Codex 실행 handoff — 복사해서 시작

권장 기본모델 gpt-6.1-sol/high, 핵심이론·독립review gpt-6-astra/xhigh, 제한된metadata작업 gpt-6-luna/medium. 현재환경에노출된설정을확인한다. 아래명령은최종게시branch에서실행한다. public자료의자동취득은이미사용자가허용했다.

```text
저장소 cosmosapjw-quantum/htt_base의 6개 논문 연구를 이어서 실행하라.
기존 primary checkout /home/cosmosapjw/Dropbox/bianchi/htt_base를 사용한다.
이번 continuation branch는 research/htt-open-input-theory-20261018이다.
intake 부모 HEAD는 4a68995507bf8e672b2551d9030f3ad9f0d2152e이다.
실행할 실제 branch HEAD는 origin에서 확인하고 기록하라. 부모 SHA를 새 tip으로 오인하지 말라.
새 clone/worktree를 만들지 말고 사용자 수정과 기존 원본·실패 기록을 보존하라.

최종 goal: 원래 PUBLICATION_DAG.json의 42개 노드 각각을 원래 acceptance에 따라
실제 연구·검증·결과·그림·보고서로 완성하고 여섯 논문의 준비도를 각각 판정하라.
목표를 작업별로 세운 뒤 하나 끝나면 다음 실행 가능한 목표를 골라 같은 세션에서 계속하라.
계획이나 감사 문서만 쓰고 멈추지 말라. 기존 완료실험을 불필요하게 반복하지 말라.

먼저 AGENTS.md, docs/harness/CURRENT_CODEX_RUNTIME.md와
 docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/README.md
 HANDOFF_PROMPT_KO.md, CONTINUATION_TASKS.json, ACQUISITION_MANIFEST.json,
 OBSERVATIONAL_DATA_KO.md, PUBLICATION_CANDIDATES_KO.md, VERIFICATION.md를 읽어라.
직전 실제상태는17/42완료,8직접외부입력,17의존대기이며 모든논문NOT_READY_TO_SUBMIT이다.
원래42노드의실시간상태를다시읽고 이 숫자를고정된테스트기대값으로만들지말라.

native solver 구축이나 ODE 적분은 하지 말라. 기존 코드·유한선형대수·통계·관측처리와
이미 계산된 공개 외부 transfer만 사용한다. dossier의 quotient/identified-set 논리를
실제 자료·단위·frame에 연결하되 physics 입력의 빈자리를 synthetic success로 채우지 말라.

외부 관측자료가 필요하면 local에서 스스로 다운로드하라. 사용자 추가승인을 반복요청하지 말라.
공식 공개 HTTPS, 인증·결제 없는 경로부터 사용하고 원본은 Git 밖
/mnt/extdrive/workdir/htt_open_data에 저장하라. manifest의 --fetch를 실행하고
기존 receipt/hash가 맞는 자료는 재사용하라. 기본batch2GiB, 큰split세트4GiB, 여유2GiB를
기준으로 필요공간을 확인하고 chunk별 처리하라. 인증벽은 우회하지 말고 공개대체경로를 찾으라.
업스트림 코드를 자동실행하지 말고 자료/가중치/스키마만 먼저 읽어라. 깨진 HTML/LFS pointer,
잘린 TAP응답, 부분FITS를 완전한 자료로 취급하지 말라. 새 downloader는 자동resume가 없으므로
전송실패시 partial을보존하고 Content-Range/ETag/길이를검증하는복구를선택하라.

자료획득 ready와 과학 ready를 별도로 운영하라. 과학 ready=0이어도 공개자료 취득·조인·이론
해소가 가능하면 진행한다. D01에서 시작하고 독립lane D02/D03/D04/D05를 자원에 맞춰 수행하라.
D09의lane 목록은전체완료를기다리는barrier가아니다. 어느원래노드든실제의존성이풀리면즉시실행한다.

우선순위:
1. GBT628대상 결과를 기존TF/CF4 PGC→group에 연결해 bounded cohort selection을 모형화한다.
2. Pantheon+1701행과전체covariance를 CF4/SN/calibrator에 교차연결한다. 동일CID/상류보정 의존성,
   rawcovariance3e-8mag²비대칭과 명시적symmetric-part 처리를 기록한다.
3. 기존L01/L02/V02와8paircache를재사용하고 공개HM1/HM2/OE1/OE2 ID00000 noise를 확보한다.
   simulation번호=sharedseed/독립성을 가정하지 말고, splitCMB/beam/foreground/selection법칙을 구분한다.
4. GaiaCRF3전체 proper-motion/covariance와VLBA713을 취득한다. TOP2를전체자료로쓰지말고,
   TAPoverflow·회원행수·프레임제작/NNR·공간상관을검증한다. 관측VSH와cosmiccurl을구분한다.
5. 보정앵커 정리에서 raw anchor는 eta+gamma_m를측정한다. methodgamma를joint로전파하거나
   알려진보정을제거한경우에만 eta로사용한다. .001759mag목표는known-gamma이상설계이지 실제성능아니다.
6. 수정CF4/CF4++flow를 동일자료에의존하는대체모형으로 사용한다. mean/rms를jointdraw로만들지말라.
7. V03/B02는이미계산된적격global-history/polarizedall-m숫자payload를계속찾아intake한다.
   영상·코드·chain을atlas라고부르지말고 solver를만들지말라.

parent 포함 최대4 nativeagents, nestedagent없음. 파일별단일writer, fresh boundedpacket을 사용한다.
기본worker Sol/high, 핵심이론과별도독립reviewer Astra/xhigh, 명확한metadata Luna/medium을권장한다.
요청model/effort와관찰runtime을분리하며관찰불가면UNKNOWN으로기록한다.

각 coherent increment마다 실제 command/result/source identity를 기록하고 집중검증과
한번의독립review를수행하라. finding을고친뒤동일reviewer의targetedcloseout으로닫아라.
원래acceptance를실제로충족한노드만완료처리하고필요한canonicalqueue/status를동기화하라.
검증된결과·코드·그림·문서를push하고draftPR을연다. mainmerge나저널제출은하지말라.
조건부결과와향후가능결과의목록을갱신하고 각논문의distinct기여/선행연구/coverage를검토하라.

모든노드완료 또는 남은모든lane에실제외부입력장벽만남고 공개대체조사와가능한부분연구까지
소진될때까지계속하라. 전체완료를보장하려고가정·수용기준·HOLD/UNKNOWN을바꾸지말라.
실제외부장벽이면정확히무슨payload/조건이필요한지와재개명령을남기고완료라고쓰지말라.
context가차면최소checkpoint로현재goal·완료증거·다음행동을보존하고동일목표에서재개하라.
```

첫 명령:

```bash
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
git status --short
git fetch origin research/htt-open-input-theory-20261018
# 사용자수정을보존할수있음을확인한뒤existingbranch로switch한다.
# 로컬branch가없으면위remote를tracking하는branch를이primarycheckout에서만든다.
.venv/bin/python scripts/htt_publication_dag.py --validate
.venv/bin/python scripts/htt_sixpaper_goal_packet.py --frontier
.venv/bin/python scripts/htt_open_input_packet.py
.venv/bin/python scripts/htt_fetch_open_inputs.py --fetch
```

프롬프트가 외부입력을 자동으로 만들어 주거나 context 밖에서 영구 실행을 예약하지는 않는다. 이 명령은 해당 Codex 세션에서 실제 작업을 이어 가도록 하는 지시이며, 실행 불가능한 마지막 의무도 정확히 보존한다.
