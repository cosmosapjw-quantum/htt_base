# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
`research_gates/pr04/tests/` and, where the analytic core is closed-form, (ii) a
Wolfram symbolic proof in `docs/generated/pr04_paper_theorem_proofs.json`
(`scripts/prove_pr04_paper_theorems.py`). Run `make paper-a-gates` /
`make paper-b-gates` (thread-pinned). "symbolic" = closed-form QED; "numeric" =
property gate only; "corollary" = analytic consequence of a proved gate, with the
full manuscript proof pending independent review (`BLOCKED_PROOF_REVIEW`).

## PAPER-A — response identifiability and congruence kinematics

| Theorem | Statement (under registered operators) | Gate test | Symbolic | Status |
| --- | --- | --- | --- | --- |
| A-rank (response identifiability) | whitened stacked response blocks have rank = identifiable dimension; a duplicate block adds zero rank, nullspace = (x,−x) line | `test_pr04_response::test_full_and_duplicate_rank` | `A-rank` | symbolic ✓ |
| A-nuisance | projecting out a nuisance equal to a response block removes exactly that block's rank | `test_pr04_response::test_nuisance_removes_exact_block` | (numeric) | numeric ✓ |
| A-angles | identical response subspaces have zero principal angles | `test_pr04_response::test_principal_angle_identical` | (numeric) | numeric ✓ |
| A-ladder (complementary-channel sufficiency) | adding complementary blocks gains rank monotonically until the design is identifiable | `test_pr04_response::test_rank_ladder` | (numeric) | numeric ✓ |
| A-flrw (congruence limit) | flat-FLRW comoving congruence has θ = 3H and zero shear/acceleration | `test_pr04_congruence::test_flat_flrw_limit` | `A-flrw` | symbolic ✓ |
| A-minkowski | inertial Minkowski congruence has θ = σ = ω = a = 0 | `test_pr04_congruence::test_minkowski_inertial` | (limit of A-flrw) | numeric ✓ |
| A-wigner (rapidity non-additivity) | two non-collinear boosts compose to an exact Lorentz map whose velocity ≠ Euclidean sum | `test_pr04_congruence::test_noncollinear_boost_is_lorentz` | `A-wigner` | symbolic ✓ |
| A-failclosed | a single rapidity/velocity does not determine θ/σ/ω; incomplete normalization fails closed | `test_pr04_congruence::test_incomplete_normalization_fails` | (numeric) | numeric ✓ |
| A-radial-novortex (radial-vorticity no-go) | a purely radial response design places vorticity in the data nullspace | (rank machinery: `audit_response_blocks`) | — | corollary (proof review) |
| A-single-shell-degeneracy | a single-shell response is rank-deficient for the joint bulk/shear/curl design | (rank machinery: `rank_gain_ladder`) | — | corollary (proof review) |
| A-temporal-tensor-rank | the dynamic tensor design recovers rank only with independent temporal kernels | (rank machinery) | — | corollary (proof review; ties to LR-06G) |

The last three are honest analytic corollaries of the proved rank audit; their
standalone manuscript proofs are the `BLOCKED_PROOF_REVIEW` items for PAPER-A.

## PAPER-B — restricted Bianchi-I multifluid dynamics

Restricted branch (stated before every theorem): expanding geodesic normal
congruence, Fermi-propagated orthonormal triad, flat Bianchi-I, homogeneous
non-interacting perfect-fluid species (p̂ = w ρ̂, −1 < w ≤ 1), signature
(−,+,+,+), c = 1.

| Theorem | Statement | Gate test | Symbolic | Status |
| --- | --- | --- | --- | --- |
| B-codazzi (flux balance) | an antipodal species pair has zero tilt flux J (Codazzi residual 0), Ω_tilt > 0, realizability margin ≥ 0 | `test_pr04_bianchi::test_counterstream_codazzi` | (numeric; flux algebra) | numeric ✓ |
| B-nonsuff (scalar nonclosure) | a colinear antipodal pair and an isotropic six-stream share Ω_tilt = Tr(K) but differ in the STF moment Π | `test_pr04_bianchi::test_scalar_non_sufficiency` | `B-nonsuff` | symbolic ✓ |
| B-psd (PSD moment cone) | every PSD second moment K realizes as a sum of antipodal eigen-pairs e eᵀ, each with zero first moment | `test_pr04_bianchi::test_psd_pair_decomposition` | `B-psd` | symbolic ✓ |
| B-dust (exact FLRW oracle + Gauss transport) | a(t) = (1 + 3H₀t/2)^(2/3) gives H = H₀/(1+3H₀t/2), Ḣ = −(3/2)H² and an exactly preserved Gauss constraint; the RK4 integrator reproduces it to ~2e-9 | `test_pr04_bianchi::test_dust_flrw_limit` | `B-dust` | symbolic + numeric ✓ |
| B-shear (shear memory) | shear obeys σ̇ = STF(−3Hσ + κΠ); d(σ̇)/dΠ = κ ≠ 0, so ablating the anisotropic stress changes the shear history | `test_pr04_bianchi::test_pi_ablation_changes_shear` | `B-shear` | symbolic + numeric ✓ |
| B-conservation (species continuity/Euler) | each species obeys the tilted continuity + Euler RHS; total flux is the Codazzi source | (`dynamics.rhs`, `constraint_residuals`) | — | numeric ✓ |
| B-pushforward (fail-closed reporting) | the legacy x_C/Q/Π/F/G_F pushforward blocks on missing components and on a zero denominator | `test_pr04_pushforward::*` | — | numeric ✓ |

## Exit-criteria coverage (`PAPER_EXIT_CRITERIA.md`)

- PAPER-A: response-subspace identifiability ✓, complementary-channel sufficiency
  ✓, congruence/Wigner kinematics ✓ (symbolic); radial-vorticity no-go,
  single-shell degeneracy, temporal tensor rank remain `BLOCKED_PROOF_REVIEW`
  (analytic corollaries pending independent proof review).
- PAPER-B: flux balance ✓, PSD tilt moments ✓, exact conservation + constraint
  transport ✓ (exact FLRW oracle), shear-memory ✓, scalar nonclosure ✓ — all with
  symbolic or symbolic+numeric backing. Independent dynamics review remains the
  `BLOCKED_DYNAMICS_REVIEW` gate before submission preparation.
