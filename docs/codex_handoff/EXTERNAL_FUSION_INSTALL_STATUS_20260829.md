# External fusion installation and data status — 2026-08-29

## Status

```yaml
document_role: OPERATIONAL_STATUS_ONLY
source_run: EXTERNAL-FUSION-INSTALL-20260829
repository_base: c9b2af5a3a3e442a988895c0fd970f1ecdf23b8f
core_installation: COMPLETE
active_downloads_at_closeout: 0
active_tmux_sessions_at_closeout: 0
blocked_external_components:
  - CONCEPT-1.0.1
  - sbibm-1.1.0
  - native_bianchi_boltzmann
scientific_claim_promotion: false
native_solver_validation: false
publication_readiness_claim: false
```

The available data placement, isolated environments, repository virtual
environment, and bounded installation/smoke checks are complete.  The three
blocked external components above remain explicitly unavailable; none was
replaced, emulated, or reported as installed.  This document records an
operational snapshot and does not establish scientific validity, transfer
validity, Bianchi-family identification, or publication readiness.

## Data holdings and storage

The content inventory finished on 2026-08-29 at 14:14 KST, before the isolated
environment tree was added.  It traversed the external workdir without errors
or broken symlinks and found 18,256 unique regular files totaling
1,185,632,921,952 bytes.

| Scientifically reviewed category | Bytes | Decimal GB | Disposition |
|---|---:|---:|---|
| Observational inputs | 120,042,470,154 | 120.04 | retained |
| Mock and simulation data | 937,273,565,097 | 937.27 | retained |
| Quarantined partial files | 1,365,789,644 | 1.366 | excluded from science admission |
| Code, archives, outputs, logs, manifests, and other auxiliary material | 126,951,097,057 | 126.95 | retained |
| **Total inventory snapshot** | **1,185,632,921,952** | **1,185.63** | byte-conserving total |

After adding the isolated environments, the final external-workdir allocation
was 1,202,027,061,248 bytes.  All payloads reside beneath
`/mnt/sn850x2t/htt_base_e2e/workdir`; repository `workdir/` is a link layer
allocating 57,344 bytes.  New acquisitions must first use:

```bash
workdir/prepare_external_download_dir.sh raw/<dataset>
```

This prevents a new payload from being written to the main NVMe by accident.

### Capacity snapshots

Storage values are time-dependent and are therefore recorded with their role:

| Measurement | Main NVMe free | Main use | External 2TB NVMe free | External use |
|---|---:|---:|---:|---:|
| Installation closeout snapshot | 86,493,167,616 B | 91% | 484,857,442,304 B | 76% |
| Documentation-time live recheck | 129,638,506,496 B | 87% | 484,857,442,304 B | 76% |

The run removed 65,925,873,664 bytes of mechanically verified inactive Cargo
caches from `/tmp`.  Its closeout inventory left 145,772,138,496 readable bytes
under `/tmp`; unrelated research worktrees and the active VigilODE build were
preserved.  The change in main-NVMe free space after closeout is reported as a
live measurement only and is not attributed to this run.

## Download completeness and remaining ETA

No data-transfer process or tmux session remained at closeout, and a live
documentation-time recheck also found none.

| Dataset or lane | State |
|---|---|
| FFP10 SMICA CMB | 999 admitted maps; only `00970` is absent, as an explicitly recorded upstream absence |
| FFP10 SMICA noise | 300/300 complete |
| DESI BGS | 17/17 files match their aria2 SHA-256 expectations |
| KiDS | candidate archives match their receipts |
| Planck PR3 | required maps and masks present |
| Selected Planck PR4 | nine 30--857 GHz frequency maps present |
| WebSky selected | seven selected components present |

The only presently identified optional remainder is the FFP10 Commander
`00002`--`00006` set.  Existing partial bytes remain quarantined and
1,654,149,556 bytes are needed to reach five common-size files.  No official
direct URL and checksum set is currently bound, so the lane is
`NOT_RUNNING / WAITING_FOR_AUTHORITATIVE_PLA_ROUTE_AND_HASHES`.

Once an authoritative route exists, idealized transfer-only estimates are:

| Sustained rate | ETA for 1,654,149,556 B |
|---:|---:|
| 2 MB/s | 13m 47s |
| 10 MB/s | 2m 45s |
| 25 MB/s | 1m 06s |

Matched PR4 simulations, additional WebSky components, Planck--unWISE and PSZ
remote-field products, and CMB-S4 PANEX inputs are PR-specific candidates, not
missing mandatory inputs.  They require a consuming work unit to freeze the
selection before acquisition.

## Installed code and environments

Here `INSTALLED_VERIFIED` retains the source run's machine-state vocabulary: a
version/import/help check or a bounded functional smoke passed.  It must not be
read as scientific validation.

| Profile group | Installed and checked components |
|---|---|
| Low-ell and maps | CAMB 1.6.6; CLASS/classy 3.3.4.0; GLASS 2026.2; healpy 1.20.0; NaMaster/pymaster 3.0; PySM3 3.4.6; lenspyx 2.0.52 |
| Harmonic and morphology | S2FFT 1.4.0; S2WAV 1.0.4; CVXPY 1.9.2; CVXPYlayers 1.2.0 |
| Inference | SACC 2.4; Firecrown 1.15.2; sbi 0.27.0; NumPyro 0.21.0; Cobaya 3.6.2 |
| Survey and clustering | pyccl 3.3.4; COFFE 3.0.1; pycorr 1.0.0; pypower 1.0.0; Snakemake 9.26.1; Corrfunc 2.5.3 |
| Simulation and support | JaxPM 0.0.2; nanoCMB; PySCo 1.0.9; pspy 1.8.4; HEALPix 3.83; revival_core 0.2.0; `htt-external-fusion` 0.1.0 |

The `inference` and `morphology_s2wav` profiles use
`torch==2.13.0+cu132`.  Both performed an actual CUDA tensor reduction on the
NVIDIA GeForce RTX 3090; this is a runtime smoke, not a morphology or inference
validation result.

The repository environment is fully externalized:

```text
/home/cosmosapjw/Dropbox/bianchi/htt_base/venv
  -> /mnt/sn850x2t/htt_base_e2e/venvs/htt_base-py312-20260829
```

It uses Python 3.12.3, passes `pip check`, imports BASS/HTT/MIO and the retained
TSC/Teff/`tsc_legacy` compatibility surfaces, and passed the focused repository
smoke (`6 passed`).  TSC/Teff remain legacy/document-only owners.

Activation:

```bash
deactivate 2>/dev/null || true
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
source venv/bin/activate
```

No completed profile requires a system/root installation or `sudo`.

## Explicit blockers

| Component | Status | Exact boundary |
|---|---|---|
| `sbibm==1.1.0` | `BLOCKED_EXTERNAL` | Upstream GPy fails on the available Python/NumPy build paths; the bounded retry budget was exhausted and no broken environment was retained. |
| `native_bianchi_boltzmann` | `BLOCKED_EXTERNAL` | No authenticated solver-delivery receipt or implementation is present.  No substitute solver or emulation was created. |
| CONCEPT 1.0.1 | `BLOCKED_EXTERNAL / STOP_BUDGET` | The official isolated installer reached SciPy 1.7.3 and repeated the same Cython interpreter mismatch 55 times.  No SciPy or CONCEPT executable was produced; the incomplete runtime was removed after preserving compressed logs and hashes. |

The retained CONCEPT status is at:

```text
/mnt/sn850x2t/htt_base_e2e/workdir/
  external_fusion_round3_20260722_envs/logs/
  concept-1.0.1-20260829/STATUS.md
```

## Dropbox and Git state

- `user.com.dropbox.ignored=1` is set on repository `workdir/`.
- Dropbox remote `/bianchi/htt_base/workdir` was already absent; there was no
  uploaded payload tree to delete.
- The storage/install run did not restore, overwrite, or commit source changes
  owned by parallel jobs.
- Canonical Git status contained zero tracked or untracked entries at closeout
  and again at documentation-time recheck.
- A stale VS Code “too many active changes” warning can be cleared with
  **Developer: Reload Window**, followed by selecting
  `/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python`.

## Claim and evidence boundary

| Claim ID | Owner | Status | Evidence type | Claim tier | Caveat |
|---|---|---|---|---|---|
| `XFI-DATA-SNAPSHOT-20260829` | common | `VALIDATED` | artifact | C0 | Fixed inventory snapshot; not a live catalog after later writes |
| `XFI-INSTALL-REACHABILITY-20260829` | common | `SMOKE_TESTED` | test | C0 | Import/help/targeted functional checks only |
| `XFI-CUDA-RUNTIME-20260829` | common | `SMOKE_TESTED` | test | C0 | CUDA execution only; no scientific-output validation |
| `XFI-EXTERNAL-BLOCKERS-20260829` | common | `VALIDATED` | artifact | C0 | Installation and delivery blockers, not scientific refutations |
| `XFI-SCIENTIFIC-PROMOTION-20260829` | manuscript | `FORBIDDEN` | none | C0 | No native solver, transfer, family-ID, or publication claim follows from installation |

The controlling host-local evidence is preserved at:

```text
.agent-harness/runs/EXTERNAL-FUSION-INSTALL-20260829/artifacts/
  XFI-INSTALL-LEDGER.md
  XFI-WORKDIR-001.inventory.json
```

Those run artifacts are local execution evidence rather than committed source
authority.  This committed status document summarizes them without copying raw
data, private manifests, environments, or failure logs into Git.
