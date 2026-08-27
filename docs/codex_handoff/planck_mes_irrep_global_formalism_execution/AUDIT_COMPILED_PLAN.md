# Planck MES Irrep/Global-Formalism Audit-Compiled Execution Plan

## A. Authority and Scope

Canonical scientific authority is `changeset/pr324-mes-methodology-stack-20260826@3cdeaba39e164c911a26c5daa37f0e15b29614d3` with tree
`47bdbb72aae62ca4280a96897f80028b1b910c20`. The current planning predecessor is
`analysis/planck-mes-extended-data-execution-20260826@2669a55ef230d1ca9e79c09d3344f7b15c50ac0e` with tree
`274d74507542cc99bb4ea355705791fa03d15697`, represented by draft PR #417.

This package supersedes the predecessor package **only for execution order**.
The predecessor data inventory, route evidence, and historical threat analysis
remain durable evidence. `PED-WU-001..004` must not be executed directly after
the active pointer selects this package.

The scientific goal is not to attach more scalar labels to the existing Planck
rank. It is to preserve and analyze the observer-space low-ell irreducible
carrier while keeping four different semantic layers separate:

```text
ObservableIrrepState
    != JointAnisotropyState
    != MesPremiseNormalizer
    != ResponseBoundObservableState
```

The frozen scalar Planck result remains a compatibility baseline:

```yaml
GENERIC_12: 133/301
RAW_REDUCED_10: 110/301
EPS_REDUCED_10: 109/301
MES_10: 98/301
ANCHORS_ONLY_2: 78/301
MORPHOLOGY_ONLY_8: 88/301
minimum_coordinate: multipole_l3_absdot_0
minimum_coordinate_rank: 16/301
MES_ceiling_local_ranks: [74/301, 74/301]
```

Non-goals are physical shear/vorticity measurement, Planck-only
local/global identification, Bianchi-family inference, likelihood fitting,
and unrelated repository refactoring.

## B. P0/P1 Threat Catalogue

The machine catalogue contains 25 failure classes:
11 P0 and
14 P1. Every row has one
primary executable detector or fail-closed gate.

The load-bearing classes are:

1. observable/physical state conflation;
2. scalar-to-vector/STF fabrication;
3. mutation of the frozen scalar baseline;
4. carrier layout/frame/unit/order drift;
5. observation/null operator mismatch;
6. raw input mutation;
7. null-role substitution or Commander pseudo-calibration;
8. physical-template labels without response provenance;
9. false independent-information claims for MES coordinates;
10. post-hoc reducer/tail/template selection;
11. reuse of the physical orbit catalogue on observer-space irreps;
12. a new map pass that discards retained harmonic carriers.

See `P0_P1_THREAT_CATALOG.json`.

## C. Invariant/Test Matrix

`INVARIANT_TEST_MATRIX.yaml` maps each requirement to one invariant, failure
mode, mechanical detector, work unit, and positive pass transition. No prose
warning is the sole control for a P0/P1 class.

The highest-value exact identities are

\[
W^2_{\max}=\frac{C_2}{30\pi T_0^2},
\qquad
\Sigma^2_{\max}=\frac{27}{98}(7\epsilon_2+\epsilon_3)^2,
\]

with inverse map on the registered nonnegative domain

\[
\epsilon_2=\sqrt{\frac{75}{2}W^2_{\max}},
\qquad
\epsilon_3=\sqrt{\frac{98}{27}\Sigma^2_{\max}}-7\epsilon_2.
\]

Therefore

\[
\sigma(\Sigma^2_{\max},W^2_{\max},M)
=
\sigma(C_2,C_3,M)
\]

for the registered branch, and the typed report must carry
`independent_information_gain=false`.

## D. Ordered Work Units

```text
PMG-WU-001  freeze scalar baseline; create ObservableIrrepState
PMG-WU-002  apply typed adapters and layer firewalls across relevant code
PMG-WU-003  execute map-free coordinate/reducer mechanism audit
PMG-WU-004  verify local Planck/FFP10 inventory read-only
PMG-WU-005  execute paired-300 carrier-preserving map pass
PMG-WU-006  calibrate ell=2/3 observable irrep-orbit morphology
PMG-WU-007  execute carrier-preserving 999 and Commander lanes
PMG-WU-008  execute harmonic and conditionally physical injection power
PMG-WU-009  rebuild the paper as a methods-first irrep-aware analysis
```

The first two units are bounded enabling work. `PMG-WU-003` is a mandatory
real objective transition; another planning package before it is a process
failure.

Each work unit in `AUDIT_COMPILED_EXEC_PLAN.yaml` is an
`audit-compiled-work-unit/v1` contract with exact paths, preconditions,
invariants, implementation steps, verification commands, evidence, and
`PASS -> next executable action`.

## E. Fresh-Context Review Contract

The first independent review pass is read-only and sees only the authoritative
base, candidate SHA, diff, compiled work-unit contract, verification logs,
objective artifacts, and unresolved blockers. It must report reproducible
P0-P3 findings using the schema in `FRESH_CONTEXT_REVIEW_CONTRACT.yaml`.

Pass requires `P0=0, P1=0`. There is one review and at most one targeted
repair unless a new current-task P0/P1 is independently reproduced.

## F. Final Differential Audit Contract

The final strong-model audit examines the compiled contract against the actual
predecessor-to-final delta and evidence. It does not restart the historical
project review. It asks whether:

- implementation violated the contract;
- the contract missed a new P0/P1 visible in the delta;
- evidence was invalid or misclassified;
- scope expanded;
- a reviewer gave a false PASS/FAIL;
- real mechanism, map, irrep, and power execution occurred.

## G. Unresolved Specification Boundaries

No boundary blocks `PMG-WU-001..007`.

The physical-template part of `PMG-WU-008` remains conditional on a
content-bound template artifact carrying solver commit/tree, frame, units,
epoch, transfer, family, and tilt/boost semantics. If absent, that candidate
is `DEFERRED_NOT_ATTEMPTED`, not refuted and not a blocker for the algebraic
method-power lane or methods paper.

Publication venue, author list, and final title remain editorial decisions
after the scientific execution.

## H. Process-Cost Assessment

Reused rather than regenerated:

- frozen scalar packages and exact ranks;
- the current joint cut-sky operator;
- MES coefficient authority;
- physical `JointAnisotropyState` and `orbit_catalogue_v3` contracts;
- predecessor inventory evidence as a planning input.

Justified expensive work is limited to one paired-300 carrier reconstruction,
one 999 carrier-preserving pass, one Commander descriptive pass, and bounded
map-free injection trials.

Not justified:

- another planning package;
- review-of-review;
- a full raw-tree hash sweep;
- full repository tests after each local unit;
- unrelated architecture cleanup;
- rereading maps to change packaging metadata.

Two substantial process-only cycles trigger `PROCESS_STARVATION`; the response
is execution, not another remediation document.
