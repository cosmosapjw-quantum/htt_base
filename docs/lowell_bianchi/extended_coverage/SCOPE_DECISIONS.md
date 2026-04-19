# Scope decisions (extended bundle)

**Purpose**: append-only log of scope decisions on the extended
coverage bundle. Every entry is dated, reasoned, and references
the concrete surfaces affected. A decision recorded here is
**binding** — it can only be reversed by a new dated entry that
supersedes the previous one, with explicit cross-reference.

**Parent**: [INDEX.md](INDEX.md).
**Coordinator**: [EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md](EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md).

---

## 1. 2026-04-20 — Scope sealed to FB-8 / FB-9 / FB-11

**Decision**: The extended coverage bundle's in-scope phases are
**FB-8 (local-boost vs global-tilt discrimination)**,
**FB-9 (massive neutrino)**, and
**FB-11 (inference driver + multi-type Bayes factor)**.
All other phases previously enumerated in the draft plan are
discarded (see §§2 – 4 below).

**Rationale**: the three retained phases together close the
research-to-deployment gap that the parent plan's FB-7 exit left
open:

- FB-8 supplies the observer-frame boost parameter that
  separates local from cosmological anisotropy — without it the
  Bayes factor FB-7 produces cannot be reported on real Planck
  data because the `(β_cosmo, β_obs)` axes are conflated.
- FB-9 supplies the massive neutrino species required for any
  Planck-2018-compatible parameter reporting.
- FB-11 supplies the sampler, the `ln B` extractor, and the
  reproducibility contract that turn the likelihood stack into
  something a downstream collaborator can use.

The three retained phases share a dependency graph (FB-11
consumes FB-8 and FB-9) that fits within a single coherent
delivery, whereas the discarded phases (§§2 – 4) each represent
a distinct extension direction that can be resumed independently
later if the need arises.

**Ratified by**: user acceptance 2026-04-20.

---

## 2. 2026-04-20 — FB-10 (survey integration) discarded

**Discarded scope**: mask / beam / noise-covariance layer,
pseudo-`C_ℓ` estimator on cut sky, bridge between `bass/` and
`htt/` + `mio/` observation-side code.

**Rationale**:

- The `htt/` and `mio/` subsystems already carry the survey-side
  infrastructure for the HTT pipeline. Duplicating that surface
  inside `bass/` would violate the "single source of truth"
  discipline.
- A proper survey integration requires decisions about
  HEALPix-native vs PSTF-native mask representation, beam-
  transfer parameterisation, and noise-covariance format —
  those decisions belong with the observation-side team and
  their review cycle, not the theory stack.
- The research question FB-11 answers (multi-type Bayes factor
  at Planck-2018 precision) can be answered on synthetic
  datasets generated with idealised systematics inside
  `bass/inference`, without ever passing through a realistic
  survey pipeline. The FB-11 summary run (see
  [FB11_INFERENCE_DRIVER_SDD.md §7](FB11_INFERENCE_DRIVER_SDD.md))
  explicitly operates on synthetic data for this reason.

**Disposal**: no `bass.survey` module will be added. The FB-11
driver consumes FB-7's cosmological-frame likelihood composed
with FB-8's observer-frame adapter; realistic-survey effects
remain the `htt/` + `mio/` responsibility.

**Re-entry condition**: a dated §N entry on this document
noting the specific research question that forces a `bass/`-
side survey surface, plus a fresh SDD. Do **not** simply re-add
FB-10 rows to the coordinator plan.

---

## 3. 2026-04-20 — FB-12 (lensing / ISW non-linear) discarded

**Discarded scope**: lensing `φφ`, `Tφ` cross-spectra, lensed
`C_ℓ^{TT/TE/EE/BB}`, non-linear ISW contribution, Bianchi-
anisotropy × lensing cross-terms.

**Rationale**:

- Lensing enters the observational budget at `ℓ ≳ 200`; the
  low-ℓ Boltzmann solver at the core of this project targets
  `ℓ ≲ 32` (approximately) where lensing corrections are
  sub-percent. The research question FB-11 answers is
  dominated by `ℓ ≲ 30` — lensing does not change the sign of
  the Bayes factor for any Bianchi type at that scale.
- A proper lensing implementation requires the FB-5
  perturbation sector to be closed at high-`k` which the
  parent plan's FB-5.7 exit criteria does not enforce; adding
  lensing on top of an incompletely-converged high-`k` sector
  risks absorbing truncation error into the lensing signal.
- The CAMB fixture path retained by parent plan D8 = (a)
  covers the lensed `C_ℓ` that downstream users may need for
  cross-validation; reproducing it inside `bass/` is not
  required for the research question.

**Disposal**: no `bass.lensing` module will be added. Downstream
consumers that need lensed spectra call CAMB via its fixture
NPZ files (per the external-code policy in
[PROJECT_MEMORY_EXPLICIT.md §2](PROJECT_MEMORY_EXPLICIT.md)).

**Re-entry condition**: a Bianchi-lensing cross-term
measurement question that cannot be addressed by CAMB fixtures
alone — for example, a tilted-cosmology × lensing bispectrum
question. That would require its own SDD + a fresh dated entry
here.

---

## 4. 2026-04-20 — FB-13 (second-order tilt) discarded

**Discarded scope**: `β²` corrections beyond the linear FB-8
aberration kernel, full non-linear boost kernel on PSTF moments,
`v_e²` Doppler quadratic terms in the Thomson collision operator.

**Rationale**:

- At the Sun-CMB dipole amplitude `β_obs = 1.23e-3`, `β² ≈
  1.5e-6` — well below Planck-2018 per-ℓ noise on any quantity
  FB-11 reports. The linear aberration kernel is sufficient
  for the research question at Planck precision.
- At cosmological `β_cosmo` values consistent with Bianchi-
  type upper bounds (`β_cosmo ≲ 1e-2`), `β² ≲ 1e-4` —
  comparable to or smaller than the FB-2.4 PSTF-cache
  truncation error at `L_max = 32`. Chasing `O(β²)` while
  truncation error dominates would be a false-precision move.
- Second-order tilt is the natural first target for a
  post-extended rotation once either (a) a CMB-S4-class
  dataset lowers the noise floor enough that `β² ~ 1e-6` is
  detectable, or (b) a cosmological-tilt constraint beyond
  `β_cosmo ~ 1e-2` is driven by data rather than theory.

**Disposal**: no `order=2` kwarg will be added to
`aberration_kernel`, `accel_from_tilt`, or the Thomson
collision operator. The FB-8 / FB-3.2 / FB-4 linear surfaces
stand as the production path.

**Re-entry condition**: a measurement sensitivity beyond
Planck-2018 (e.g. LiteBIRD / CMB-S4 forecasts showing `β²`
discriminability) or a theoretical target requiring
`O(β²)` precision. A dated §N entry here plus a fresh SDD.

---

## 5. Re-entry procedure (reserved)

Any of the discarded scopes (FB-10 / FB-12 / FB-13) is re-
entered by the following procedure, never by simply re-adding
rows to the coordinator plan or the parent `FULL_BIANCHI_COVERAGE_PLAN.md`:

1. Open a new dated section `## N. YYYY-MM-DD — FB-<k> re-entry`
   on this document.
2. Document the research question that drives re-entry.
3. Author a fresh SDD `FB<k>_*_SDD.md` at the same granularity
   as the current FB-8 / FB-9 / FB-11 SDDs.
4. Update [INDEX.md](INDEX.md) read order and
   [EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md §5](EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md)
   (or its successor plan) with the re-entered phase's row.
5. Obtain explicit user acceptance before any code lands.

The purpose of this procedure is to keep scope decisions auditable
long after the session that made them.
