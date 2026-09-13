# Phase 9 — Independent Diff Review

A reviewer independent of implementation reads the fixed base/candidate diff, task/scientific contracts and necessary actual evidence. Report blocking correctness, scientific inconsistency, numerical instability, regression, missing discriminating checks, error swallowing, hidden scope and provenance flaws first. Each finding needs location, impact and evidence or a reproducible counterexample. If independence is unavailable, label the result self-review.

The owner repairs in-scope findings and rechecks the affected claim. Do not create reviewer-of-reviewer recursion without new evidence. Close when necessary findings and required checks are resolved, or identify a concrete blocker and retained claim ceiling. Unresolved scientific failures cannot be promoted by unsupported risk acceptance.
