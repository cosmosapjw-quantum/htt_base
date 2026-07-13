# NSC self-adversarial audit — Stage 1: SELF-DISCOVER (scope + module selection)

_2026-07-13. Internal dev-tier audit ledger; NEVER rendered into any report (no-meta-dev rule).
Owner ask: three-axis (novelty / significance / correctness) self-adversarial audit of all
research results to date, JCAP/PRD referee style, multi-agent debate, workflow orchestration,
with explicit execution evidence per loop stage:
self-discover -> step-back -> metacognitive self-ask -> CoVe -> adversarial self-ask ->
web CRAG -> CCoT -> PDR._

## Evidence read (this stage)

- `docs/generated/egs_results_table_v9.md` — 78 rows, full claim inventory (read in-session,
  2026-07-13; status census: measured=9, measured_diagnostic=3, measured_partial=2,
  measured_synth=5, measured_no_go=1, proven*=46, diagnostic*=4, blocked=2,
  retracted_superseded=2, re_frozen=1, reclassified=1, registered_external=1,
  web_traced_refuted_readopted=1).
- `docs/research_program/OPEN_ITEMS_LEDGER.md` — 10 open items (1 now, 1 decision_only, 8 blocked).
- `CLAUDE.md §1/§3` — honest claim envelope + rev-r190..r198 cycle summaries.
- `docs/PR_DELTAS/rev-r198.md` — latest delta (read in-session).
- Skill `htt-adversarial-review-loop` invoked (five-angle review contract).

## Task decomposition (self-discovered module selection)

The 78 rows cluster into 10 auditable claim clusters (correctness axis, one CoVe lane each):

| Lane | Cluster | Headline under audit |
|---|---|---|
| C1 | K5-MV | CF4 MV bulk flow \|B\|(200)=405 km/s, LCDM tension range 4.4–5.4σ |
| C2 | K5-MOCKSIG | in-house GRF forward-mock calibration, parametric ~5.8σ, mock/analytic ρ≈0.93 |
| C3 | K5-VCORR-ML | field-level ML fσ8 = 0.40 ± 0.02 (Vpec, shape-corrected; jk ±0.10) |
| C4 | EXT-DESI(+MOCK) | window-corrected dipole D=9.49e-3; clustering-dominated, ΛCDM-consistent p=0.90 |
| C5 | EXT-ACT | ℓ=2..10 κ isotropy p=0.35 + 95% UL 3.28e-6 |
| C6 | K6-CURL | WF mean-field curl/div=0.009 potential flow; CR distribution PARTIAL |
| C7 | MES program | geodesic re-freeze W2_max=3.3789e-13; MESb web-trace refutation; ε1_crit |
| C8 | Framework core | parent identity c=(1,-1,1,1); graded comparator rank-2; PSD cone; T1'/T2G intervals |
| C9 | K5-LCDMCV + K5-RECON | GLS 340.7±5.0 (significance withheld) + 7-method reconstruction spread |
| C10 | K1 + JWST | BipoSH p=0.68/0.65; global max-scan p=0.097/0.121; JWST labelled forecast |

Novelty axis: 6 web-CRAG lanes (N1 bulk-flow lineage; N2 field-level PV fσ8; N3 number-count
dipoles; N4 CMB-lensing isotropy nulls; N5 velocity-field vorticity + reconstruction comparison;
N6 Bianchi/tilt framework). Significance axis: 3-referee panel (JCAP referee, PRD referee,
skeptical field expert) after correctness+novelty land (genuine barrier: panel needs ALL
lane outputs). Then 3-axis multi-agent debate (attacker ∥ defender -> judge per axis) + one
completeness critic. PDR (final adjudication/decision review) synthesized inline from all
artifacts into `08_final_referee_report.md`.

## Ground rules bound into every lane

- Judge each claim against its CLAIMED tier (diagnostic-only / measured / proven-seal) —
  overclaim and underclaim both reportable; consistency/upper-limit claims are not "detections".
- Read-only: no repo edits by lanes; small (<60 s) recomputation snippets allowed; heavy reruns forbidden.
- Refute-prompted: every correctness lane must pursue its single strongest kill-attack.
- Fail-honest: "cannot verify from artifacts" is itself a finding, never smoothed over.
