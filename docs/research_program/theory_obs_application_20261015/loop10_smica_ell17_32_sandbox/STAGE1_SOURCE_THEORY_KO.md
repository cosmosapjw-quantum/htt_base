# Loop 10 / S1: ell 17..32 finite-shell bound (2026-10-16 KST)

## Exact source and scope
- Predecessor: [PR #536](https://github.com/cosmosapjw-quantum/htt_base/pull/536), `37db458319fd10e353a722345cb9a4ea6a39c698`.
- Original Dropbox-synced byte source: `docs/research_program/theory_obs_application_20261015/loop9_smica_finite_response/results/response_v1/baseline_response_matrices.npz`, SHA-256 `a9aaeb393deba03c97ecf45bf4e1ab74e98e3a8747de7c4bc7a96bff27014007`.
- Independent sandbox SVD: `||K_0..5,6..16||=2.535379690985017`, `||K_2..3,6..16||=1.7559728099975862`, `||K_2..5,6..16||=2.2557202911770022`; 12/32 retained rows exactly match original matrix rows [4:16]/[4:36].

## Constructive theorem for *any* same-pixel support
For the unweighted full-rank real-orthonormal low design `Y_L` (ell0..5, 36 columns) on N=26846 selected NSIDE64 RING pixels, set `K=Y_L^+ Y_H` for the M=800 ell17..32 high columns. Spherical addition theorem yields `||Y_H||_F^2=N*800/(4*pi)`. Since the constant harmonic is a low column, `sigma_max(Y_L)>=sqrt(N/(4*pi))`. Thus `||K||_2 <= kappa(Y_L)*sqrt(800)`. The source-recorded condition estimate `kappa=3.6013785311890616` implies the **conservative source-conditional finite-shell bound** `||K_17..32||_2 <= approximately 101.86236724093735`. That is NOT the actual new mask-specific norm. If a verified condition cap `kappa<=3.602` is supplied, its resulting cap is `101.87994503335777`.

For ell2..5 retained rows, concatenate archived K6..16 and unknown new K17..32: by PSD Gram addition, `2.255720291177002 <= ||[K6..16,K17..32]||_2 <= approximately 101.88734040085458`. This is conservative and need not be useful for astrophysical inference.

No actual ell17..32 selected-mask operator is computed in this sandbox, because the original 2048 masks and reduced K1 cache are not available here. No actual high-mode coefficient amplitude or ell>=33 remainder is inferred. Retain physical EGS, beam/foreground/E2E, covariant derivatives and Bianchi shear/tilt as HOLD.

## Execution / evidence
Actual isolated sandbox Python reloaded the SHA-locked predecessor NPZ, independently computed SVDs, validated retained rows and wrote a JSON numeric certificate. Wolfram confirmed 800 coefficient count and the exact horizontal-concatenation Gram identity. This S1 backup is available as `STAGE1_BASELINE_THEORY_BACKUP_20261016.zip` in the chat sandbox, SHA-256 `b2a3829dc79d66241d0d9fbde4f0df38ea4a024809ab1c0ffb3df848656b74d3`. A ChatGPT Library upload was attempted but returned `container_session_expired`; do not claim Library backup. GitHub branch publication is a separate verified preservation channel. No native independent subagent or local PC execution.

S2 next: construct and sandbox-test a memory-bounded per-shell spherical-harmonic QR operator and replay archived K6..16 on the owner's existing source mask when available. S3: actual full SMICA ell17..32 remains LOCAL_INPUT_REQUIRED. No physical claim promotion.
