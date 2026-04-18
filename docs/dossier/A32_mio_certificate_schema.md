# A32 · `MioCertificate` schema

**Appendix**: A32 (§11.14.6 of `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3)
**Version**: 2026-04-19 draft (landed with DOS-A30-MIO Week 5 Day 7).
**Code anchor**: [`bass_py/workspace/contracts/mio_certificate.py`](../../bass_py/workspace/contracts/mio_certificate.py)
**Related contracts**: [`bass_py/workspace/contracts/`](../../bass_py/workspace/contracts/)
— sibling `HttForwardOutput`, `AtlasEntry`, `PosteriorExportBundle`.
**Governing rules**: v3 §4.5.2 (interface table) + §4.5.2.1 (dataclass
body) + §4.5.4 (G19 hard separation) + §10.2bis (enforcement matrix).

---

## A32.1 Purpose

`MioCertificate` is the single output object produced by every MIO
diagnostic module (`mio.extraction`, `mio.coherence`, `mio.tension`,
`mio.decomposition`, `mio.diagnostics`). Its role is **model-independent
diagnostic reporting** — NOT posterior inference, NOT truth attestation,
NOT Bayesian-evidence export.

Three hard rules apply, enforced at the class, workflow, and repository
levels (see §A32.5):

1. `MioCertificate.as_posterior_bundle()` MUST raise `NotImplementedError`
   by design. Any PR that implements it is a G19 violation.
2. HTT likelihood code MUST NOT ingest `MioCertificate` instances as
   likelihood inputs; type-checkers and runtime hooks flag this.
3. Scalar expressions that sum an `MioCertificate` score with HTT
   `lnB` / evidence are forbidden; a text-scan lint in the G19 test
   suite enforces this (see [test_g19_enforcement.py](../../bass_py/workspace/contracts/tests/test_g19_enforcement.py)).

## A32.2 Field-by-field schema

| Field | Type | Source | Purpose |
|---|---|---|---|
| `report_type` | `str` | caller | One of `'shear_extraction'`, `'directional_coherence'`, `'flrw_tension'`, `'evidence_anatomy'`, `'predictive_residuals'`, `'adequacy_certificate'`. |
| `probe_name` | `str` | caller | Which data probe contributed (`'Planck_TT'`, `'CatWISE'`, `'CF4pp'`, `'Radio'`, `'BiPoSH'`, or composite labels). |
| `channel` | `str` | caller | Analysis channel (`'low_ell'`, `'biposh'`, `'dipole'`, `'recomb_only'`, `'reion_only'`, `'full_TTTEEE'`). |
| `departure_variables` | `Dict[str, float]` | MIO module | Primary extracted quantities. Must NOT include any field whose name contains `posterior`. |
| `adequacy_indicators` | `Dict[str, bool]` | MIO module | Booleans that report whether model adequacy checks pass (e.g. `{"ell_independence_p_gt_0p05": True}`). |
| `consistency_metrics` | `Dict[str, float]` | MIO module | Numerical consistency scores (e.g. `chi2_per_dof`). |
| `domain_caveats` | `List[str]` | MIO module | Human-readable scope-of-validity notes (`'masked_sky_partial'`, `'valid_only_below_ell_30'`). |
| `channel_caveats` | `List[str]` | MIO module | Per-channel caveats. |
| `reduction_status` | `str` | MIO module | `'theory-direct'` / `'theory-approximate'` / `'diagnostic-only'` (v3 §4.5.2.1). |
| `generated_by` | `str` | MIO module | Module version string (e.g. `'mio.coherence.directional v0.1'`). |
| `git_commit` | `str` | provenance | Commit hash at generation time. |
| `config_hash` | `str` | provenance | Hash of the config dict supplied at generation time. |
| `input_data_hashes` | `List[str]` | provenance | Hashes of consumed datasets. |
| `htt_cross_check_suggested` | `Optional[Dict[str, str]]` | MIO module | Optional hint to HTT on which posterior is the natural cross-check target. NOT a likelihood input. |

## A32.3 Canonical instance examples

### A32.3.1 `mio.coherence.directional` (HJ-02a, Week 6)

```python
MioCertificate(
    report_type="directional_coherence",
    probe_name="5probe_bundle",
    channel="dipole",
    departure_variables={
        "resultant_R": 0.913,
        "l_deg_best": 261.2,
        "b_deg_best": 44.8,
    },
    adequacy_indicators={
        "isotropy_p_lt_0p01": True,
        "all_probes_within_20deg_cone": False,
    },
    consistency_metrics={
        "chi2_per_dof": 1.02,
        "pairwise_max_sep_deg": 27.4,
    },
    domain_caveats=[
        "masked_sky_partial",
        "valid_only_for_dipole_resolved_probes",
    ],
    channel_caveats=["BiPoSH preliminary — awaiting W11-02"],
    reduction_status="theory-direct",
    generated_by="mio.coherence.directional v0.1",
    git_commit="<w6-commit>",
    config_hash="<cfg>",
    input_data_hashes=["<planck>", "<catwise>", "<radio>", "<cf4pp>", "<biposh>"],
    htt_cross_check_suggested={
        "compare_to": "htt.evidence_models.BianchiI_tilt.axis_posterior",
        "expected_relation": "axis within 2σ of MIO best direction",
    },
)
```

### A32.3.2 `mio.tension.flrw_tension` (HJ-03, bass_py dep)

```python
MioCertificate(
    report_type="flrw_tension",
    probe_name="Planck_TT",
    channel="low_ell",
    departure_variables={"x_C": 0.41, "x_C_sigma": 0.08},
    adequacy_indicators={"ppp_p_lt_0p05": True},
    consistency_metrics={"look_elsewhere_corrected_p": 0.12},
    domain_caveats=["requires bass W10-02 K_ℓ atlas"],
    channel_caveats=[],
    reduction_status="theory-approximate",
    generated_by="mio.tension.flrw_tension v0.1",
    git_commit="<hj03-commit>",
    config_hash="<cfg>",
    input_data_hashes=["<planck>", "<k_ell_atlas>"],
)
```

## A32.4 Provenance requirements

Every `MioCertificate` instance MUST carry all four provenance fields
populated at generation time (`generated_by`, `git_commit`, `config_hash`,
`input_data_hashes`). The MIO generator API (`mio.interface.mio_certificate.
build_mio_certificate`, Week 6) auto-populates `git_commit` from
`bass_py.runtime.provenance`; `config_hash` is a SHA-256 of the config
dict passed to the module; `input_data_hashes` is the list of
content-hashes of each input data file.

## A32.5 G19 enforcement mechanisms

| Layer | Mechanism | Location |
|---|---|---|
| Class | `as_posterior_bundle()` raises `NotImplementedError` | [mio_certificate.py](../../bass_py/workspace/contracts/mio_certificate.py) |
| Class | Schema hash anti-regression (test fails if a new field is added silently) | [test_mio_certificate.py](../../bass_py/workspace/contracts/tests/test_mio_certificate.py) |
| Class | `'posterior'` token forbidden in any field name | [test_g19_enforcement.py](../../bass_py/workspace/contracts/tests/test_g19_enforcement.py) |
| Runtime | HTT likelihoods reject `MioCertificate` inputs (TypeError) | [test_g19_enforcement.py](../../bass_py/workspace/contracts/tests/test_g19_enforcement.py) |
| Static | `bass_py/**.py` text-scan lint for MioCertificate-plus-HTT scalar-sum | [test_g19_enforcement.py](../../bass_py/workspace/contracts/tests/test_g19_enforcement.py) |

## A32.6 Manuscript wiring

- **ch11 §11.X "`MioCertificate` semantic rule"** — must reference this
  appendix; must say "truth certificate" ≥ 4 times (v3 §15.2 qualitative
  gate); must include a box with the three G19 rules above verbatim.
- **ch12 §12.0 MIO philosophy** — prose summary of purpose; cites A32.1.
- **ch12 §12.7 scope limits** — explicit restatement of §A32.1 hard rules.

## A32.7 Open items (post-Week 5)

- **Week 6 MIO-HJ-06a**: `bass_py/mio/interface/mio_certificate.py` builder
  that wraps the frozen dataclass with validation + provenance autofill.
- **Week 7 CONTRACTS-02**: `docs/design/G19_cross_check_protocol.md`
  specifies the HTT↔MIO cross-check protocol that consumes a
  `MioCertificate` plus a `PosteriorExportBundle`.
- **Schema evolution policy**: any new field requires (a) an audit
  record; (b) updated `test_miocertificate_schema_frozen`; (c) a
  manuscript paragraph justifying the addition.
