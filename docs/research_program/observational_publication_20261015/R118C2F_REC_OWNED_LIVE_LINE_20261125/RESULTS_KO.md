# R118-C2F: REC_BIANCHI 독립 실행과 calibrated live resonance

사용자 요구: HyRec runtime/history와 독립적으로 구동. 검증된 primitive atomic rate table 및 상수는 변형 필요 없으면 원전 그대로 상속한다. REC의 독립 H-only HMLA+Tm 이력, QSS ground population, 직접 상태별 COM-KHW scalar source compilation, equilibrium-aware native BE 및 local exterior live transport를 구현·검증했다. REC 자체 소스, 실행파일, 세 원본 rate table만 있는 입력 tree에서 전체 독립 실행을 확인했다 (Python audit, OS sandbox는 아님). 별도로 prescribed LRS Bianchi I native TLA/W 12 cases/5760 steps를 reference correction 없이 실행. 65 line cases/209 steps, REC Rust 145 + Python targeted 25, BASS 274 + examples 3 통과. 기존 BASS dual_source의 구현 소유권을 REC에 귀속시키고 exact Git pin으로 연결했다. 첫 BASS 회귀의 이전 pin 기대값 실패 1개는 새 pin으로 교정해 재검증했으며 실패 로그도 보존했다. 원래 rate archive byte unchanged.

REC commit 7fe5017c195fbf4ff4619c5c69b6eae364fe728b / BASS 101b4d5c648a93bd869393beff61102e264f6c2e. 원시 검증 자료와 실패 trial, 정량적 오차 및 실행 명령은 REC research/r118c2f_standalone 및 docs/REC_RUNTIME_OWNERSHIP.md 참조. BASS의 기존 matched production default는 유지. 이번 독립성은 H-only neutral-He HMLA + frozen-bath scalar live-line 및 별도 reduced TLA prescribed background에 한정한다. 일반 angular state-dependent redistribution, full H/He chronology, native virtual exterior ownership swap, coupled thermal/population feedback은 미해결. 기존 overlapping atomic terms는 제거하거나 중복 적용하지 않았다. REI/R78 변경 및 science promotion 없음.

다음: R118-C2G-REC-OWNED-ANGULAR-LINE-AND-ATOMIC-OWNERSHIP-01.
