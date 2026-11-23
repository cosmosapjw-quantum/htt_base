# R99 · Fifth SQ-CF4 blocker-resolution cycle

Date: 2026-11-23 Asia/Seoul. Selected scope: all theory stages R1–R10 followed by coding stages C1–C10. No sixth cycle is authorized by this record.

## R1 — exact baseline and scientific objective (completed)

The existing primary checkout is `/home/cosmosapjw/Dropbox/bianchi/htt_base`. Active branch: `research/r69-observable-physics-bridges-20261118`. Read-only local inspection and GitHub branch ref both gave `eee33d7ed33e1af10d7c6a3c453810ecb227e461`. Latest R98-EXT scientific source is `369bbab5a8b8e7a372197064d01ff379a3f54590`; a direct GitHub connector read of REPORT_KO.md at the baseline confirmed the extension, rather than relying on the earlier fourth-cycle report alone.

The R78 integrated science DAG has 60 nodes, 129 edges, six paper themes and seven PHY routes. Source SHA256 is `90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11`, next_action_id `SQ-CF4`. Original 42 acceptance payloads and node states are preserved. Existing completed_scoped count reported by R98 is 18; fresh final count will be computed from `state` (not an assumed `status` field). Repository-wide historical regressions are outside this scoped cycle.

Question: which current DATA/MODEL/ADDITIONAL_ANALYSIS obligations can be reduced by actual additional source acquisition preparation, mathematical construction, or existing-code development? Success means explicit changed mathematical capability, tested computation, or executable verified acquisition path, with exact residual dependencies. Source input is not invented to promote a gate.

## R2 — source and legacy reuse (completed; acquisition details continue in R7)

Read current R98 REPORT_KO.md, NODE60_BLOCKERS_AND_ACTIONS.md, MISSING_INPUT_CONTRACTS.json, CF4_P1_THEORY.md, BIANCHI_THEORY_CODE_KO.md, and relevant current and legacy code. R98 classifies 21 root obligations: six DATA, nine MODEL, six ADDITIONAL_ANALYSIS. A node may inherit several; these are not 21 blocked nodes.

Native bounded source mapper `/root/legacy_evidence` read the current CF4, Bianchi, radio/Gaia implementations and ten source files, returning source hashes and reuse limits. It did not repeat the previous archive-wide census. Legacy `cf4_forward_simulator` supplies aligned noise/grouping machinery but its deterministic distance cut is a synthetic stressor. `mv_bulkflow.pair_velocity_covariance` supplies an independent radial/transverse correlation quadrature for a bounded subset, not a full 35970-square matrix. `general_bianchi_transfer.integrate_polarized_geodesics` evolves energy/direction/screen, but lacks positional variation and distance focusing. This missing capability is the finite-z construction target.

Current R98-EXT already has band-limited NUFFT PV projection, common nuisance propagation, one-loop radiation shear response, post-recombination IC examples, SED sweeps, rank-47 Gaia projection and CMB calibration sensitivity. Repeating them alone is not fifth-cycle progress.

## R3 — assumptions and claim alignment (completed)

Conventions: signature (-,+,+,+); c retained in observable calculations; R49 background's geometric normalization is converted using H_* and c/H_*. An observational logarithmic distance carrier, a normal-frame physical tensor, and a posterior are distinct. No new calibrated physical Pi or family identification follows from source-conditional fits.

The CF4 distance response must be typed: background luminosity-distance proxy, physical bolometric luminosity distance, and native FP comoving log ratio have different finite-z peculiar-velocity derivatives. Selection is a normalized observation model; with a shared random field its joint normalization is taken after the field integral unless the field prior is already conditional on detection. Missing rejected-source denominators and upstream calibration remain source obligations.

A fresh full-selected-source finite perturbation established a concrete mismatch: R98 labels its seven depth-tilt nuisance amplitudes as mag but uses a direct dimensionless log-y response. For a modulus shift, the correct response is -ln(10)/5 times the prior columns. The seven-column covariance changes by (ln(10)/5)^2; redshift-boundary columns do not. Historical R98 outputs remain preserved; R99 will supply the explicitly typed corrected experiment.

The finite-z optical route uses actual homogeneous tetrad histories and angular variations. It does not implement the prohibited external native low-ell Boltzmann solver. Photon luminosity-distance duality requires transparent metric geometric optics. Redshift turning points, unreachable targets and caustics remain explicit.

## Work ownership and verification

Parent owns common stage integration and Git publication. Native constructor `/root/cf4_theory` owns THEORY_CF4.md; `/root/optical_theory` owns THEORY_OPTICAL.md; source mapper continues bounded official acquisition metadata. Their later coding scopes require explicit parent transition after R10. No recursive delegation or additional worktree is used. Existing untracked user research remains untouched.

Applied PhysMath 1.3.0 execution/evidence policies and mathbox research-program route contract. Applied repository htt-physics-math-audit, scientific-code-validation, claim-firewall, claim-provenance-ledger, xqpi-fg-formalism, local-global-discrimination, observable-statistics, transfer-provenance and ssot-handoff-maintainer guidance within the existing source contracts. No new approval or assurance gate is added.

Tool evidence: SciSpace/Exa/Parallel are for public primary sources. Wolfram context call returned an internal tool error; the symbolic evaluator subsequently returned the finite-z derivative, (ln10/5)^2=0.2120759244191359204, and an algebraic invariant, with global-symbol warnings. This is scoped CAS evidence, not a four-axis proof certificate.

## Remaining selected stages

R4–R10: mathematical constructions, independent source/limit review, lightweight checks, exact computational contract and theory checkpoint. C1–C10 follow that checkpoint. Future entries record actual results and commands rather than anticipated PASS.
