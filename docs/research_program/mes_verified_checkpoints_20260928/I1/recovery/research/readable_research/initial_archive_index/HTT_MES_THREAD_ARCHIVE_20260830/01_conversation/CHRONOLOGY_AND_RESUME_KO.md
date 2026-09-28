# 보존용 흐름·재개 지점 — 새 연구 판정 아님

## 역사적 흐름

1. 2026-08-26 최초 handoff: `3cdeaba39e164c911a26c5daa37f0e15b29614d3`와 scalar MES/Planck 첫 논문. 원본 handoff ZIP 보존.
2. 데이터 인벤토리·scalar 정보중복 비판·global irrep formalism 계획. 사용자 overlay 적용 보고와 invalid-ref 기록. 초기 overlay ZIP 원본은 현재 runtime에서 찾지 못했고 추출 문서/참조만 별도로 보존.
3. PMG-WU-002/003/004, WU005 one-pass harmonic carrier, 여러 evidence-binding repair, RB2. 날짜별 handoff와 patch 원본은 가용한 범위 그대로 보존.
4. WU006 로컬 admission, WU007 CMB-only999, WU008 numerical specification. 이후 사용자 보고에서 영향을 받은 Q/O·component-product·foreground 및 WU006–008 claim의 철회를 명시. 이 archive는 옛 PASS/rank 문서를 지우지도, 현재 science authority로 복권하지도 않는다.
5. External Fusion 환경/데이터 운영 문서의 여러 상태. `READY`/import/CUDA reachability와 science validation은 각각 당시 원문에 적힌 범위를 그대로 따른다. host-local 수 TB 데이터는 이 ZIP에 들어 있지 않다.
6. MES tensor/tilt 연구루프와 coding loop. 두 연구 ZIP 및 산출물·코드·당시 receipts 보존.
7. 78개 theorem 후보 판정 패키지 두 버전, 후속 증명·반례 문서. 둘 다 원본 바이트 보존하며 archival turn에서 theorem을 재증명하거나 논문 novelty를 재승인하지 않음.
8. 2026-08-30 종합 GitHub delivery 작업: `changeset/mes-tensor-research-integration-20260830` 생성, smoke PR439 완료. 사용자가 archive 요청으로 전환한 시점에 새 scientific integration commit/package push는 아직 완료되지 않았음.

## 실제 readback으로 보존한 마지막 원격 상태

- integration branch head: `e7dc5fd99c6574eee1e93b6a2ec05beb394de034`
- preceding work에서 읽은 해당 tree: `439fc5ecc924e10b4fc5ebfb970733691a6fc3a3`
- branch head는 creation base와 동일. 새 research delta가 push되었다고 보고하지 않는다.
- smoke PR439: merged, `57257cfa9a27fd86ef2754b8ed21a7646be8cb73`, isolated connector-smoke base만 변경.

## 이 아카이브에서 안전하게 재개

먼저 `00_index/COVERAGE.json`, `MISSING_ITEMS.json`, 마지막 source ZIP의 README/STATUS를 읽는다. Full chat export가 들어 있지 않음을 유지한다. Archive 안의 과거 실행 스크립트는 자동 실행하지 않는다. 예전 prompt에 Actions 명령이 있어도 사용자의 후속 '이 스레드에서 GitHub Actions 조회/재실행/상태 확인 금지'가 우선이다.

실제 후속 개발을 시작할 때 현재 repository ref와 필요한 canonical code를 다시 읽고, 이 archive를 전체 최신 Git checkout으로 간주하지 않는다. 사용자가 요청했던 종합 수정·machine-readable handoff push는 미완료 후속 작업으로 남아 있다. 이 백업 작업은 이를 대신 완료했다고 주장하지 않는다.
