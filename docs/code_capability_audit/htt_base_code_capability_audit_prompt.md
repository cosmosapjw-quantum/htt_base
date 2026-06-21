# Code-Capability / Execution-Feasibility Audit Prompt

You are an external engineering+scientific auditor. Your job is to assess
**what this codebase can actually run and compute**, and whether its claimed
capabilities are supported by the source. Review the code as code; do not grade
the project's claim tiers here (a separate package covers results/claims).

## Inputs

This archive only. Start from the four guides at the archive root
(`01_ARCHITECTURE_GUIDE.md`, `02_CODE_MAP.md`, `03_ENTRY_POINTS.md`,
`04_DATA_ACCESS.md`), then read the raw source under `code_capability_audit/`.

## Questions to answer

1. **Runnability.** For each major entry point in `03_ENTRY_POINTS.md`, is the
   code path actually executable as described? Identify missing dependencies,
   dead imports, or stubs masquerading as implementations.
2. **Capability inventory.** Enumerate what the codebase can genuinely compute:
   the Rust MB-95 solver path, the PSTF/tetrad hierarchy, recombination/kinetic
   theory, the HTT inference layer, the MIO diagnostics, the OBSSTAT estimators,
   the execution stacks. Flag any capability that is asserted in docstrings but
   not implemented.
3. **Data reach.** Using `04_DATA_ACCESS.md`, confirm what real data the code
   can load and what must be downloaded first. Are the loaders consistent with
   the download manifest? Any path that cannot be satisfied?
4. **Legacy / deprecated executability.** The `htt/tsc` legacy layer is shipped.
   Determine whether it still runs independently, what it computes, and whether
   any of it is worth re-activating or is safe to retire.
5. **Architecture integrity.** Are the BASS/HTT/MIO/OBSSTAT ownership boundaries
   real in the code (imports, interfaces), or only documented?
6. **Risk.** Where would a new contributor be misled about what runs?

## Output

1. `Capability Map`: table `Subsystem | Runnable? | What it computes | Evidence (path) | Gaps`.
2. `Entry-Point Findings`: per-entry status (runs / needs-deps / broken / stub).
3. `Data-Reach Findings`: which inputs are satisfiable, which need downloads.
4. `Legacy Verdict`: tsc (and any other legacy) — runs / partial / dead; reactivate or retire.
5. `Architecture Findings`: where ownership boundaries hold or leak.
6. `Top Risks`: ranked list of places where capability is over- or under-stated.

Cite `path:line`. Prefer concise tables. Do not review code style or formatting.
