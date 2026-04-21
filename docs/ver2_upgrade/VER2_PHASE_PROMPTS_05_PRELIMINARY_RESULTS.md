# VER2 Prompt List 05

## Preliminary Results Mode

**Status**: post-BASS-first operating mode  
**Authority**: `docs/ver2_upgrade/*` + `docs/manuscript/*`  
**Purpose**: keep `htt/bass/*` scientifically useful as a low-`\ell` preliminary Boltzmann solver that can feed HTT/MIO/TSC and the plotting/export scripts, without reopening every remaining exactness debt before preliminary results are produced, while preserving the all-11-type 1+3 PSTF/tetrad architecture as the solver backbone.

## 0. Why this mode exists

The manuscript does not ask BASS to become a universal exact solver before any
result is useful. Reading the current text gives a narrower research target:

1. quantify departure from FLRW under a typed, assumption-explicit low-`\ell`
   anisotropy pipeline;
2. test whether the matter-dipole anomaly is at least tilt-compatible;
3. keep geometry claims blocked until direction-dependent observables and
   stronger identifiability arrive;
4. produce forward outputs that HTT, MIO, TSC, and the manuscript/export layer
   can consume consistently.

The relevant manuscript claims are:

- `docs/manuscript/ch01_introduction.tex`
  - the project asks “how large is the departure from FLRW, and what does it
    constrain?”
  - the current evidence focus is tilt-compatible anomaly support, not a clean
    geometry identification.
- `docs/manuscript/ch06_pipeline.tex`
  - BASS owns forward physics and low-order Boltzmann outputs;
  - HTT owns evidence/posteriors/figures;
  - MIO owns certification / status classification.
- `docs/manuscript/ch07_results.tex`
  - the current results chapter is built around likelihood architecture,
    evidence, and bounded model comparison.
- `docs/manuscript/ch09_discussion.tex`
  - the central dichotomy is CMB-vs-matter and tilt-vs-geometry attribution,
    not immediate proof of anisotropic spatial geometry.

So the next development mode is not “maximize exactness at any cost.” It is:

> make BASS reliable enough to generate scientifically meaningful preliminary
> low-`\ell` results, pass them to HTT/MIO/TSC cleanly, and keep the residual
> caveats explicit.

This mode does **not** redefine the architectural target. The solver domain
remains:

1. all eleven Bianchi types;
2. both orthogonal and tilted matter branches for each type;
3. nonperturbative time-dependent homogeneous background evolution;
4. perturbative spatial/temporal fluctuation transport on top of that
   background;
5. explicit distinction between global tilt geometry/matter-frame effects and
   local observer boost / peculiar-velocity artifacts.

## 1. Operating rules

1. `docs/ver2_upgrade/*` remains the semantic SSOT.
2. Keep BASS observer-neutral. HTT still owns posterior/evidence interpretation.
3. Do not reopen already-closed exactness debts unless they block preliminary
   results or downstream integration directly.
4. Prefer representative family coverage over premature exact closure of every
   remaining family.
5. Treat `Type I`, `V`, `VII_0`, and `VIII` as the first preliminary-results
   family set unless a later step proves one of them non-viable.
6. Validation is intentionally lighter in this mode:
   - required: CoVe / metacognitive audit, equation-to-code mapping against
     `lowell_bianchi_solver_SDD_PR_WBS_pstf_tetrad.md`, touched-surface tests,
     exporter/script checks when touched;
   - optional by default: plot-reading adversarial loop;
   - mandatory plots only when the step explicitly changes figure-generation or
     when a numerical mismatch cannot be resolved from code/test evidence alone.
7. Preliminary-results mode may use bounded approximations that already exist in
   SSOT, but must never silently relabel them as exact or validated geometry
   claims.
8. The target artifact is not “perfect science closure.” The target artifact is
   “conditional, caveated, script-runnable preliminary result packs.”
9. The representative family sweep is a staging order only. It must never be
   misread as narrowing the solver architecture away from the full eleven-type
   registry with orthogonal/tilted branches.
10. Preserve the 1+3 gauge-invariant covariant PSTF objects as the semantic
    source of truth. Tetrad components are the code representation of those
    objects, not a replacement formalism.
11. Keep global tilt and local boost distinct:
    - global tilt belongs to the model/background/matter-frame state;
    - local boost belongs to observer or peculiar-velocity artifact handling;
    - neither may be silently folded into the other for convenience.
12. Prefer algebra substitution over handwritten family rewrites: when a new
    Bianchi family is enabled, the default path should be to swap the
    tetrad/commutator algebra backend and retain the common PSTF transport
    machinery unless the SDD explicitly requires a family-specific operator.
13. Constraint handling must continue to descend from the SDD identity path
    (Jacobi, Ricci, Codazzi, Gauss, Bianchi identities) or from an explicit
    SDD-approved closure. Ad hoc runtime constraints are not a substitute.

## 2. Success criteria for BASS in this mode

BASS is “good enough for preliminary results” when all of the following hold:

1. `execute_tier_b_solver(...)` runs reproducibly for the representative family
   set on bounded low-`\ell` configurations.
2. The common solver contracts continue to expose the full eleven-type /
   orthogonal-vs-tilted architecture even if only a representative subset is
   exercised in the current sweep.
3. The runtime/forward/observable path keeps global tilt and local boost
   metadata distinct enough for HTT/MIO/TSC to avoid semantic drift.
4. `SolverCoreOutput -> ObservableVector -> HTT/MIO/TSC adapters` stays live.
5. `scripts/ver2_artifact_export.py` and the relevant paper/gallery plotters run
   without requiring manual data patching.
6. The generated artifacts carry the right caveats:
   - tilt-compatible preliminary result: allowed;
   - exact geometry identification: blocked unless separately validated.
7. Manuscript-facing conditional claims can be generated from current artifacts
   without hand-editing science numbers.

## 3. Packet table

| Packet | Goal | Depends on | Lane | Commit prefix |
|---|---|---|---|---|
| `PRM-01-BASS-INTEROP` | stabilize BASS output contracts for HTT/MIO/TSC/exporter consumers | closed VER2 packets + `V2-B12` | `B` | `V2-P1:` |
| `PRM-02-BASS-FAMILY-SWEEP` | run bounded representative-family low-`\ell` solver sweeps and close obvious family blockers | `PRM-01-BASS-INTEROP` | `B` | `V2-P2:` |
| `PRM-03-PRELIM-RESULT-PACKS` | refresh manifest-backed preliminary result packs and plotting/export scripts from current BASS outputs | `PRM-02-BASS-FAMILY-SWEEP` | `B/D` | `V2-P3:` |
| `PRM-04-HTT-MIO-HANDOFF` | make HTT/MIO/TSC consume the preliminary result packs without manual glue | `PRM-03-PRELIM-RESULT-PACKS` | `H/M/T` | `V2-P4:` |
| `PRM-05-TARGETED-PHYSICS` | only then reopen deeper exactness work that blocks a concrete preliminary claim | `PRM-04-HTT-MIO-HANDOFF` | `B` | `V2-P5:` |

## 4. Packet intent

### `PRM-01-BASS-INTEROP`

**Write scope**

- `htt/bass/forward/*`
- `htt/bass/observational/*`
- `htt/bass/observer/*`
- `htt/bass/likelihood/*`
- `htt/bass/inference/*`
- selected `htt/workspace/contracts/*`
- selected `htt/scripts/*`
- related tests

**Intent**

Stabilize the current BASS output path so external modules do not need special
cases. This is not new physics; it is contract cleanup for preliminary results.

**Required closure**

- `SolverCoreOutput` and `ObservableVector` remain machine-readable and
  sufficiently populated for HTT/MIO/TSC.
- no production-root export points at surrogate-only helpers by accident.
- exporter and downstream adapters can read the current BASS artifacts directly.

### `PRM-02-BASS-FAMILY-SWEEP`

**Write scope**

- `htt/bass/runtime/*`
- `htt/bass/los/*`
- `htt/bass/validation/*`
- selected `htt/bass/forward/*`
- related tests

**Intent**

Close the most obvious family blockers for a representative preliminary sweep.
This packet is about making a useful family subset run end-to-end, not about
closing every exact propagator debt.

The subset is a sequencing choice, not a semantic downgrade of the solver
domain. The algebra registry, branch metadata, and tetrad/PSTF contracts remain
all-11-type and orthogonal-vs-tilted throughout.

**Representative target set**

- `Type I`
- `Type V`
- `Type VII_0`
- `Type VIII`

**Required closure**

- each target family has a bounded runnable path;
- each target family records honest propagator / covariance / claim metadata;
- validation is sufficient for conditional preliminary result production.

### `PRM-03-PRELIM-RESULT-PACKS`

**Write scope**

- `scripts/ver2_artifact_export.py`
- selected `scripts/make_*figures.py`
- generated result-pack docs under `docs/ver2_upgrade/generated/*`
- related tests

**Intent**

Turn the representative family sweep into manuscript/export-ready preliminary
artifacts. The priority is runnable scripts and consistent caveats, not maximal
statistical sophistication.

**Required closure**

- exporter runs from current artifacts;
- paper/gallery plotting scripts run on the current BASS outputs;
- generated result packs reflect the conditional/preliminary claim ceiling.

### `PRM-04-HTT-MIO-HANDOFF`

**Write scope**

- `htt/htt/*`
- `htt/mio/*`
- `htt/tsc/*`
- selected `htt/workspace/contracts/*`
- related tests

**Intent**

Ensure the external modules consume preliminary BASS artifacts without local
ad hoc glue or manual JSON surgery.

### `PRM-05-TARGETED-PHYSICS`

**Intent**

Only after preliminary result production is stable should we reopen deeper
exactness tasks. Candidate examples:

- non-Type-I exact propagator closure when it blocks a family in the
  representative sweep;
- direction-resolved reionization microphysics when it blocks a concrete
  manuscript-facing observable;
- stronger morphology/covariance closure when HTT/MIO claims need it.

## 5. Verification policy in this mode

### Required every step

1. CoVe-style self-check on the touched claim.
2. Metacognitive audit:
   - what exactly changed,
   - what it still does not justify,
   - what downstream module could misread it.
3. Equation-to-code check against the SDD for touched equations/quantities.
4. Touched-surface tests.
5. Script `--check` or exporter run when the step touches plotting/export.

### Optional by default

- plot generation and visual audit
- wide adversarial mutation sweeps
- full hostile-audit reruns outside the touched scope

These become required only when:

- a touched script/figure breaks,
- a numerical mismatch remains unexplained,
- or a new manuscript-facing observable is being promoted.

## 6. Immediate next action

The recommended next packet in this mode is:

1. `PRM-01-BASS-INTEROP`

That is the cheapest DAG-correct step because it improves the current BASS
artifact usability for HTT/MIO/TSC and the plotting/export scripts without
reopening the hardest remaining physics debt first.

The hard design axioms for every packet in this mode are:

1. all eleven Bianchi types remain the architectural target;
2. orthogonal and tilted branches remain explicit, not implicit;
3. global tilt and local boost remain distinct contracts;
4. 1+3 PSTF semantics remain the equation-level authority;
5. tetrad algebra substitution remains the preferred family-extension path.
