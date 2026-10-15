# Codex handoff: C8-OBS-MES-EPS local evidence and continuation

Date: 2026-10-16 KST. Canonical repository: `cosmosapjw-quantum/htt_base`. User's EXISTING checkout, when reachable: `/home/cosmosapjw/Dropbox/bianchi/htt_base`. Do not make a new clone, Git worktree, or full repo copy; do not clean/reset/stash or overwrite previously uncommitted work. Existing stacked PR #533 HEAD `13d8d85fa470d645d008986e8f77d8d0f70fdf54`, followup draft #534 HEAD observed `635e5e83a50f947a2c92b9cc90a7f99aa68e1cd7`; the exact newer PR #535 head may change and MUST be fetched freshly. `main` remains publication branch, no merge authorization.

## Source-grade work already done in ChatGPT sandbox

- Exact source snapshots: bundled `inputs/loop5`, `inputs/loop6`, `inputs/loop7`, `inputs/ffp_response`, `inputs/ffp_pilot`, `inputs/loop2`; the bare `C8_OBS_MES_EPS_RESULT.json` alone is NOT sufficient to replay. `src/mes_eps_diagnostic.py` enforces exact immutable source SHA-256 and source metadata correspondence; no FITS download necessary for this bounded replay. Original raw Planck on `/mnt/extdrive/workdir/raw` remains authoritative for new independent physical validation, but is NOT contained in the archive.
- Stage under `C8-OBS-MES-EPS`, original Loop7 DAG. Nine genuine Planck PR3 processing products are SAME-SKY. Six FFP response options are SIMULTANEOUS 6 processing branches for each one of 300 paired latent skies. Train 60, compare 240 held-out under existing fixed sources; newly chosen spread statistic is retrospective, not a physical p-value.
- Registered PR124 geodesic MES `B_sigma=(5/3)e1+3e2+(3/7)e3`, `B_omega=(10/3)e1+(2/15)e2` and strict hierarchy `0 <= e1 < (43/25)e2+(9/35)e3` only if covariant eps fields are qualified. Calculating `eps1=0` is an ALGEBRAIC scenario, not measured residual dipole. No acceleration/anisotropic-curvature anchor, no true Bianchi shear or tilt posterior.
- Delivered scoped product: 14 Python tests PASS in ChatGPT container; 3 diagnostic figures; exact source/hash and zero-rollover fail-closed tests. No user's local machine execution or native subagent reviewer this turn; scientific HOLD remains.

## First action: preserve and run locally without touching dirty tracked files

1. Obtain `HTT_C8_OBS_MES_EPS_HANDOFF_20261016.zip` from the user-facing conversation download or from its ChatGPT Library backup. Unzip into a **temporary STAGING directory, NOT the existing repo checkout**. For archive path `$PKG`, use:

```bash
STAGE=$(mktemp -d /tmp/htt-c8-mes-eps.XXXXXX)
unzip -q "$PKG" -d "$STAGE"
PKGROOT="$STAGE/htt_mes_eps_20261016"
cd "$PKGROOT"
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 bash LOCAL_RUN.sh
```

2. Inspect exact canonical repository state **before any write**:

```bash
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
pwd; git branch --show-current; git rev-parse HEAD
git status --porcelain=v1 -uall
# Do not switch branches if it would change dirty tracked/untracked files.
```

3. Compare `PKGROOT/docs/SOURCE_MAP.json` with the repo's source and PR124/MES registry; run stage `C8-OBS-MES-EPS` tests and inspect the generated `C8_OBS_MES_EPS_RESULT.json`. Check genuine nine-source Loop5 identical-mask C2/C3 parity, FFP first processing row identity with 300 original paired simulations, and correct conditional rank 73/241 and 45/241. Do NOT merge Loop5 and K1 FFP into one noise distribution. The source-conditioned CMB amplitude is NOT EGS covariant epsilon with gradient bounds.

4. Independently audit/repair only an observed defect, then stage any production changes on **one owned path** after source comparison and targeted tests. Authoritative code is allowed to reuse the source-locked diagnostic but this archive's `src` is separate from repo modules. Do not silently replace `htt/obsstat/typed_xqpi_observation_bridge.py`, `htt/obsstat/cf4_apparent_kinematic_distribution.py`, or existing Loop5-7 source; those are different dirty research units. Preserve earlier raw outcomes as immutable, write a new version.

5. Update the canonical dependency DAG only after checking `docs/codex_handoff/pr_backlog.yaml`, `pr_status.yaml` and actual branch/PR ancestry. Link this bounded `C8-OBS-MES-EPS` scientific input closure to Loop7 `NEXT_RESEARCH_DAG.json`, with state `COMPLETED_SCOPED_CONDITIONAL; LOCAL_TESTED` only after an actual local PASS. Mark *physical* `EPS_COVARIANT_EGS` and `T8-GEOM-SOURCE` as blocked, not zero. If a fresh, independent reviewer is exposed, perform ONE bounded pass; if not, explicitly `NOT_RUN`, do not manufacture a receipt.

6. Only after tests/review make a safe additive commit to a dedicated PR branch, push, record remote HEAD/tree and actual provider ACK. Do not merge main or the draft parent chain. Preserve a one-row status ledger for each step with fields test/backup/remote commit/DAG/next action. A backup upload ACK does not imply restore verified.

## The actual next physics input to acquire, not simulate

- The coupled masked-sky response `A_L`, `K_LH` beyond finite l6..16 with beam/compsep/foreground/FFP E2E noise and sky/covariance selection, in the SAME processing and observer frame.
- A bound on unobserved high-l amplitude and the physical residual cosmological dipole after observer motion, plus almost-EGS spatial/time covariant derivatives (`C1,C2`). Null placeholders are prohibited.
- Only then translate normalized source epsilon field into same-congruence shear/vorticity one-way MES anchors, not a total-defect x/Q ceiling.

The next `C8-REAL-JOINT` remains blocked by missing physical selection, transfer and simultaneous all-sector covariance; local source exploration and finite mask response verification may proceed on an independent lane.

## Stop/return contract

Return exact `git rev-parse HEAD`, per-file SHA-256 for modified files, source hashes, local command/exit/test count, any failure distinction (scientific/numerical/implementation/runtime), current PR URL/head, backup object IDs, DAG state and next ready item. Do not claim success from historical sandbox tests alone. If local desktop access is still missing, use the packaged results as the bounded handoff and stop at `LOCAL_RUNTIME_BLOCKED`, without installing services or trying to circumvent access controls.
