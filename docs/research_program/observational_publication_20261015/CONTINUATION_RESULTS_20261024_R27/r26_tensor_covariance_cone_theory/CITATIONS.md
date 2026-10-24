# Primary sources and overlap record

Access date: 2026-10-24. These references supply standard mathematical background, not an empirical CF4 covariance or a physical-response qualification. The proofs in `DERIVATION.md` are explicit algebraic derivations; no result is presented as new mathematical foundations.

## Verified primary literature

1. Stephen Boyd and Lieven Vandenberghe, *Convex Optimization*, Cambridge University Press, 2004. [Author-hosted book](https://www.stanford.edu/~boyd/cvxbook/bv_cvxbook.pdf). Relevant locations verified in the hosted PDF: §2.2.5, printed pp. 34–35 (PDF indices 47–48), PSD cone; Appendix A.5.4, printed pp. 648–649 (PDF indices 661–662), SVD and Moore-Penrose inverse/projectors; Appendix A.5.5, printed pp. 650–651 (PDF indices 663–664), PSD block matrices and singular Schur-complement range conditions. These are the background for congruence, the canonical PSD lift, and full-block feasibility. The book's §4.6 is the general conic-optimization background; the proposed implementation is not claimed to have been run.
2. Lieven Vandenberghe and Stephen Boyd, “Semidefinite Programming,” *SIAM Review* 38(1), 49–95, March 1996. [Author-hosted publication record](https://stanford.edu/~boyd/papers/sdp.html). The page verifies authors, journal/year/pages and describes linear optimization under affine PSD constraints. It supports the identification of a covariance support problem with linear/PSD restrictions as an SDP. The paper's page, rather than an inconsistent year in another bibliography, is the cited bibliographic authority.

Only these primary sources were used externally. No secondary search summary, copied proof, physical Gamma value, assumed correlation, or calibrated probability was imported.

## Cache-first intake and limitation

Read-only searches for filenames matching `boyd|cvxbook|vandenberghe` under `/mnt/extdrive/workdir/htt_open_data` and corresponding source mentions in the relevant publication/research folders found no cached source. The parent independently reported the same outcome in the public-literature cache. The web reader then opened both exact primary URLs successfully, including the book's mathematical pages and the paper's publication record.

Optional local caching attempted this first command:

```sh
curl --fail --location --max-time 60 --silent --show-error https://www.stanford.edu/~boyd/cvxbook/bv_cvxbook.pdf --output /mnt/extdrive/workdir/htt_open_data/r26_tensor_covariance_cone_theory/sources/bv_cvxbook.pdf
```

Observed raw stderr: `curl: (22) The requested URL returned error: 403`; exit code 22. A second HTML download chained with `&&` therefore did not start. No local PDF checksum or successful cached byte download is asserted. The verified author URL, bibliographic identity, page locations, access date, and web-reader content suffice for this exploratory theoretical note. Exact replay of the upstream PDF is unavailable here; this limitation does not manufacture a scientific failure or an additional admission gate.

## Controlling local source

`/mnt/extdrive/workdir/htt_open_data/r26_cf4_actual_source_model_review/CONTRACT.md` was read and its SHA-256 verified as `cdf94aaf6d39a01baae0d2fc03342032b1eb5f82ef34555e83ca8631d43f7992`. No implementation, held-out result, actual M7, witness arrays, or empirical covariance from that prospective task was consumed. The contract remains proposed execution, not proof that response acceptance was met.

Read-only repository identity when preparing this note: `/home/cosmosapjw/Dropbox/bianchi/htt_base`, branch `research/htt-adaptive-methods-20261023`, HEAD `d93605e66adfececa89b90681124b232a5f90220`, origin `https://github.com/cosmosapjw-quantum/htt_base.git`. The checkout contains existing tracked and untracked edits. No repository file, controller state, Git object/ref, or scientific numerical artifact was written by this task. The reports below were read as working files, not assumed to be identical to HEAD.

## Report comparison and reused material

All relative paths below begin at `docs/research_program/observational_publication_20261015/` in that checkout.

| Exact working file | Material already present and reused | SHA-256 at read |
|---|---|---|
| `REPORT_20261024_REV1/sections/01_framework.tex` | Tensor-valued departure carrier, named measures, anchors, joint coverage images; sections beginning at lines 17, 30, 75 | `1712e2b1d9c1ad09906669c07ad9cc737a7aa0a3cafe41b138f18270a1b345af` |
| `REPORT_20261024_REV1/sections/07_mathematical_details.tex` | Joint support/floor and ratio-domain statements at lines 24, 63; covariance domination and sharp arbitrary-dependence scalar bound at line 112; rank-loss pseudoinverse caution at line 134 | `9035b5f6bbac599c50c861110be730fb6678a2b112337e5935a3f686b23a1cd0` |
| `P1_SELECTED_TENSOR_LAW_20261024/sections/02_identification.tex` | Observation-law fibres, full STF basis, physical functional/denominator domains, qualified Pi; sections beginning at lines 4, 30, 52 | `865712c29b5de95704b06622dd116e1b0548fc6abaf543abfaa033fa70f963bd` |
| `P1_SELECTED_TENSOR_LAW_20261024/sections/05_coupled_functionals.tex` | Restricted-domain optical-bias fibre, separate apparent rate carrier, full cross-window law, retained finite measure, unknown mass; sections beginning at lines 4, 49, 75, 124 | `515d934b7ae5b3ab284ea84900a8f5ed1743db2490d0fdea574218ba581e70d0` |
| `P1_SELECTED_TENSOR_LAW_20261024/sections/07_proofs.tex` | Fibre and domain proofs, coverage versus measure, Gaussian pivots, common-law event completion; sections at lines 1, 10, 29 | `e0ec9987c8ec59fae6239bee795f3c86cb96be6a86c949afbade62c5f22c0bef` |

No response-specific exact PSD-cone image proof, minimum-latent-trace image characterization, or anchor-aware seven-versus-six gauge derivation was observed in these five files. This is a bounded overlap check, not a repository-wide or literature novelty search. General pushforward and worst-dependence statements already present are not the new capability. The proposed consuming decision is whether a future qualified response and covariance class permit finite conditional uncertainty, with explicit identification of the unbounded case.

## Skill and evidence boundary

Applied the repository-local `htt-physics-math-audit`, `htt-xqpi-fg-formalism`, `htt-claim-firewall`, and `htt-claim-provenance-ledger` instructions. Evidence is the stated source contract, five report sections, author-hosted primary references, and self-contained proofs. There was no numerical scientific run, CAS execution, physical admission, independent review of this note, publication, or controller dispatch. Preparation/review wall time was not instrumented; no scientific-run debit is invented. The memory registry was consulted only for the preservation/claim-ceiling convention; current scientific statuses were not inferred from an old memory snapshot.
