# HTT 6개 논문 DAG: P2/L01 로컬 Codex 직접 실행 인계

**사용자 다운로드나 수동 shell 작업이 필요하지 않다.** 기존 `/home/cosmosapjw/Dropbox/bianchi/htt_base`와 GitHub `cosmosapjw-quantum/htt_base`, [PR #542](https://github.com/cosmosapjw-quantum/htt_base/pull/542)를 읽어 필요한 소스와 연구 코드를 직접 찾아 실행한다.

1. `AGENTS.md`와 42노드 6개 논문 `docs/research_program/observational_publication_20261015/PUBLICATION_DAG.json`을 먼저 확인. S1/S2 artifact는 stacked PR #542 `L01_20261016/`; 기존 P3/H03 #541 및 dirty checkout 상태를 보존. 새 Git worktree/clone, reset/clean/force checkout 금지.
2. L01 `src/run_local_replay.py --repo-root /home/cosmosapjw/Dropbox/bianchi/htt_base --output-dir <new-create-only-dir>`를 호출해 원본 Loop5/8/9/12와 FFP source NPZ를 정확한 SHA로 읽고 수치 JSON identity 및 17개 테스트를 검증. 파일이 없으면 다른 source로 대체하지 말고 `MISSING_SOURCE` 기록. 설정·의존 경로 변경 전 diff/ownership 확인.
3. 진짜 남은 연구목표: 로컬 원본 `scripts/run_htt_planck_multisplit_spin_20261015.py`의 `native_mask()`와 `spin2_design_real(nside=64,lmax=5)`를 사용해 공식 common/HM/OE **Pol PMASK**를 NSIDE2048 NESTED에서 NSIDE64 RING으로 변환. `sel_p`를 Loop5 원본과 비교하여 정확히 30,021개, source SHA 및 ordering/coordinate/units를 검증.
4. 실제 source 선택에서 `spin2_design_real(nside=64,lmax=8)`를 새로 만들고 \(S_L\)는 ℓ2–5의 64개, \(S_H\)는 ℓ6–8의 90개 열로 분리. 이 때 배열은 원본이 `[ell,E then B, real m0/cos/sin]`이므로 index와 부호를 직접 검산. 서로 독립적인 injection test, QR vs `lstsq`/SVD, `K=R^-1 Q^T H`, `K_E<-B`,`K_B<-E`, mask cardnality and permutation metamorphisms, stability spectrum을 검산하라.
5. 생성되는 것이 **source-specific finite POL geometric operator**이지 Planck beam/foreground/reconstruction end-to-end transfer나 physical primordial B/EB likelihood가 아님을 명시. 온도는 이미 real `K6..32`가 있으므로 중복 계산하지 말고 실제 source-bound NPZ와 비교.
6. 독립 reviewer가 실제 가능하다면 read-only fresh context에서 phase/frame/sign/rank/selection evidence를 검토. reviewer identity 실제 관측값만 사용; 사용할 수 없으면 `NOT_RUN`.
7. 증거를 새로운 `L01` S3 부록으로 별도 보존하고 테스트 출력·입력 SHA·새 K NPZ·수치 결과·실패 내역 기록. 유효한 source K/E/B 고차 경로와 acceptance가 확보되어야만 **6개 논문 정본 DAG의 L01 상태를 `completed_scoped`로 전환**. 그 전엔 `pending + existing_evidence`로 유지. P1/P3/P4/P5/P6 status, 245카드 canonical DAG와 manuscript 제출 gate를 변경하지 마라.
8. 독립 게이트를 통과한 별도 소스·테스트·수치 결과를 PR #542 위의 new draft PR 또는 동일 리뷰 작업의 안전한 successor에 게시하고, Dropbox/Library 이중백업·원격 PR/branch SHA·DAG 해시·다음 READY를 보고하라. 메인 병합/투고 불허.

실제 mask 파일 이름, hash 등록과 LoS spin response source 경로는 Loop5 `run_htt_planck_multisplit_spin_20261015.py`, source run의 native_mask/fine mask policy를 기준으로 한다. Raw E/B maps를 새로 다운로드할 필요 없이 기존 소스와 설계 연산자부터 진행할 수 있다. 원본 `SMICA_noSZ_FULL`의 편광을 0으로 채우지 마라.
