# CLAUDE.md — non-authoritative compatibility entry point

This file is not a second source of truth and must not accumulate rolling
session status. Its former log is recoverable from Git history.

The authority boundary is:

- `AGENTS.md` — durable agent policy.
- `.agent-harness/context/CONTEXT_INDEX.json` — sole persistent harness
  context configuration.
- `.agent-harness/generated/CONTEXT_PACK.md` — generated bounded delivery
  view, never scientific authority.
- `docs/codex_handoff/pr_backlog.yaml` and `pr_status.yaml` — canonical DAG
  and execution status; `machine_readable/` contains compatibility mirrors.
- Owning code, tests, contracts, specifications, and
  `docs/SSOT_POLICY.md` — scientific meaning and numerical ownership.

The context harness cannot promote validity, novelty, readiness, or a claim.

## 1. Project identity

BASS/HTT studies CMB T+E+B spectra and graded FLRW departure through the
typed `JointAnisotropyState`. It seals congruence, velocity-frame, geometry,
units, missing components, content identity, and transfer provenance before a
functional, orbit, likelihood, or diagnostic can consume the state.

The historical scalar
`x_C = Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso}` is not the current state
authority and is not an anisotropy norm. It may appear only in an explicit
`LegacyProjectionReport` carrying the BC1/BC2 conditions, source state,
comparator, frame, units, and loss/cancellation disclosure. It is never
auto-promoted into a vector/tensor state.

Older code and reports cite this section for the dual MB-95/PSTF architecture
and for the honest coverage envelope: full-mode end-to-end LoS closure is
limited to FLRW, I, V, and IX; the remaining families are axis-aligned
subsets, and off-axis work must fail closed. The owning dispatch, runtime
controls, and scientific contracts decide the current boundary.

## 2. Canonical directory map

Use the repository tree and the ownership map in `AGENTS.md`. Manuscript
sources live under `docs/manuscript/`; `project/` is local-only planning;
`legacy/` is archival; `.agent-harness/` and `.codex/` own the execution
harness.

## 3. Current phase status

The former rolling phase log is historical. Use
`docs/codex_handoff/pr_backlog.yaml` and
`docs/codex_handoff/pr_status.yaml`; hooks resolve HEAD and the stable active
run summary at invocation time. Historical references to a numbered blocker
or phase in this section describe the cited revision, not current authority.

## 4. Active manuscript

Use the manuscript build configuration and current sources under
`docs/manuscript/`.

## 5. Physics-parameter compatibility anchors

Older live comments and tests cite this section. The values below are a compact
legacy compatibility index only. They cannot seed, anchor, or validate the
current typed state or inference path; follow the named owner and a generated
source for current semantics.

- Historical production labels: `ln B(FLRW_tilt)=+26.40`,
  `β=1.360e-3`, and `F_Bayes=0.093±0.025`. They remain legacy-only until
  PR-288 independently revalidates normalized likelihood/prior, evidence,
  PPC, and LOOCV semantics.
- `T_CMB=2.72548 K` and `z_*=1089.94`:
  `docs/SSOT_POLICY.md` and owning configuration/tests.
- `D_2=1002.086744 μK²`: enforced on the Rust MB-95 path; the PSTF Python
  closure remains the status expressed by its owning test.
- `D_2(Σ²=1e-8)=0.174112 μK²`: owning gallery/validation test.
- `Π_BASS=Θ₂+E₀+E₂`; production
  `polter=2Θ₂/5+3E₂/5`: `docs/SSOT_POLICY.md` and transport code.
- `W²=ω_abω^ab/(6H²)` and the current admissibility ceiling: owning
  scientific contract, comparator code, and gate tests.
- Historical performance target: 10–15 seconds for a single run, with the
  benchmark method and environment supplied by the owning benchmark.

Ownership order remains exact transport → normalized hierarchy → canonical
source primitives → LoS/observable assembly → feature extraction → typed
state → separate diagnostics/inference. BASS owns physics and transfer/atlas
adapters, OBSSTAT observable features, HTT model-dependent inference, MIO
family-independent diagnostics, and COMMON the shared contracts/firewalls.

## 6. Compatibility prohibitions

Durable workflow policy lives in `AGENTS.md`; scientific prohibitions live in
the roadmap, owning code, and tests. Older references to this section mean:

- do not introduce a TCA pre-phase, FLRW UFA, or photon RSA under the
  approximation-free roadmap;
- the conditional inline DAE relaxation in
  `htt/bass/hierarchy/integrator.py` is permitted because the ODE hierarchy
  remains integrated; its smooth transition is owned by
  `test_tca_switch_smoothness.py`;
- do not edit `legacy/`, commit `project/`, create duplicate CHANGELOGs, or
  infer mock status from images when structured status exists.

## 7. Session closeout

Use `AGENTS.md` and the governing task workflow. Do not append session
history or current-state claims here.
