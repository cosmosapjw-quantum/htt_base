# HTT P2/L01 R10/C10: repo-import recovery, native split-source intake and science handoff

Date: 2026-10-17 Asia/Seoul. Parent Draft PR #558 HEAD `5dc7ffefcfbcb353f51cf08b2aca11d29b9d51f4`.
This is a **stacked Draft PR**, not a main merge, manuscript submission or fresh scientific detection.

## R10: actual result and rigorous interpretability

The user's original local R8/C8 results are inherited as **user-reported native observations**, not recomputed with the inaccessible Planck maps:

- Common and three-way mask `K_c,K_t: R^90 -> R^64` (ell 6..8 E/B to ell 2..5 E/B).
- `||K_t-K_c||_2 = 0.4396287723908507`, `||(K_t-K_c)_{B<-E}||_2 = 0.2564294649638681`, numerical rank of the full difference 64.
- For a shared unknown high coefficient `h`, exactly `Delta y=(K_t-K_c)h` and `Cov(Delta y)=Delta K C_h Delta K^T`. The finite sharp E->B difference bound `0.2564294649638681 R_E` requires an independently justified `||h_E||<=R_E`.
- `ell>=9`, foregrounds, asymmetric instrumental/processing response, physical amplitude prior, release-matched FFP10 and actual Q/U residuals are **NOT_ESTABLISHED**. Neither a physical B anomaly nor a publication-grade Planck null follows. The exact full-row-rank claim remains conditional on an externally justified operator-error bound; reported numerical rank is not a formal rank certificate.

### New constructive split-source lemma

Let independent sample-level noise `n_i` satisfy `E[n_i]=0`, `Cov(n_i,n_j)=sigma_n^2 delta_ij`. For sample sets A,B define `bar_n_A=|A|^{-1} sum_{i in A}n_i` and similarly B. Then

`Cov(bar_n_A,bar_n_B) = sigma_n^2 |A intersect B|/(|A||B|)`.

This follows by exchanging sums and evaluating the Kronecker delta. In an eight-sample manufactured half-mission vs alternating odd-even split, `A={1,2,3,4}`, `B={1,3,5,7}`: their variances are both `sigma_n^2/4`, covariance `sigma_n^2/8`, and correlation `1/2` (exact Wolfram computation). This **does not measure a Planck noise cross-covariance**. Real mapmaking correlated noise and systematic terms can invalidate the iid assumption. It does demonstrate why HM/OE split images must not be automatically counted as four independent physical null skies; only the actual shared-sky processing and joint simulation law can qualify that assumption.

Literature comparators: [Planck 2018 IV](https://arxiv.org/abs/1807.06208) on component-separated polarization noise/systematics, [Planck 2018 VII](https://arxiv.org/abs/1906.02552) on isotropy tests and matched simulations. Official [NASA/IPAC PR3 product index](https://irsa.ipac.caltech.edu/data/Planck/release_3/all-sky-maps/matrix_cmb.html), [full SMICA header](https://irsa.ipac.caltech.edu/data/Planck/release_3/all-sky-maps/previews/COM_CMB_IQU-smica_2048_R3.00_full/header.txt). The latter specifies ten float32 component-map columns with NAXIS2=50,331,648 and a 4097-row `INT_BEAM/POL_BEAM` table.

## C9 observed defect repair, C10 executable handoff

These are distinct observed failures and not defects in `Delta K`:

| Object | Observed defect | Failure kind | Actual repair |
|---|---|---|---|
| Git worktree | `fatal: detected dubious ownership` | runtime/environment Git trust | Inspect trust/owner; use path-specific global `safe.directory` only for the user's controlled worktree. Never `safe.directory=*`. |
| Tests + C9 CLI | `ModuleNotFoundError: l01_k_spectral_certificate / test_l01_k_certificate` | implementation/packaging | Explicit `src/l01_repo_imports.py` and `tests/conftest.py` import previous versioned `R8_SPIN2_S02_COHERENT_20261017` code without copying it. Original C8 and C9 CLIs import the bridge. |
| Full SMICA FITS | `DOWNLOAD_INCOMPLETE` | transfer, not astrophysical invalidity | Keep `.part`, retry up to `--attempts 3` with exact HTTP 206 Content-Range matching; no Range-ignore overwrite; structural validation checks entire HDU chain including the full POL_BEAM extension. |
| HM/OE split products | Four successful source-file downloads | user-reported provenance | Preserve four originals. New validation reuses existing files without networking and checks multi-HDU structural integrity before calling them usable data inputs. |

### User-reported source intake (NOT verified by this assistant on user machine)

All four local files reported `DOWNLOADED_FITS_FRAMING_VALID`, each 603,990,720 bytes:

| Product | User local SHA256 |
|---|---|
| HM1 | `736338208cf0b494c3b6c13c444f116262c8052dcb4a7842dc738bf6a4a426b0` |
| HM2 | `0a4dc860a6f7bbdb5980cd7ac1d187ba9139a383c9c47f159e069281c3d5f3a5` |
| OE1 | `5473304ed71348cb346b335bca0deb417c9dd3f0286c7e3d2dfd5e1fc93f503a` |
| OE2 | `da9c3e3e09fdff87ada31db00417ae7688facc8b47756576ed8daec12fe1e2f0` |

No externally signed/publisher SHA is claimed. Full 1.9-GiB product is still `NOT_ADMITTED_TRANSFER_INCOMPLETE` until a verified HTTP resume and complete FITS check succeeds.

### Verification provenance

A faithful reconstructed GitHub stacked-directory layout in the ChatGPT Python sandbox was tested, using predecessor R7/C7 and C8 test sources, reconstructed R9/C9 contracts plus newly repaired import/FITS/retry modules. **74/74 pytest PASS** (Python sandbox, NumPy/SciPy/pytest); actual HTTP 206 resume and full/split FITS layout tests use manufactured tiny payloads, not real IRSA network bytes. Byte SHA readback of newly posted source/test files is separately verified. The byte-exact final GitHub tree itself, real user worktree and native ~2GiB full SMICA download are **NOT_RUN** in this sandbox; local Desktop Commander terminal remains quota-blocked. The R9/C9 transcribed sandbox test implementation was semantically aligned but not byte-identical to the entire existing source in GitHub, so this is explicitly a bounded **source-equivalent** regression run rather than final-head CI.

No native subagent dispatch is available: `native_subagent=NOT_RUN`. No false scientific gate promotion.

## Direct repo terminal execution: user-owned clean checkout (2026-10-17 correction)

**IMPORTANT CORRECTION to the prior guidance.** The user reported an existing
\`/mnt/extdrive/workdir/htt_l01_repo_r9c9\` whose directory **and .git file
are root:root** and whose \`git status --porcelain\` was nonempty. The earlier
conditional branch switch was therefore skipped, but subsequent tests/downloads
still ran **stale PR #558 code**, producing the old \`ModuleNotFoundError\` and
\`--attempts: unrecognized arguments\`. The GitHub PR #559 contains the
import bridge and \`--attempts\`; the old detached HEAD did not.

Do **not** \`chown -R\`, reset, clean or overwrite the root-owned worktree to
continue. Do **not** use global \`safe.directory=*\`. Keep the old worktree for
later inventory/recovery. Create a new worktree in the user's own home directory:

\`\`\`bash
set -euo pipefail
REPO="$HOME/Dropbox/bianchi/htt_base"
BR=research/htt-sixpaper-p2-l01-r10c10-runtime-recovery-20261017
WT="$HOME/worktrees/htt_l01_r10c10_clean_20261017"
mkdir -p "$HOME/worktrees"
if [[ -e "$WT" ]]; then
  echo "STOP: $WT already exists; choose an unused user-owned path." >&2
  exit 2
fi
git -C "$REPO" fetch origin "$BR"
git -C "$REPO" worktree add --detach "$WT" "origin/$BR"
cd "$WT"

# This fails closed unless HEAD exactly matches the fetched branch, the
# checkout is clean, and all predecessor module imports/CLI options work.
python docs/research_program/observational_publication_20261015/L01_R10_C10_RUNTIME_RECOVERY_20261017/scripts/l01_checkout_guard.py
\`\`\`

**Only if the last command prints \`PASS_EXACT_HEAD_CLEAN_IMPORTS\` and exits
zero** continue in the **same terminal**:

\`\`\`bash
S=docs/research_program/observational_publication_20261015/L01_R8_C8_TWO_MASK_STABILITY_20261017
ROOT=/mnt/extdrive/workdir/htt_open_data
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m pytest -q "$S/tests"

# Already downloaded source files are verified without a second download.
python "$S/src/fetch_planck_pr3_smica.py" \
  --root "$ROOT" --products hm1 hm2 oe1 oe2 --attempts 1

# Preserve the old full .part and use a verified HTTP 206 Range to resume.
python "$S/src/fetch_planck_pr3_smica.py" \
  --root "$ROOT" --products full --attempts 3

# Only after a completely qualified full SMICA source exists:
python "$S/src/l01_r9c9_same_sky_beam.py" \
  --native-receipt "$ROOT/provenance/L01_NATIVE_PR3_POL_K64x90_v2.json" \
  --spectral-receipt "$ROOT/provenance/L01_NATIVE_SPECTRAL_CERT_20261017.json" \
  --c8-receipt "$ROOT/provenance/L01_R8_C8_TWO_MASK_STABILITY_20261017.json" \
  --smica-full "$ROOT/planck/PR3/cmb/COM_CMB_IQU-smica_2048_R3.00_full.fits" \
  --out "$ROOT/provenance/L01_R9_C9_SAME_SKY.json"
\`\`\`

If full source transfer fails, the shell stops because \`set -e\` is active.
Do not run the \`--smica-full\` step against \`.part\`, or relabel
\`FITS_FRAMING_VALID\` as a physical null. Existing HM/OE files and native NPZ
are never overwritten. This correction adds only a checkout preflight and
repo-layout regressions, not a new paper claim or a source-lock migration.

## Canonical DAG and next scientific work

Original authoritative `PUBLICATION_DAG.json` blob `ac4a94c3da13f142eaab3b06b5275b58096c95e1`; READY `L01,S02`. P1 1/6; P2 0/6; P3 2/6; P4 1/6; P5 1/5; P6 2/6; COMMON 7/7. **14/42 completed_scoped**, 28 pending; all papers `NOT_READY_TO_SUBMIT`.

- P2/L01 remains pending. The mask-geometry lane has conditional verified source/operator identities; full beam conditional adapter and sampled Q/U injection/null remain to be executed, and ell>=9 remainder is still unbounded absent physical/source assumptions.
- L03 matched FFP10 joint end-to-end null/exchangeability still a separate external physical blocker.
- HM/OE are split data products from the same sky. Their four file identities never equal four independent CMB sky realizations.

Next DAG-bound productive step after native intake: compute same processing on selected I/Q/U signal and split-map differences, quantify matched joint covariance, and extend high-ell transport beyond ell8 with an explicitly justified source/beam/foreground model. No claim about anomaly significance before a qualified matched simulation bank.
