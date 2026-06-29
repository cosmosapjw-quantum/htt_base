# Voluntary Additional Audit — Beyond the Review Prompt

Items I checked on my own initiative, outside the prompt's eight required sections. None changes the verdict (MINOR REVISIONS); they are listed so nothing is left unexamined. Severity: ◆ worth fixing before submission · ○ minor/cosmetic · ✓ positive finding to preserve.

## A. Internal consistency of the results ledger ✓

`egs_results_table.md` declares `{proven_symbolic:6, proven_gate:8, measured_partial:1, measured:1, measured_no_go:1}` = **17 rows**, matching the 17 data rows in the table (14 proven + 3 data). The status taxonomy is used consistently and the blocked rows carry their registered codes. No phantom or double-counted theorems. The `data_rank` in `pr08_006_joint_artifact.json` is reported separately from `prior_conditioned_rank` (both 2 here, with an explicit note that no prior adds a sector) — a clean separation that many anisotropy papers blur.

## B. The "data rank 2" count mixes a full and a partial sector ◆

`pr08_006_joint_artifact.json:data_rank` gives `data_rank_count:2` with `reachable_full:[Ω_tilt]` and `reachable_partial:[Σ²]`. So the rank-2 headline is **1 fully measured + 1 partial** (Σ² is K1-partial: look-elsewhere only, E2E null open). This is disclosed, but the headline number "rank 2" reads stronger than "one full + one partial." Recommend stating the rank as "1 full (Ω_tilt) + 1 partial (Σ²)" wherever the rank-2 headline appears, so the maturity of the two reachable sectors is not flattened. (This compounds the §5 `Ω_k` point: of four sectors, exactly one is fully measured today.)

## C. e-value null inherits the GRF-ΛCDM idealisation ◆

EGS3-A3's certificate `E=1[x>t]/α` is a valid e-value (independently confirmed: unit null mean, Markov bound holds — `reviewer_verification.py` check 2). But `α` is fixed by the **same isotropic GRF-ΛCDM null** as K1, which omits instrument/foreground/systematics. So the e-value's "stated error rate" is an error rate *under an idealised null*. This should be said next to the certificate claim: the e-value is calibrated to the GRF-ΛCDM null, and the E2E null (Blocker §1) would re-calibrate it. Otherwise "Π is a certificate with a stated error rate" can be over-read as systematics-robust.

## D. K1 component-separation dependence is a quiet systematic ◆

SMICA global p = 0.097, Commander = 0.121 (`k1_global_maxscan.json`). A ~25% method dependence in the corrected p is exactly the kind of foreground/component-separation sensitivity the unbound E2E null is meant to capture — and it is *larger* than it looks because the individual statistics driving the result (parity 0.025, `S_{1/2}` 0.045, planarity 0.042) are themselves cleaning-sensitive at low ℓ. Report both pipelines side by side (the program already does in the JSON) and resist any temptation to quote the more extreme SMICA value alone.

## E. Self-flagged contract failures — I concur with the diagnosis ✓/○

`BLOCKERS.md` (hygiene-pass section) correctly identifies that 6 of 7 residual contract failures are **structural**: the generated artifacts embed `git_commit_or_worktree_state:<HEAD>+dirty`, so any commit re-stales them — they can only pass in the exact uncommitted generation state. The proposed fix (drop `git_commit_or_worktree_state` from emitted artifacts; keep content-addressed `config_hash`/`input_hashes`) is the right one and matches the content-addressed manifests already used for the EGS figures. This is a provenance-hygiene refactor, not a research-content issue — out of review scope, but the diagnosis is sound. ○ The 7th (`manuscript_audit_repair_matrix`) reflects the PDF carrying **2 genuine `pdf_claim_lint` findings** under the current linter while the committed report is blessed at 0 — this *is* a research-surface item: re-run the linter and fix the 2 flagged sentences (or bind a hash-exemption with the reason), don't let a blessed-at-0 snapshot mask 2 live findings.

## F. K5 figure title vs caption mismatch ○ (self-flagged)

The K5 figure's internal PNG title still reads "minimum-variance" while the authoritative LaTeX caption says "weighted-GLS" (`BLOCKERS.md` §3 note). Minor, but a reader comparing figure and caption sees two estimator names for one result. Fold the title regeneration into the K5 discharge as planned.

## G. K6 injection tests a single curl mode ○

The K6 no-go is validated by recovering an injected **solid-body** rotation to machine precision (`k6_cf4_curl_posterior.json`). That demonstrates estimator curl-sensitivity for *that* mode; it does not, by itself, prove sensitivity to a general (sheared/differential) vorticity field. The structural-no-go conclusion is still correct (the WF prior suppresses curl regardless of mode), but state the injection's scope: "estimator recovers an injected solid-body curl; the suppression is the WF prior's, across modes."

## H. Provenance discipline ✓

Every discharge JSON and figure manifest carries `config_hash`/`input_hashes`, real input provenance (CF4 VizieR ID, Planck map filenames, `n_groups_used:38049`, `n_mock:600`, seeds), and `claim_tier:diagnostic_only` with `family_identification:false`/`native_solver_result:false`. The reproducibility surface is strong and should be preserved as-is. The cobaya check (ruling it out as `C_ℓ`-level, not maps) is documented honestly in `BLOCKERS.md` — a good example of recording a *negative* result so it is not re-attempted.

## Independent re-checks (runnable)

`reviewer_verification.py` (stdlib, no project code) confirms, independently: the bracket constant `12/7>1` and proper interval (EGS3-B4); the e-value unit null mean + Markov bound (EGS3-A3); the Fisher-floor monotone descent below 0.632 (NT2-A1); the radial-vorticity identity `n·Ω·n≡0` (EGS3-B3); and a **demonstration of the §5 point** — two response maps with identical rank 2, one where `Ω_k` is a genuine null and one where it is degenerate with `Σ²`, proving the rank count alone cannot characterise the `Ω_k` blindness. 5/5 checks confirmed.
