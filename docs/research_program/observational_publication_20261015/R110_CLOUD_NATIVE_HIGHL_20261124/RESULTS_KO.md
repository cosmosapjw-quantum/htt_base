# R110-CLOUD · BASS/REC/REI Rust 개발: 비섭동 배경의 임의 ℓ C_ℓm^XY

기준: htt_base `423165ab2`, BASS R109 `3966f2a08`, REC `f3797f42c`, REI `25fbae98b`. 커밋 고정값은 [NATIVE_PINS.json](NATIVE_PINS.json), 로컬 인계는 [LOCAL_AGENT_HANDOFF.md](LOCAL_AGENT_HANDOFF.md).

- **BASS** (`research/r110_cloud_highl_sky`): 이론 루프 10단계(THEORY.md)와 코딩 루프 C1–C10(README_KO.md). 순방향 해의 충돌 원천을 기록하고 역방향 특성선에서 같은 이산 사상을 replay해 관측 ℓ 해상도를 Lagrangian 격자와 분리했다. 순방향 광선 재현 차 0(bitwise), 부스트 FLRW ℓ≤40 해석해 <10⁻¹³, Bianchi I 닫힌형 2차 수렴, 회전 공변성 6×10⁻¹⁵. SDIRK2로 Thomson cell 시간 정확도 2차(연속 변화비 ≈4.0), Lie 합동 갱신으로 12계열 유형·h 보존(≤2×10⁻¹⁵), Ω_Λ 추가. 12계열 ℓ≤32 아틀라스와 z=1100→0 장기 4계열 ℓ≤48 시연.
- **REC** (`research/r110_anisotropic_source`): 이방 하늘의 HYREC-2 TLA 원천. 두꺼운 Sobolev 탈출률에서 전단이 모든 차수로 상쇄됨(보조정리), 방향 Wien 평균의 Jensen 증폭(사중극 0.1에서 2차식 대비 +10%, Lyα에서 +50%).
- **REI** (`research/r110_bass_ionization`): REC(z>20)+AX08(4–20)+연속(z<4)을 BASS 이온화 표로 결합. ZERO에서 τ_reio=0.054.
- **htt_base**: `scripts/r109/commander_native.py --modes-name los_modes.tsv`로 R110 템플릿을 Commander 선형 연산자에 투영할 수 있다(기본값은 R109와 동일).

해석 범위: 단일 이력의 결정론적 모드 곱이며 공분산·계열 귀속·관측 적합은 없다. 시연 매개변수는 관측 제약이 아니다.
