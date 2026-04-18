# BASS Environment Variables

본 문서는 `bass_rs` 가 인식하는 환경 변수를 정리한다.

---

## `BASS_SERIAL_KLOOP`

- **값**: `1` (활성화), 그 외 / unset (비활성화)
- **효과**: `solve_production_spectrum` 의 모든 rayon 병렬화를
  (k-loop par_chunks **그리고** compute_dl_spectrum 의 ell-loop par_iter)
  비활성화하고 직렬 실행으로 fallback
- **사용 시점**:
  - 디버깅: rayon 관련 의심 issue 격리
  - Profiling: 단일 thread 시간 측정
  - Sandbox 환경에서 rayon 이 효과 없거나 오히려 느릴 때
- **production 에서는 unset 권장** (사용자 local 환경에서는 병렬화가
  의미 있는 win — sandbox 의 memory bandwidth bound 와 다름)

```bash
# 직렬 강제
BASS_SERIAL_KLOOP=1 cargo test --release --test test_dl_200k -- --nocapture

# 기본 (병렬, RAYON_NUM_THREADS 환경변수와 함께 사용 가능)
RAYON_NUM_THREADS=8 cargo test --release --test test_dl_200k -- --nocapture
```

## `RAYON_NUM_THREADS` (rayon 표준)

- **값**: 양의 정수, unset 시 시스템 nproc
- **효과**: rayon worker pool 의 thread 수
- **권장**: production 에서는 unset (rayon default = nproc)

## `MIMALLOC_*` (mimalloc 표준)

`mimalloc` allocator 의 표준 환경변수가 그대로 적용됨. 보통 default 충분.

- `MIMALLOC_VERBOSE=1` : allocator 통계 출력 (디버깅)
- `MIMALLOC_SHOW_STATS=1` : 종료 시 통계 출력

---

*문서 끝.*
