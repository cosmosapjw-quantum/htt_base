# Observation-independent theory-promotion audit v1

Date: 2026-08-24

Exact audit base: `aaa87d6de692f5c47d5ea9eff963db6dd9ee5be7`

Exact base tree: `5901e12457e4ae677f0b74c0c8fdd8257987f084`

Acceptance hash: `147d242632311f5e96ac23d1e3d2b0921770f150af1178c1f599447eff4f9f8d`

## Decision

This audit finds substantial observation-independent mathematical content, but
it does **not** promote a new claim at the current repository head. The terminal
decision is:

```text
STOP_INVALID_FOR_CURRENT_PROMOTION
```

The stop is not a statement that the historical mathematics is false. It
separates three facts:

1. frozen historical four-axis CAS adjudications exist for exact restricted
   statements;
2. the later PR-285/PR-286 adjudications expose scoped PASS, FAIL, BLOCKED, and
   INCONCLUSIVE rows that are absent from the older PR-275 report surface; and
3. the present exact-head replay has stale bindings and a new PR-284 CAS
   conflict, so a current publication claim cannot honestly be sealed yet.

No observed payload was opened. No observed statistic, native transfer result,
geometry detection, or Bianchi-family identification enters this report.

The complete 152-row reconciliation is
`THEORY_PROMOTION_MATRIX_V1.json`. The same matrix seals a 157-candidate
scientific universe: the 152 broad adjudication rows plus five independently
reportable scoped candidates. These are evidence dispositions and scoped
candidates, not unique-theorem counts.

## Mechanical coverage

The audit froze and searched the following surfaces before interpreting any
claim:

| Surface | Frozen coverage |
|---|---:|
| Canonical strict DAG | 259 valid PR cards |
| PR delta files | 228 |
| Revision delta files | 91 |
| GitHub PR objects, frozen through PR #403 | 402 |
| Local refs at freeze | 129 |
| All-ref commit subjects | 1,530 |
| Legacy theorem-registry rows | 65 |
| Two-pillar registry rows | 58 |
| PR-285 Pillar-T adjudication rows | 80 |
| PR-286 Pillar-S adjudication rows | 72 |

PR #404 appeared after the frozen inventory and is deliberately excluded. New
activity did not expand the acceptance set. The search covered DAG cards,
existing PR and revision deltas, all-ref history, theorem/signature registries,
proof registries, CAS contracts/adjudications, formal sources, and GitHub PR
metadata. A theorem-like name or a completed PR was never treated as proof.

## Scientific-candidate terminal taxonomy

Every candidate in the sealed universe now has exactly one of five terminal
states:

- `PROMOTED`: its exact registered proof or experiment passed at the declared
  scientific scope;
- `REFUTED`: an actual attempted proof or experiment produced an explicit
  counterexample or failure;
- `UNRESOLVED`: a real attempt was made, but it did not settle the candidate;
- `DEFERRED`: the candidate is postponed for an explicit recorded dependency,
  capability, data, or scope reason;
- `NOT_ATTEMPTED`: the candidate was proposed, but no real proof or experiment
  addressing it was run.

The governing non-equivalence is:

```text
NOT_ATTEMPTED != REFUTED
```

An unavailable source, a missing data or solver capability, a stale replay, or
the absence of a proof is not a refutation. The only `REFUTED` broad candidate
in this audit is the PR-190 attainability claim, for which exact same-frame
counterexamples are recorded. In particular, the two restricted J1/J2 rows
remain `UNRESOLVED`: their adjudication was attempted, but the exact source
statements were unavailable and the counterexamples were not independently
replayed in that cell.

The current terminal counts are:

| Terminal state | Candidates |
|---|---:|
| `PROMOTED` | 36 |
| `REFUTED` | 1 |
| `UNRESOLVED` | 107 |
| `DEFERRED` | 2 |
| `NOT_ATTEMPTED` | 11 |
| **Total** | **157** |

The 36 `PROMOTED` candidates comprise the 32 broad PASS rows and four scoped
results inside broader non-PASS rows: the `VT-T8` local chart, the `VT-T13`
chain rule, the PR-190 normal-vorticity obstruction, and the `VT-S14`
synthetic positive cell. `PROMOTED` here is scientific and scope-local. It does
not override the separate current-head publication gate, which remains
`STOP_INVALID_FOR_CURRENT_PROMOTION` where replay or release bindings are not
closed.

The finite PR-284 path is `UNRESOLVED`, not `REFUTED`: the four-axis attempt was
real, but its aggregate is `CAS_CONFLICT`. The eleven proposals listed in the
priority proof backlog are `NOT_ATTEMPTED`, not failed theorems.

The matrix contains a machine-checkable coverage proof over the ordered
candidate universe, sealed as
`8e83989a568cefabfdf3a887ed0c1588ad91f44c83dec5a4ec167561e83bf8bc`.
It reports zero missing states, zero unknown states, zero duplicate candidate
identities, and zero `NOT_ATTEMPTED`/`REFUTED` overlap.

The campaign sentence `No scientific result survived.` is **not eligible**.
Its gate is:

```text
coverage_complete
and PROMOTED_count == 0
and NOT_ATTEMPTED_count == 0
and every state is in {REFUTED, UNRESOLVED, DEFERRED}
```

Coverage completeness alone is necessary but insufficient. This campaign has
36 scoped promoted results and 11 unattempted proposals. More generally, a
campaign closeout may only claim that every candidate was consumed after the
complete universe lies in
`PROMOTED | REFUTED | UNRESOLVED | DEFERRED`; it cannot silently count
`NOT_ATTEMPTED` as failure.

## What had been missed or suppressed

### 1. Thirty-two current PASS rows are absent from the historical report

PR-285 has 11 PASS rows and PR-286 has 21 PASS rows. The frozen PR-275 proof
atlas still says that all 123 source obligations and all 28 successor
obligations are `NOT_ADJUDICATED`. That is a stale presentation layer, not a
reason to rewrite PR-275 history.

The 32 rows split into:

- 24 exact or premise-conditional mathematical rows;
- 8 preregistered synthetic statistical validation rows.

They are not 32 unique theorems. At minimum, `I-2.2` overlaps `VT-T6`, and
`I-2.3` overlaps `VT-T7`. The matrix records eight explicit semantic link
groups so that equivalent or narrower statements are not counted twice.

### 2. Two broad INCONCLUSIVE rows contain exact narrower cores

`VT-T8` remains `INCONCLUSIVE_WITH_RECEIPT`, because a local Jacobian does not
prove global orbit separation or invariant-ring completeness. Its established
core is nevertheless a valid restricted result:

> On the registered principal cyclic eigenframe slice, the fourteen declared
> coordinates have a nonzero exact Jacobian at the registered rational witness
> and hence are local coordinates there.

`VT-T13` also remains `INCONCLUSIVE_WITH_RECEIPT`, because no typed full
covariant evolution law binds the requested electric/magnetic Weyl, stress,
acceleration, and vorticity decomposition. Its exact surviving core is:

\[
\dot I_2=2\operatorname{tr}(\sigma\dot\sigma),\qquad
\dot I_3=3\operatorname{tr}(\sigma^2\dot\sigma),
\]

together with the registered quotient chain rule for
\(J_\sigma=\sqrt{6}I_3/I_2^{3/2}\) when \(I_2>0\).

These cores can be written as propositions in an independent mathematical
note only if their broader source rows remain visibly inconclusive.

### 3. The PR-190 FAIL contains an exact negative theorem

The broad claim that every registered comparator value is attained by an
admissible same-frame Einstein-matter solution is correctly `FAIL`. The reason
is itself a reportable observation-independent result.

For a homogeneous Bianchi-I chart adapted to a hypersurface-normal congruence,
Frobenius gives

\[
D_{[i}n_{j]}=0,\qquad \omega_i=0,\qquad
W^2=3\sum_i(\omega_i/\Theta)^2=0.
\]

The registered lower and interior witnesses instead require respectively
\(W^2=1/25\) and \(W^2=3/100\) in the same frame. They therefore cannot be
hypersurface-normal constraint witnesses. This is a negative obstruction, not
a rescued attainability theorem and not a statement about all tilted frames.

The frozen PR-190 contract has a historical `CAS_4AXIS_PASS`. The current
replay reproduced the exact values in SymPy, Sage/Singular, and Lean; Wolfram
could not run because the installed engine is not activated. The frozen
historical result remains historical evidence, while the current replay is
explicitly incomplete.

### 4. Two exact restrictions were registered but not adjudicated as source rows

The two-pillar registry preserves counterexamples to the strong J1 and J2
claims:

- unequal anchors refute the strong J1 assertion while a one-way containment
  survives;
- identical marginals can have different exceedance probabilities, refuting a
  J2 claim without a joint numerator-anchor law.

PR-286 could not adjudicate `I-5.5` or `II-4.5` because the source statement was
unavailable in its input. These are high-value negative-result replay targets,
not presently promoted rows.

### 5. A useful synthetic result remains inside a blocked row

`VT-S14` has a passing registered synthetic local/global discrimination cell,
including an identified positive cell and a killed proportional-design
negative control. Its broad row correctly remains `BLOCKED_WITH_RECEIPT`
because admitted data are absent. The synthetic result may be reported as a
method validation, never as observational evidence or family identification.

## New proof attempt: the PR-284 finite registered path

A shared four-axis contract was created for exactly one finite four-atom
fixture. With equal weights, target

\[
X=(-3,-1,1,3),
\]

and the fine, two-block, and one-block partitions, direct conditional
expectation gives

\[
M_0=(-3,-1,1,3),\quad M_1=(-2,-2,2,2),\quad M_2=(0,0,0,0).
\]

Also

\[
E[X]=0,\qquad E[X^2]=5.
\]

For \(\lambda=6/5\), the inclusive event is attained by atoms zero and three,
so

\[
\Pr\!\left(\max_j |M_j|^2\geq \lambda^2 E[X^2]\right)=\frac12
\leq \frac{25}{36}=\frac1{\lambda^2},
\]

with exact slack \(7/36\).

The engine results are:

| Axis | Current result |
|---|---|
| SymPy 1.14.0 | PASS, all ten exact obligations |
| SageMath 10.9 + Singular 4.3.2 | PASS, all ten exact obligations |
| Lean 4.31.0 + Mathlib | Exact fixture compiles, but INCONCLUSIVE against the literal contract because `#print axioms` reports `propext`, `Classical.choice`, and `Quot.sound` |
| Wolfram + xAct | `BLOCKED_PLATFORM_OR_LICENSE`; the program did not execute |

The aggregate is `CAS_CONFLICT`, and
`claim_promotion_cas_eligible=false`. The exact arithmetic is useful evidence,
but the repository's R3 four-axis rule forbids majority promotion. The broad
`II-3.2` reverse-martingale statement remains inconclusive. This proof attempt
does not assert convergence, optional stopping, an if-and-only-if theorem,
continuum paths, or observed-sky calibration.

The Lean finding is not repaired by silently redefining “without axioms.” A
minimal `decide` experiment failed to reduce the rational equality and was
removed. A future contract may explicitly distinguish source-declared axioms
from Mathlib's standard logical axioms, but that would be a new preregistered
contract, not a post-hoc pass for this one.

## Historical proof replay

| Package | Frozen status | Current replay | Current use |
|---|---|---|---|
| PR-190 normal-vorticity obstruction | `CAS_4AXIS_PASS` | SymPy/Sage/Lean PASS; Wolfram blocked | exact negative theorem candidate after current evidence rebinding |
| PR-270 vector/tensor algebra | `CAS_4AXIS_PASS` | SymPy/Sage/Lean PASS; Wolfram blocked | exact restricted algebraic cores; no global orbit or dynamics promotion |
| PR-284 finite path | none before this audit | SymPy/Sage PASS; Lean contract mismatch; Wolfram blocked | theorem candidate only; aggregate `CAS_CONFLICT` |

A missing current Wolfram engine does not erase a frozen historical
adjudication. Conversely, a frozen adjudication is not misreported as a fresh
four-axis replay.

## Historical claims that remain unsafe

The audit found five substantive places where implementation or prose exceeds
the proved physical content:

1. **PR-216 constraint attainment.** Replacing spatial gradients by zero does
   not derive the complete homogeneous Bianchi-frame Gauss/momentum
   constraints; connection, structure-constant, curl/vorticity, and momentum
   flux terms require an explicit branch derivation. A future transfer solver
   also does not prove global Einstein-matter development.
2. **PR-223 moment cone.** The exact antipodal two-stream example is valid, but
   random antipodal samples, including unvalidated negative weights, do not
   characterize the physical moment cone. A viable next theorem is the
   positive-semidefinite condition and constructive antipodal
   eigendecomposition at zero first moment.
3. **PR-197 exchangeable ranks.** At \(\alpha=0.05\), the advertised exhaustive
   checks through twelve calibration representatives are vacuous because the
   smallest p-value is at least \(1/13\). Arbitrary exchangeable tie blocks were
   not exhaustively proved.
4. **PR-210 frame bridge.** The current bridge copies scalar components and
   changes a frame label; it is not a derived matter-frame to normal-frame
   transformation and accepts an empty validity domain.
5. **PR-222 CF4 bridge.** Exact rank and GLS facts for one hard-coded rational
   matrix are valid conditional linear algebra. They do not bind that matrix to
   a physical CF4 window, transfer, covariance, gauge, frame, or units.

These findings do not require generic security or provenance machinery. They
require physics derivations, typed domains, exact assumptions, and direct
counterexamples or tests.

## Current exact-head replay blockers

Only affected historical contract slices were run; no full repository suite
was used.

- The theorem/vector-tensor contract slice produced 48 passes and 8 failures.
  The theorem rows regenerate, but metadata hashes and the PR-275 binding to
  the PR-273 diagnostic pack are stale.
- The PR-191--258 bounded slice produced 357 passes and 4 failures. The failures
  expose an active MES namespace source mismatch, an obsolete PR-253 overlay
  expectation, and one PR-256 near-zero singular value recorded as `0.0` versus
  `1.2100106776761e-13`. The PR-256 rank decision is unchanged, but exact replay
  is not closed.

These are current promotion blockers, not permission to weaken exactness or
overwrite historical receipts.

## Promotion strategy

The smallest scientifically useful publication programme is three notes, not
one omnibus theorem ledger.

### Note A — exact invariant and quotient geometry

Candidate content:

- the eight frozen `PROVEN_CAS4` algebraic/gauge rows;
- the exact `VT-T5`--`VT-T7` cores after deduplication;
- the restricted `VT-T8` local-chart proposition;
- the restricted `VT-T13` chain-rule proposition.

Required closure: repair exact-head input bindings, regenerate a downstream
current-adjudication overlay, replay the affected contracts, deduplicate exact
statements, and obtain external mathematical review. Global orbit separation,
full invariant-ring generation, constraint realizability, full covariant
dynamics, and family identification remain excluded.

### Note B — exact no-go and counterexample results

Candidate content:

- the PR-190 same-frame normal-vorticity obstruction;
- the registered J1 and J2 counterexamples after direct replay;
- explicit boundaries showing which weaker statements survive.

Negative results should be first-class results. The note must preserve the
broad PR-190 `FAIL` and must not describe a refutation as a repaired positive
claim.

### Note C — finite statistical identities and synthetic method validation

Candidate content:

- exact data-processing, gauge-refusal, monotonicity, sample-wise pushforward,
  and paired-covariance identities from `VT-S1`, `VT-S2`, `VT-S4`, `VT-S7`, and
  `VT-S8`;
- the eight synthetic PASS rows in a separate validation section;
- the PR-284 finite fixture only after a clean shared four-axis contract passes.

This note must distinguish an exact theorem, a premise-conditional theorem, and
a finite synthetic experiment. No synthetic row becomes a theorem or an
observational result by being included in the same document.

## Priority proof backlog (`NOT_ATTEMPTED`)

The following proposals were registered but never independently proved. This
order maximizes scientific leverage while respecting dependencies:

1. `I-1.3`: orbit dimensions and isotropy strata;
2. `I-2.6`: degree-bounded catalogue closure;
3. `I-2.7`: global principal-stratum orbit separation;
4. `I-2.8`: Molien-Hilbert/full invariant-ring question;
5. `I-6.4`: kinematic invariant space to constraint-realizable geometry;
6. `II-2.2`: functional-indexed well-posedness table;
7. `II-4.4`: partial-identification envelope optimization conditions;
8. `II-5.1`: maximal-invariant theorem, after catalogue completeness;
9. `II-5.2`: Hunt-Stein applicability for the exact registered testing problem;
10. `II-5.3`: finite catalogue/look-elsewhere completeness, after `I-2.7` and
    `I-2.8`;
11. `B-1`: typed separation of algebraic morphology bounds from MES anchor
    authority.

The largest immediate proof target is `I-2.7`, but it must not be inferred from
the `VT-T8` local Jacobian. The largest physical target is `I-6.4`, which
requires the complete constraint map rather than a transfer solver.

## Minimal closure DAG

```text
current adjudication overlay
        |
        +--> exact-head binding repair --> affected replay
        |                                  |
        |                                  +--> Note A candidate
        |                                  +--> Note B candidate
        |
        +--> J1/J2 direct negative replay --> Note B candidate
        |
        +--> new preregistered PR-284 contract, if desired
                                             |
                                             +--> four-axis PASS or retained block

I-1.3 --> I-2.6 --> I-2.7 --> I-2.8 --> II-5.1 --> II-5.2/II-5.3
                         |
                         +--> no automatic edge to I-6.4
```

No manuscript or claim ledger should be expanded before the first two closure
steps produce current replay evidence. The matrix and this report are the only
new audit outputs.

## Claim ceiling

Safe terms for these results are:

- `observation-independent exact theorem core`;
- `premise-conditional linear-algebra result`;
- `exact negative obstruction`;
- `preregistered synthetic validation result`;
- `local quotient-chart result`.

Forbidden extensions include detection, native-transfer validation, physical
CF4 identification from a synthetic matrix, global orbit separation from a
local Jacobian, full dynamics from an invariant chain rule, and Bianchi-family
identification.

## Watchdog and metacognitive closeout

```yaml
watchdog:
  production_modules_added: 0
  global_ledgers_added: 0
  observed_data_opened: false
  current_head_publication_promotions_made: 0
  scientific_candidates_promoted_at_exact_evidence_scope: 36
  scientific_candidates_not_attempted: 11
  no_scientific_result_survived_eligible: false
  historical_receipts_rewritten: 0
  scientific_outputs:
    - one complete reconciliation matrix
    - one human audit report
    - one shared finite-fixture CAS package
  decision: STOP_INVALID_FOR_CURRENT_PROMOTION

metacognitive_output:
  decision: STOP_INVALID_FOR_CURRENT_PROMOTION
  falsifier: >-
    The affected exact-head replay passes, a current adjudication overlay
    preserves every negative and blocked row, and every promoted R3 statement
    receives a shared four-axis pass plus independent statement-level review.
  next_action: >-
    Repair the stale bindings and generate the current overlay before selecting
    the first exact theorem note; leave every broad non-PASS row unchanged.
```

The metacognitive pass ends in these observable outputs and this explicit stop
decision. No second-order evaluation of the reflection is introduced.
