# A33 · `HttForwardOutput` + `AtlasEntry` schemas

**Appendix**: A33 (§11.14.6 of `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3)
**Version**: 2026-04-19 draft (landed with DOS-A30-MIO Week 5 Day 7).
**Code anchors**:
  - [`bass_py/workspace/contracts/htt_forward_output.py`](../../bass_py/workspace/contracts/htt_forward_output.py)
  - [`bass_py/workspace/contracts/atlas_entry.py`](../../bass_py/workspace/contracts/atlas_entry.py)
**Related**: [A32 `MioCertificate` schema](A32_mio_certificate_schema.md);
[A38 HTT↔MIO cross-check protocol](#) (Week 7 CONTRACTS-02).
**Governing rules**: v3 §4.5.2 (interface table), §10.2 (table row 1 +
row 2), §4.5.6 (what MIO enables with these objects).

---

## A33.1 `HttForwardOutput` — BASS → HTT model-dependent theory bundle

### A33.1.1 Purpose

`HttForwardOutput` is the single hand-off object BASS produces for each
forward theory run (one parameter point, one Bianchi type, one axis
choice). HTT likelihood code consumes it to evaluate posteriors.

**Hard rules** (v3 §4.5.2):
- NOT observational data — the `C_ell_*` vectors are theory predictions.
- NOT an adequacy certificate — adequacy reporting is MIO's job
  (`MioCertificate.adequacy_indicators`).

### A33.1.2 Schema

| Field | Type | Purpose |
|---|---|---|
| `model_name` | `str` | e.g. `'BianchiI_tilt'`. |
| `bianchi_type` | `str` | Member of `{I, V, VII0, VIIh, IX, FLRW}`. |
| `axis_galactic_lb_deg` | `Tuple[float, float]` | Model preferred axis in Galactic degrees; `b ∈ [−90°, 90°]` enforced at `__post_init__`. |
| `ell` | `ndarray` (1-D, int) | Multipole grid. |
| `C_ell_TT` / `TE` / `EE` | `ndarray` (1-D, float) | Angular power spectra (K²); shape equals `ell.shape`. |
| `directional_summary` | `Mapping[str, float]` | Summary statistics feeding HTT's directional layer (`l_deg`, `b_deg`, `R`, …). |
| `shear_Sigma2` | `float` | Shear amplitude (s⁻²); non-negative. |
| `tilt_beta` | `float` | Tilt parameter. |
| `atlas_entry_hashes` | `Sequence[str]` | Hashes of `AtlasEntry` rows consumed to build this bundle. |
| `generated_by` / `git_commit` / `config_hash` | `str` | Provenance. |

### A33.1.3 Validation

The `__post_init__` rejects:
- Non-1-D `ell`.
- Mismatched shapes between `ell` and any `C_ell_*` vector.
- `b ∉ [−90°, 90°]`.
- `shear_Sigma2 < 0`.

See [test_htt_forward_output.py](../../bass_py/workspace/contracts/tests/test_htt_forward_output.py) for the regression gate.

### A33.1.4 Canonical example

```python
HttForwardOutput(
    model_name="BianchiI_tilt",
    bianchi_type="I",
    axis_galactic_lb_deg=(264.021, 48.253),
    ell=np.arange(2, 101),
    C_ell_TT=<99-vector>,
    C_ell_TE=<99-vector>,
    C_ell_EE=<99-vector>,
    directional_summary={"l_deg": 264.02, "b_deg": 48.25, "R": 0.91},
    shear_Sigma2=1.2e-8,
    tilt_beta=1.334e-3,
    atlas_entry_hashes=("<K_ell_v1_hash>",),
    generated_by="bass.spectrum.cl_assembly v0.8",
    git_commit="<commit>",
    config_hash="<cfg>",
)
```

---

## A33.2 `AtlasEntry` — BASS theory-atlas row

### A33.2.1 Purpose

`AtlasEntry` represents one tabulated row of a BASS pre-computed theory
atlas (e.g. the K_ℓ kernel used by `mio.extraction.shear_nonparametric`,
or a Sobolev A1–A5 atlas for the W_R window). Downstream code looks up
rows by `entry_hash`, interpolates between neighbouring parameter
points, and composes forward bundles.

**Hard rules** (v3 §4.5.2):
- NOT observational data.
- Membership in the atlas does NOT confer posterior meaning; it is an
  interpolation step, not an evidence update.

### A33.2.2 Schema

| Field | Type | Purpose |
|---|---|---|
| `atlas_name` | `str` | Identifies the atlas family (e.g. `'K_ell_v1'`). |
| `bianchi_type` | `str` | Geometry label (same enum as `HttForwardOutput`). |
| `parameter_point` | `Mapping[str, float]` | Coordinates of this row in parameter space. |
| `ell` | `ndarray` (1-D) | Multipole grid. |
| `kernel_values` | `ndarray` (1-D) | Tabulated kernel; `shape == ell.shape`. |
| `kernel_name` | `str` | Which kernel this row tabulates (`'K_ell'`, `'Sobolev_A1'`, …). |
| `generated_by` / `git_commit` / `config_hash` | `str` | Provenance. |
| `entry_hash` | `str` | Unique id for the row; non-empty. |
| `domain_caveats` | `Sequence[str]` | Optional scope-of-validity notes. |

### A33.2.3 Validation

The `__post_init__` rejects:
- Non-1-D `ell` / `kernel_values`.
- Mismatched shapes.
- Empty `entry_hash`.

See [test_atlas_entry.py](../../bass_py/workspace/contracts/tests/test_atlas_entry.py).

### A33.2.4 Canonical example

```python
AtlasEntry(
    atlas_name="K_ell_v1",
    bianchi_type="I",
    parameter_point={"Sigma2": 1.2e-8, "beta": 1.334e-3},
    ell=np.arange(2, 101),
    kernel_values=<99-vector>,
    kernel_name="K_ell",
    generated_by="bass.atlas.builder v0.3",
    git_commit="<commit>",
    config_hash="<cfg>",
    entry_hash="<sha-of-row>",
    domain_caveats=("valid_below_ell_30_only",),
)
```

---

## A33.3 Where these objects flow

### A33.3.1 Forward pipeline

```
BASS forward run
    │
    ├── AtlasEntry lookups (K_ℓ, Sobolev, …)
    │
    └── HttForwardOutput  (one per parameter point)
            │
            ├── HTT likelihood evaluators (evidence_models, directional)
            │     │
            │     └── dynesty / nested sampling → PosteriorExportBundle
            │
            └── MIO diagnostic modules consume AtlasEntry directly
                  (MIO does NOT ingest HttForwardOutput — it reads the
                  atlas independently of any model-dependent forward)
```

### A33.3.2 Cross-package boundary

| From | To | Object | Rule |
|---|---|---|---|
| bass_py | htt | `HttForwardOutput` | Model-dependent; do not treat as observational data. |
| bass_py | mio | `AtlasEntry` (not `HttForwardOutput`) | MIO consumes atlases directly to preserve model-independence. |
| htt | mio | `PosteriorExportBundle` | Cross-check only; not a likelihood input for MIO. |

## A33.4 G19 implications

`HttForwardOutput` and `AtlasEntry` are model-dependent objects, so they
are on the HTT/BASS side of the hard separation boundary. MIO MUST NOT
consume `HttForwardOutput` in non-parametric extraction routines — doing
so would contaminate the model-independence claim of `MioCertificate`.

The enforcement hook (`test_g19_mio_output_has_no_posterior_field`,
[test_g19_enforcement.py](../../bass_py/workspace/contracts/tests/test_g19_enforcement.py))
asserts that neither contract contains a field named `*posterior*`.

## A33.5 Manuscript wiring

- **ch06 §6.7 pipeline** — cites A33.1.2 / A33.2.2 when introducing the
  BASS ↔ HTT / BASS ↔ MIO data-flow diagram.
- **ch11 §11.X Hard-separation execution** — §A33.3.2 table is the
  reference boundary diagram.
- **A38 (Week 7)** — HTT ↔ MIO cross-check protocol that consumes both
  `PosteriorExportBundle` and `MioCertificate`.
