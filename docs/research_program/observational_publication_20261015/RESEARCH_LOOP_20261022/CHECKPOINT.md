# Research loop checkpoint — 2026-10-22

Scope: revive source-qualified legacy ideas and resolve theory/open-data blockers
of the original six-paper DAG. Owner: HTT research intake. C0, exploratory until
scoped independent review; original scientific admission remains HOLD.

Baseline: existing checkout, branch `research/htt-open-input-theory-20261018`,
local/remote/PR561 HEAD `d66328b8d96ba9cc7bd8c1cbfd929be40903312c`; clean intake.
PR561 is OPEN/DRAFT with base `research/htt-sixpaper-goals-robustness-20261018`.
The live packet reports 17/42 completed, eight direct external blockers, 17
dependent nodes. All original acceptances and historical R9/UNKNOWN are retained.

The owner requested a continuing loop; this unit applies R1–R10 and applicable
C1–C10 of the now-installed `physmath-research-loop` **1.3.0**. Prior records
reporting its absence describe their earlier environment. Stage labels are not
science completion. No native evolution solver or ODE is permitted here.

Dispatch: fresh bounded `legacy_theory_20261022` requested `gpt-6-astra/xhigh`
(read-only R2–R5); `open_sources_20261022` requested `gpt-6-sol/high` (writes
only `data/`); `normalized_bounds_20261022` requested `gpt-6-sol/high` (writes
only `selection/`). Separate `review_loop_20261022` requested `gpt-6-astra/xhigh`
is read-only and authored none of those results. Observed child runtimes UNKNOWN.
Parent request Sol/high; actual runtime UNKNOWN.
No nested children; at most four active including parent; parent alone publishes.

Before source acquisition, `/dev/sda2` is mounted at `/mnt/extdrive` (fuseblk),
2.3T available. Data stay under `/mnt/extdrive/workdir/htt_open_data`; no download
budget option is used. Existing downloader retains its 2GiB reserve and streaming
space checks. Completed Gaia/radio/PR3/SDSS/LP/history/optical campaigns are reused.

## Completed research and source transitions

- Inventoried all 558 PR records returned by the live API, including open and
  closed historical PRs. [PR_INDEX.json](PR_INDEX.json) preserves metadata;
  [LEGACY_MAP_KO.md](LEGACY_MAP_KO.md) distinguishes selected inspected source/body
  paths from uninspected diffs. Source JSONL remains outside Git, SHA-256
  `ad0585ce7bc094e331d599170c24021239e619d720b9daccdf05dcbbe346d090`.
- Combined the old catalogue-normalization and joint-event-bound ideas into a
  finite normalized joint-importance-weight calculation. [THEORY.md](THEORY.md)
  proves the linear-fractional/LP correspondence and states the physical missing
  assumptions. Existing 2,048 joint-draw summaries were reused; no new draws or
  old 97-LP campaign were run. The Gamma sweep is a working-law sensitivity,
  with unmeasured Gamma and unresolved physical Q/Pi. Its physical outer interval
  remains [0,1]. Exact rational witnesses and two-redshift algebra were checked
  by a stateless Wolfram call; no historical four-axis CAS status is changed.
- Qualified pinned Pantheon author likelihood/fields and the CF4 compilation
  recipe. The existing 651-row sample contains 645 zHD/zCMB differences and 556
  rows passing the release SN-only redshift cut. The derivative of the physical
  magnitude/PV correction remains missing. No new covariance or PV term was added.
- Downloaded eight public payloads, **1,241,866,173 bytes**, into the external
  cache. The new PR4 observed A/B maps, mask and exact paired 030Ax030B beam/window
  members pass byte/schema/frame/unit checks. Product availability is resolved;
  the full map-processing/foreground and statistic-specific null laws remain
  required. No PR3 L03 acceptance was renamed or promoted.
- Preserved failed guessed IRSA/CMB-S4 paths and Globus HTTP404 probes; changed
  to linked official IRSA/NERSC routes. No authentication wall was bypassed.
  Updated the continuation's stale 4GiB batch cap to null to match the owner's
  uncapped download instruction and the existing reserve-only policy.

## Stage application and validation

R1 fixes the existing identity and original acceptances; R2 inventories and reuses
primary/legacy sources; R3 distinguishes physical, conditional and exploratory
statements; R4–R5 produce explicit weight and redshift-response formulas; R6 is
the independent Astra review; R7 is the exact/finite calculation and source check;
R8–R10 are the scoped decision, reusable theory/code and missing-input handoff.
C1–C4 bind the retained source, formula, arithmetic and small execution DAG;
C5 implements the consumer; C6–C8 test exact witnesses, numerical stability and
artifact provenance; C9 is the independent review; C10 preserves the disposition.
No stage count is used as a research-progress or acceptance metric.

Executed in the existing repository `.venv`:

- `scripts/htt_open_input_packet.py` and `--node V03`: original 17/42; direct
  external S02,S04,L03,H02,V03,B02,K03,K04; no original scientific-ready node.
- `pytest -q tests/htt/test_open_input_packet_frontier.py`: **7 passed**, exit 0.
- `data/verify_sources.py`: exit 0; hashes and row counts confirmed independently.
- `data/pr4/verify_pr4.py`: exit 0; independent reviewer recomputed hashes,
  full T/Q/U counts, archive/member schema and matched `VALIDATION.json` exactly.
- Explicit-eight-ID acquisition plan: correct external root, eight selected
  resources, null byte caps, no `--budget-gib`; plan-only exit 0.
- Selection regression/artifact commands and first failures are preserved in
  [selection/REPORT.md](selection/REPORT.md): **12 passed**, artifact generation
  exit 0. [Independent review](INDEPENDENT_REVIEW.md): **SCOPED_PASS_C0** after
  the targeted repair episode; no unresolved blocking finding in this scope.

Original `PUBLICATION_DAG.json` remains byte-identical, SHA-256
`bcdc21a55863657c0da478e541132e0490267be6a56759d642b39698d0b14890`.
The continuation diff changes only current_handoff, F04/F06/F07 next_action,
frontier_status_note and the stale batch cap. All status, acceptance and
dependency fields are unchanged. Prior HOLD/UNKNOWN/R9 and accounting survive.

## Remaining transitions

The [README input table](README_KO.md#필요한-관측자료와-물리-입력) names the exact
remaining payloads/formulas and runnable cache/packet commands. F04 requires
source-matched correction derivatives and finite remainders; F07 requires the
complete parent/contributor/joint law or justified weight/support/event bounds;
F08 requires physical polarized and nonradial transfer/joint-error inputs.
F06 requires a matched processed-total/foreground operator and chosen-statistic
null law. Qualified new input triggers the respective packet and original
acceptance, then its dependents. The present source search is bounded and does
not prove absence from all public archives.

## Next ready action executed after the first checkpoint

The first research/source unit was committed and pushed as
`d2c11c4a850fadbf1cf181c190c3c30f48425ff3`; provider success and remote ref matched.
The existing checkout was clean after that publication. The theory agent then
specified a descriptive PR4 Q/U half-sum/half-difference calculation that is
executable without supplying a foreground/noise/null interpretation.

Fresh bounded `pr4_split_20261022` (`gpt-6-sol/high` requested; observed UNKNOWN)
owns only `pr4_comparison/`. A separate fresh read-only reviewer,
`pr4_comparison_review_20261022` (`gpt-6-astra/xhigh` requested; observed UNKNOWN),
did not author the result. At most four agents including parent remained active;
no nested agents or child publication. Historical campaign results were reused.

The new [comparison](pr4_comparison/REPORT.md) processes 5,214,208 native pixels
on the correctly converted/lifted binary mask, 41.4388% of the sky. Native mean
half-sum and half-difference powers are 10,124.469731 and 10,045.456339 microK_CMB²;
their ratio is 0.9921957994817991. Four focused tests passed. Actual parallelogram,
cross-product and common-basis-rotation checks have maximum guarded relative
residual 8.02e-15 against 1e-10. The plotted NSIDE16 scalar is the RMS over native
children, with no spin-2 Q/U downgrade, smoothing, beam inversion or null claim.
The first two plot layouts overlapped; the worker repaired presentation and
retained the failures in the report. The numerical results stayed unchanged.

The [separate independent review](pr4_comparison/INDEPENDENT_REVIEW.md) returned
**SCOPED_PASS_C0**. A weak default absolute tolerance in one test was repaired;
the reviewer closed the exact one-line change and confirmed four tests passing.
It also verified native-pixel angular ancestry and independent raw-pixel samples.
No full map was rerun for that test repair or review. All original acceptances
remain unchanged after this second research unit.

The next stronger PR4 transition requires the exact processed-total/foreground
law, applicable map/mask/beam/weight response and statistic-specific joint null
coverage. Current source availability and descriptive power do not supply those
inputs. F06, original L03 and the distinct physical atlas remain HOLD.
