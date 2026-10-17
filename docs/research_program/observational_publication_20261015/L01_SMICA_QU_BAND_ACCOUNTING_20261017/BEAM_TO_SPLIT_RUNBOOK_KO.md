# L01: 완료된 POL_BEAM 계산에서 실제 Q/U 분할 스펙트럼으로

2026-10-17 Asia/Seoul. Parent HEAD `66fc040291318f12d12c9f56851fd5b6133c5830`, existing Draft PR #559. Work scope: reported conditional-beam result admission and completion/validation of the next checkpoint-based split-spectrum calculation. No new ten-stage campaign or physical detection claim is implied.

## 1. Source authority and closed work

The user reported `PASS_SCOPED_FINITE_R9C9` with full SMICA FITS SHA256 `60952c645eb33d151905ddf5837477e15ca02a3261feca4ceca3c3feece4f9ac` and original native receipt SHA256 `7b4763afe8e5d30a02be296b0d4f7281a30f4e80937975dcda5f929643c2a7b6`. The numbers below are from user-local execution, not a new assistant FITS run.

| Quantity | No added beam | Observed-low diagonal beam | Low-deconvolved diagonal beam |
|---|---:|---:|---:|
| Total difference operator norm | 0.43962877239085046 | 0.43957475026923726 | 0.4398281962820499 |
| E-high to B-low block norm | 0.2564294649638681 | 0.2564034467308952 | 0.25654692992083233 |

Relative scalar norm changes are -0.0122881% and +0.0453619% for the total operator, -0.0101464% and +0.0458079% for the E-to-B block. These are **changes of norms**, not bounds on the norm of the operator difference, nor bounds on physical B contamination. The approximation is axisymmetric, equal E/B, diagonal beam in the fixed low ell2..5 and high ell6..8 model. Full component separation and ell>=9 are not controlled by this statement.

The current remote already contains `src/l01_smica_processed_bands.py` (Git blob `ac45c6a44e86af2fd1200e4796b8e2b041d6354a`), its tests, and `THEORY_AND_SCOPE_KO.md`. These three additions were recovered by comparing parent `4f32e218...` with `66fc0402...`. Their native transform/projection implementation is reused **unchanged**, not replaced by the unpublished code described in an earlier chat.

No new dataset download is needed. Existing full/HM1/HM2/OE1/OE2, three PMASKs and the original two K NPZ are the inputs. The user's successful prior repository collection had 41 tests; old reconstructed 80-test claims are not treated as the same collection.

## 2. Estimand and exact split identities

Write the delivered maps as x_i=A_i s+r_i+n_i, and use exactly the same native window and spin transform T_W for every product. Units are K_CMB, frame Galactic, COSMO polarization convention. Define a_i=T_W x_i and a_+=(a_1+a_2)/2, a_-=(a_1-a_2)/2. Then

```
a_- = (1/2) T_W [(A_1-A_2)s + (r_1-r_2) + (n_1-n_2)].
```

Thus a half difference is not automatically pure noise. The zero-mean noise matrices satisfy

```
N_+ = (N_11+N_22+N_12+N_21)/4
N_- = (N_11+N_22-N_12-N_21)/4
N_+-N_- = (N_12+N_21)/2.
```

The same equations hold after projection with T_W on the left and its adjoint on the right. A measured map cross-spectrum is not an ensemble noise covariance estimate.

For a fixed ell define C_ij^{XY}=(2ell+1)^(-1) sum_m a_i,lm^X conjugate(a_j,lm^Y), with X,Y=E,B. For real sky fields C_ji=(C_ij)^T and

```
C_++ - C_-- = (C_12+C_21)/2.
```

The EE and BB entries equal the corresponding split cross-spectrum. The EB entry equals `(C_12^EB+C_21^EB)/2`, not an arbitrarily selected ordered cross. The code stores EE, EB, BE and BB and does not clip negative cross spectra or the signed EB signal. Using healpy m-major arrays, the m=0 contribution is counted once and m>0 twice as `2 Re(a_lm b_lm*)`. Spectra are in K_CMB^2; a diagnostic band sum is `sum_l (2l+1) C_l/(4*pi)`.

Wolfram exact complex 2x3 array calculation returned a zero 2x2 residual for the matrix identity and for the noise-covariance identity. This is a mathematical check, not a Planck measurement. The cross matrix of that manufactured example has negative diagonal entries, demonstrating why positivity must not be imposed on cross spectra.

## 3. Connection to the existing finite-band accounting

The producer retains its native mask policy: strict >0.5 intersection of the three original NSIDE2048 NESTED PMASKs. Invalid Q/U inside that fixed common window is rejected, not silently dropped separately per map. It reads Q_STOKES/U_STOKES, not inpainted columns; reorders NESTED to RING; analyzes spin 2; then synthesizes finite bands on RING64 for the existing projectors. Q/U is not scalar-averaged and delivered-map beam is not applied a second time.

Its exact finite processed-map decomposition is

```
y_i = a_tilde_[2:5] + K_i a_tilde_[6:8] + P_i S_[9:L] a_tilde_[9:L].
```

The next script consumes the existing producer JSON/NPZ checkpoints. It does not alter this transform, compute a new K, deconvolve a beam, or re-run the large native maps. It provides full-map and individual split autos, HM/OE half sums and half differences, symmetrized split cross spectra, full-minus-HM/OE-mean autos, and the cross-spectrum between HM and OE half differences.

These quantities refer to windowed DELIVERED-MAP pseudo E/B, including processing, masking, foregrounds and noise. They are not pure cosmic E/B or an anomaly p-value. L=32 or L=64 is an output cutoff, not a proof of negligible physical ell>L leakage. Agreement of the sum/difference identity checks arithmetic, not correct physical sky recovery. Full mission is not assumed identical to the arithmetic mean of split maps.

## 4. Validation and evidence boundary

New module: `L01_R8_C8_TWO_MASK_STABILITY_20261017/src/l01_split_checkpoint_spectra.py`.
New tests: `tests/test_l01_split_checkpoint_spectra.py` in that same stage directory.

Executed in the current sandbox on the exact newly posted bytes: **30/30 tests PASS**, compileall PASS, standalone CLI help PASS. Tests cover lmax 2/5/16/32/64/128 against an explicit negative-m summation oracle, signed cross spectra, m multiplicity, identical/opposite maps, amplitudes 1 through 1e-100, spin low-mode/m0 validity, five-checkpoint CLI round trip, no overwrites and contract/source/window/code/hash/schema/symlink mismatches. The algebraic oracle is independent arithmetic, not a separate native harmonic transform.

At lmax=64 with manufactured coefficient amplitude 1e-6 K_CMB, the maximum scale-normalized split identity residual was `1.8463904527452848e-16`. Runtime: Python 3.13.5, NumPy 2.3.5. Native healpy/SMICA execution and whole-repository final-head CI: **NOT_RUN** here. The native producer remains an inherited implementation, not newly claimed native-validated by these 30 tests. No host subagent dispatch tool was present; native_subagent=NOT_RUN.

The checkpoint reader requires identical full producer contracts for all five maps, including window/code/dependency identities, plus their distinct pinned source hashes. Each NPZ digest is checked, pickle loading is disabled, and archive expansion is bounded. The output is written atomically without replacing an existing file. This is local checkpoint identity, not reauthentication of the original FITS server or a publisher signature.

## 5. Execute from the current user-owned worktree

Use the same branch and existing home worktree; do not recreate it, chown the old external-drive worktree, clear data or redownload SMICA. The following runs in a subshell and stops after any failed checkout/test/calculation. If there are local changes, it stops without discarding them.

```bash
bash <<'SH'
set -euo pipefail
WT="$HOME/worktrees/htt_l01_r10c10_clean_20261017"
BR=research/htt-sixpaper-p2-l01-r10c10-runtime-recovery-20261017
ROOT=/mnt/extdrive/workdir/htt_open_data
P=docs/research_program/observational_publication_20261015
S="$P/L01_R8_C8_TWO_MASK_STABILITY_20261017"

state=$(git -C "$WT" status --porcelain)
if [[ -n "$state" ]]; then
    printf 'STOP: preserve local changes before updating this worktree.\n%s\n' "$state" >&2
    exit 2
fi
git -C "$WT" fetch origin "$BR"
git -C "$WT" switch --detach "origin/$BR"
cd "$WT"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python "$P/L01_R10_C10_RUNTIME_RECOVERY_20261017/scripts/l01_checkout_guard.py"
python -m pytest -q "$S/tests/test_l01_split_checkpoint_spectra.py" "$S/tests/test_l01_smica_processed_bands.py"

BAND="$ROOT/provenance/L01_SMICA_WINDOWED_QU_L32"
python "$S/src/l01_smica_processed_bands.py" \
    --root "$ROOT" \
    --native-receipt "$ROOT/provenance/L01_NATIVE_PR3_POL_K64x90_v2.json" \
    --out-dir "$BAND" --lmax 32 \
    --products full hm1 hm2 oe1 oe2

python "$S/src/l01_split_checkpoint_spectra.py" \
    --band-dir "$BAND" \
    --out "$BAND/split_pseudocl_$(date -u +%Y%m%dT%H%M%SZ).json"
SH
```

The native producer reuses complete matching checkpoints on rerun. If an interrupted checkpoint or changed code/source contract is detected, preserve it and use a separately named output directory after investigating; never edit its hashes to pass. The postprocessor prints low-band full-auto, HM/OE-half-difference and full-minus-split-mean EE/BB/EB values, not only a PASS status. Detailed 2..5, 6..8 and 9..L quantities remain in JSON.

## 6. Stagewise publication and six-paper DAG

- R8 result admission: conditional POL_BEAM finite geometry closed by user stdout; no new beam run claimed.
- C5 source commit `ac39024ca9ce7e243b53a569b50f7a943594e8df`.
- C6 tests commit `9c9966656cbc21279d629996a7ea4918cda5c4d8`; tested code Git blob `96beda7c788519c40aaa11f502046b7d79726ca3`, test Git blob `255e0928b75b8c329c281c68cdb877d6e4b6df14`; remote readbacks match.
- Full machine-readable beam receipt and progress: `BEAM_RECEIPT_AND_SPLIT_PROGRESS.json` in this directory.

At every step the publication counts remain P1 1/6, P2 0/6, P3 2/6, P4 1/6, P5 1/5, P6 2/6, COMMON 7/7 = **14/42 completed_scoped**, 28 pending. READY L01/S02. L01 gains real-source conditional beam evidence and a tested next diagnostic; L03 still needs release-matched simulation/selection/foreground covariance and an admissible null. No main merge, manuscript submission or canonical 245-card backlog mutation.

## Primary references

- Planck 2018 IV, component-separated polarization and residual/noise limitations: https://arxiv.org/abs/1807.06208
- Planck 2018 VII, large-angle tests and matched simulations: https://arxiv.org/abs/1906.02552
- ESA Planck Legacy Archive CMB maps, split caveats and native conventions: https://wiki.cosmos.esa.int/planck-legacy-archive/index.php/CMB_maps
- Native spin transform API: https://healpy.readthedocs.io/en/latest/generated/healpy.sphtfunc.map2alm_spin.html

SciSpace used for discovery, with bibliographic dates reconciled against arXiv rather than inconsistent search-index dates. Exa retrieved official split cautions. The mathematical identities and numerical tests above are direct derivations/checks, not claimed novel theorems.
