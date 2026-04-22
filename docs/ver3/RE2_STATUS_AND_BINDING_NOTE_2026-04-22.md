# RE2 Status And Binding Note — 2026-04-22
## supplemental repo-state matrix for the active `htt_base` implementation

This note is supplemental only.

- It does not override `00_AUTHORITY_TREE.md`.
- If this note conflicts with the main design pack, the authority docs win.
- Its sole purpose is to keep the current repo state aligned with the ver3 PR ladder.

---

## 1. RE2 interpretation

RE2 in the active repo means:

1. re-read `docs/ver3/*` as the semantic SSOT,
2. compare the documented PR ladder against live `htt/bass/*` code,
3. separate **API presence** from **runtime wiring** and from **gate-opening evidence**,
4. fail closed whenever a higher-layer claim is not backed by a lower-layer bundle.

---

## 2. current matrix

| PR | scope | current repo state | strongest allowed claim |
|---|---|---|---|
| PR-00 | authority freeze | docs present, binding note present | authority frozen |
| PR-01 | tensor helpers | live helpers in `htt/src/common/conventions.py` | tensor helper frozen |
| PR-02 | family registry | live all-family metadata in `htt/bass/background/bianchi_types.py` | registry-complete |
| PR-03 | geometry core | live geometry operators + owner-module gate emitter; runtime consumes integrator-routed upstream geometry gate fragments | geometry contract present |
| PR-04 | matter projection | live projection helpers + owner-module gate emitter; runtime consumes integrator-routed matter gate fragments | matter projection contract present |
| PR-05 | background core | live RHS / residual helpers + owner-module gate emitter; runtime consumes integrator-routed background gate fragments; branch-level production claim still closed | background contract present |
| PR-06 | exact Thomson | live electron-frame collision wrapper + tests; final runtime Thomson probe is integrator-owned | exact collision contract present |
| PR-07 | visibility/history | live visibility adapters + tests; visibility gate evidence routes through integrator-owned gate fragments | source-history contract present |
| PR-08 | backend protocol | live backend/translator/seed contract plus bound operator payloads; runtime consumes backend-owned seed packs and integrator-bundled backend gate evidence, and native readiness/output now fail-closed on unresolved backend verification bundles | backend contract bound to executable sparse payloads, but not all-family production numerics |
| PR-09 | hierarchy layout | live layout/packing helpers, split block templates, integrator-owned runtime execution/trace bundle, multi-label canonical harmonic projection where standard `m0/m±2` labels are available, resolved canonical sector order including `src`, auxiliary `ph_B/baryon/cdm/src` histories, and integrator-bundled hierarchy gate evidence carrying multi-label projection provenance | hierarchy layout frozen with integrator-owned canonical projection and execution trace bundle; auxiliary sectors are bounded, not fully live-coevolved |
| PR-10 | output split | live archive writer; solver output and archive auto-carry upstream+output bundle chain; native runtime now sources solver-output inputs from the integrator-owned execution bundle, exposes the execution-bundle builder on the forward public surface, packages Tier-B runtime requests into dedicated request bundles, validates/runs/prepares those bundles through dedicated helpers, and routes gate-registry construction, solver-info stamping, plus both pre-run and post-run assembly through request-aware bundle helpers | output split surface present, claim depends on supplied bundles |
| PR-11 | validation hard stop | live gate bundle schema, gate status summary, readiness scoring, fitting hard stop | fitting remains blocked unless upstream bundles exist |

---

## 3. implementation stance after RE2

- `ModeOps` is no longer metadata-only; it now carries bound mass/exact-template block payloads.
- Upstream PR-03..09 gate evidence now routes through shared gate fragments, with PR-06/08/09 runtime probes, multi-label canonical projection, resolved canonical sector order, and execution-trace bundles owned by the integrator.
- `write_output_archive(...)` no longer assumes `output_split_gate=open`; it derives gate status from the supplied registry.
- Native Tier-B runtime now sources gate registry, solver output, public trace, public run assembly, request packaging/validation/execution, native solver-info stamping, pre-run context preparation, and Tier-B post-run orchestration from request-aware bundle helpers rooted in the integrator-owned execution bundle instead of assembling those inputs ad hoc.
- `hard_gate_before_fitting(...)` and `score_branch_readiness(...)` accept machine-readable gate bundles as well as legacy bool maps.
- Empty or partial gate registries keep higher gates unavailable by construction.

---

## 4. remaining open work

- PR-08 and the fully live-coevolved harmonic part of PR-09 are still wired to bounded sparse templates, not all-family production numerics.
- PR-11 hard-stop logic is live, but fitting authority remains closed until real upstream bundles are present.
