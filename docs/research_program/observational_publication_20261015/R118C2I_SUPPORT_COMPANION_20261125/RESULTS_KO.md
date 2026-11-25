# R118-C2I 연구 결과

PASS_SCOPED. C2H 이후 BASS characteristic support 압축, 과거 REI fixed-q
covariant solver 복원, REC 전체 2s paired-source 동적 companion closure를 수행했다.

- REC: 311 original points (8 interior, 303 exterior), 319 positive
  contributions. 30 cases/147 steps. Source-only normalized number/energy
  defects 2.84e-18/3.02e-18; COM combined 7.64e-8. DOP853 reference에서
  first-order convergence. Auxiliary phase volumes, fixed T/HII/2p,
  native exterior diffusion 미결. FULL owner replacement HOLD.
- REI: 0e25846433170d0f420c4cda44a0bedbf02cd177의 fixed-q transport,
  parallel/cache/local proper-time machinery와 adaptive driver 복원.
  기존 C2H driver 유지. Short 5 cases/17887 steps 완주. Long q16은
  73149 accepted steps, z=19.526371616320315에서 AXBI_RUNTIME_CAP,
  120s checkpoint. 물리 실패 아님; full-range convergence 미검증.
- BASS: same-ray/current-threshold positive endpoint compression.
  Final pins에서 18 cases/121088 steps, 9 long FLRW z20→4 완주.
  Short uncompressed reference 대비 tau 상대차 최대 6.45e-13.
  Initial FLRW angular artifact |Ppar-Pperp|/rho 5.41e-7 보존.
  Exact redshift fast path 단독은 실패; exactly isotropic geometry,
  empty UV initial, isotropic emission에서 angular symmetry reduction
  적용 후 5.30e-17 이하. Finest 32768 steps, sub16, width .01:
  tau .03218188770533301, Tm 7652.080922055792 K, HeIII .019463152048473,
  309 peak internal UV packets. Final output angular-expanded.
  PR173 historical 58/58 rows metadata 제외 정확히 재현,
  5/5 invalid fixtures 거부, original oracle 5.00e-15.
  PR171 stress SI diagnostic 복원; active Einstein coupling 없음.
- Tests: REC 146 Rust +12 targeted Python; REI 319 Rust +18 examples;
  BASS 279 Rust +3 examples. Raw verification 및 remote SHA 확인.
  Native subagent dispatch unavailable; local independent numerical
  comparisons and historical oracle checks only.

R78 unchanged. No scientific promotion. Next R118-C2J:
fixed-q adaptive long-run error/cost profiling (checkpoint preserved),
threshold-aware nonlinear rate error control, REC disjoint exterior
transport/crossing and companion coupling; evaluate active stress coupling
only after source ownership and full energy-momentum inventory are closed.
