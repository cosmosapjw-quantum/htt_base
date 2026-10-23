# PR #561 다음 재개 — 2026-10-23

기존 `/home/cosmosapjw/Dropbox/bianchi/htt_base`, branch
`research/htt-open-input-theory-20261018`, draft PR561을 사용한다. intake는
`a8fd176305fb475947a46f9dacb651805d323741`; 검토된 기존checkpoint는d256ed46,
e638029f,9f0beb69,120c8a74다. 마지막SNcandidate 작성/검토base는120c8a74다.
이인계와최종검토를포함한게시commit의정확한HEAD는PR561metadata와git으로확인한다.
기존GR/CAS사용자수정·untracked상태를보존한다. 그것들은stage하지않았다.

먼저 AGENTS.md,CURRENT_CODEX_RUNTIME.md, 이directory README, 각실행의
INDEPENDENT_REVIEW.md와RESULT/sourceidentity를 읽는다. physmathloop현재설치1.3.0을
사용했다. 과거1.0/R9/UNKNOWN/one-use기록을재작성하지않는다.

실제완료한하위결과:

- A22-03 Quaia755850PM covariance연결(기존692154+새63696subset).
- A22-04 유한spectral/두redshift/Carr성분; 추가SN010010실제photfit과pairedMW.
- A22-05 3reported-z E1/B1+commonhigherVSH/templates,32properGaussianmodels,
  PSD/densechecks와whole-fieldmocks. 빠진l4/template평균coverage .28418/0 실패.
- A22-06 mark-only628targetlaw,274present/354missingcompletion,6dFmembership,
  Gaussianselectiontailhelper. F_or와physicalparent/jointlaw는미완료.
- A22-07 legacyblob16b1b...3counterpair동등성, 새orderedJ234/topaxis,1skyID.
- A22-08 conditionalsecondaryQUwindow operator30primary+15comparator;
  physicalnull gate는blocked_input. 원래L03을PR4로이름변경하지않았다.

SN010010 baseline은χ²/19=3.2323으로사전<=3screen실패,공개summaryparity도
미재현이다. 숫자를맞추려고cuts/errors/model을변경하지않는다. CovariantMWfit항등식과
frozenMW의조건부응답은이미계산했다. 이모형의globalBBC/PV응답은UNKNOWN이다.

상태: revisedV03scope18/42(42.86%), originalexternaloutput17/42(40.48%).
PUBLICATION_DAG.json은intake대비변경하지않았다. 여섯논문NOT_READY_TO_SUBMIT.
남은24개가S02,S04,L03,H02,B02,K03,K04의실제미확보입력에모두연결된다.
scientific-ready=0만으로멈춘것이아니라,새Quaia/6dF/SNsource와새이론/통계/처리
하위결과를실행·검토한뒤각missingpayload를[현재입력표](REMAINING_INPUTS_KO.md)에남겼다.

실행검증:7개narrow suites합계30PASS,collect-only30. 독립검토와구체적finding의
한번targetedcloseout은각directory에있다. 최초tail계산오류,FP30degboundary,
parser/reference오류와physicsadequacy실패를보존한다. 추가전체Gaia/97LP/Planck
8pair/651projection/64SDSS/54history432optics를변화없이재실행하지않는다.

다운로드raw는`/mnt/extdrive/workdir/htt_open_data`에 있으며 Git 밖에 저장한다.
actualmount/dev/sda2→/mnt/extdrive rw,마지막available2480014905344bytes.
과학resource109327188bytes추가,package/APImetadata별도. 제품/누적cap없음;
--budget-gib생략,2GiBreserve/streamspacechecks유지. 기존receipt/hash/payload우선.
SNtools는`/mnt/extdrive/workdir/htt_open_data/a22_20261023/tools`에설치했다.
부모requestedgpt-6.1-sol/high;theory/reviewerrequestedAstra/xhigh,backendobservedUNKNOWN.
부모만writer/publisher,동시최대4,nested없음. 제거된CUHG를재생성하지않았다.

새정확한payload나공동법칙이생기면해당node의미변경acceptance부터검토한다.
재개첫명령:

```bash
.venv/bin/python scripts/htt_open_input_packet.py
```

그뒤`--node H02|S02|K03`또는`--task A22-08|A22-09`를하나씩선택한다.
새입력없으면같은검색/fit/diagnostic을반복하지않는다. nativeBianchisolver/ODE/
Einstein–Boltzmannevolution,mainmerge,journalsubmission은허용하지않는다.
