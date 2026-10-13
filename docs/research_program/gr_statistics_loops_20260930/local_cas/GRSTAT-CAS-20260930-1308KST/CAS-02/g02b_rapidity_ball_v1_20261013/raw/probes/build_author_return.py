import hashlib, json, pathlib, re
T = pathlib.Path(__file__).resolve().parents[2]
REPO = pathlib.Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
sh = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
rel = lambda p: str(pathlib.Path(p).resolve().relative_to(REPO))
raw = T / "raw"
receipts = []
for j in sorted(raw.glob("compile_*.json")):
    d = json.loads(j.read_text()); d["receipt"] = rel(j); receipts.append(d)
audit_out = (raw / "compile_05_audit.stdout").read_text()
axiom_lines = [l for l in audit_out.splitlines() if "depends on axioms" in l]
names = re.findall(r"^theorem (\S+)", (T / "lean" / "G02BRapidityBall.lean").read_text(), re.M)
groups = {
 "T1_gram_max_eigenvalue_operator_norm": ["gram_quad_eq","gram_quad_le","gram_eig_le","gram_lamMax_eigen","gram_max_eigenvalue","gram_rayleigh_max","lamMax_zero","future_eq_emb_chart","emb_norm_sq","future_hasFDerivAt","futureJac_norm_sq","futureJac_opNorm"],
 "T2_rapidity_bound_monotonicity": ["lamMax_le_rapidity","lamMax_at_rapidity","lamMax_mono","rapidity_cap_monotone","rapidity_mem_ball","rapidity_R_zero","futureJac_opNorm_le_rapidity"],
 "T3_closed_ball_projection": ["ballProj_norm_le","ballProj_eq_self_iff","ballProj_variational","ballProj_nearest","ballProj_nonexpansive","ballProj_error","ballProj_zero_radius","ballProj_moves"],
 "T4_mean_value_lipschitz": ["fstJac_norm_le","rapidity_ratio_le","chart_fst_lipschitz_on_ball","future_lipschitz_on_ball","clipped_future_error","clipped_monopole_check"],
 "T5_C04_connection": ["G02B_offshell_inverse_bound","G02B_offshell_inverse_bound_explicit"],
 "boundary_nonvacuity_negative_controls": ["G02B_R_zero_constants","G02B_nonvacuous_offshell","scalar_bound_needs_ball"],
}
for g, ns in groups.items():
    for n in ns: assert n in names, n
    for n in ns: assert any(f"'G02B.{n}' depends on axioms: [propext, Classical.choice, Quot.sound]" == l for l in axiom_lines), n
frozen = {g: {"theorems": ["G02B."+n for n in ns], "status": "PROVED_COMPILED_AXIOM_CLEAN"} for g, ns in groups.items()}
helpers = [n for n in names if not any(n in ns for ns in groups.values())]
C = REPO / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-02"
ret = {
 "schema": "htt.g02-b.author-return.v1",
 "task_id": "G02-B", "parent": "GR-CAS-02", "date": "2026-10-13",
 "status": "ALL",
 "status_scope": "All frozen Lean targets in FROZEN_TARGETS.md compiled (exit 0) with axioms exactly [propext, Classical.choice, Quot.sound]. Author-side only: independent fresh review (card acceptance 4) NOT performed; wolfram_xact/sympy/sage_singular tool_tasks NOT executed.",
 "requested_runtime": {"model": "claude-opus-5-5", "effort": "high", "billing": "subscription (in-session subagent fallback after API credit exhaustion)"},
 "observed_runtime": "UNKNOWN (not externally attested; author's own system prompt names model id claude-opus-5-5)",
 "interrupted_attempt": {
   "found_in_T": ["SOURCE_RECOVERY.md", "lean/ (empty)", "raw/imports/ (empty)", "raw/probes/ (empty)"],
   "raw_receipts_found": 0,
   "FROZEN_TARGETS_md_found": False,
   "disposition": "SOURCE_RECOVERY.md kept unchanged after re-verifying every quoted sha256 and file:line; FROZEN_TARGETS.md written fresh by the continuing author before the first proof compile (compile_03)."
 },
 "card": {"path": "HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip!HTT_ALL_OBLIGATIONS_20261011/tasks/G02-B.json",
          "zip_sha256": sh(REPO/"HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip"),
          "member_sha256": "b89a6a10133393b4dee956c8e233100a0b65d7d10596b21d0052b531aa757a9d"},
 "repository_head": "b976a27ca0c4fc038788e6ab8449e2d7e98b1b76",
 "source_recovery": {
   "file": rel(T/"SOURCE_RECOVERY.md"), "sha256": sh(T/"SOURCE_RECOVERY.md"),
   "citations": [
     "docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-02.json (sha256 71283a74...57a3): C03/C04 component_definitions; positive_norms convention; STAB-R0/STAB-AMPLITUDE/STAB-OFFSHELL",
     "docs/research_program/gr_statistics_loops_20260930/gr/OPTICAL_THEOREMS.md (sha256 5ae2b6a6...8c21): line 104 rapidity; line 162 Euclidean observer norms; lines 171,175-180 M, Theorem 4 / eq (20); lines 210-220 off-shell projection, eqs (22),(23); line 212 no exact-image claim",
     "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md (sha256 4714827e...1897): no projection/rapidity definition",
     "Cas02.lean: chart 116, chartJac 118, C03_hasFDerivAt 122, chartJac_apply 131, chartGram 142, C03_gram 145, gramVec 162, C03_gram_action 165, C03_longitudinal 186, C03_zero_repeated 200, C03_eigenvalue_only 203, ratio_mono 249, C03_rapidity_bound 256",
     "InverseBound.lean: Vec4/Vec3/Mat4 7-9, future 18, rapidityCap 29, future_norm_le_cap 35, spectral 53, spectral_nonneg 138, inverse 187, CAS_02_C04 213"
   ],
   "missing_items": "none blocking; physical admissibility of the clipped output is not a theorem in the source and is not claimed"
 },
 "frozen_targets_file": {"path": rel(T/"FROZEN_TARGETS.md"), "sha256": sh(T/"FROZEN_TARGETS.md")},
 "frozen_targets": frozen,
 "helper_theorems_also_audited": ["G02B."+n for n in helpers],
 "signature_fidelity_note": "Elaborated #check types (raw/compile_05_audit.stdout) match FROZEN_TARGETS.md; ‖Sstar - S‖ unifies with the Frobenius norm instance of CAS02C04.CAS_02_C04 (proof applies it directly). R is never assumed nonnegative; R=0 and d=0 are covered (rapidity_R_zero, lamMax_zero, ballProj_zero_radius, G02B_R_zero_constants, G02B_nonvacuous_offshell).",
 "explicit_constants": {"M": "CAS02C04.rapidityCap R = sqrt(cosh(2R))", "regularity": "G02B.lipConst R = sqrt(1 + tanh(R)^2) (= sup over ball of exact op norm sqrt(lamMax d) of the actual Euclidean-target derivative)", "projection": "1 (ballProj_nonexpansive)", "amplitude": "min(spectral S, spectral Sstar) or spectral Sstar alone"},
 "sources": {
   "main": {"path": rel(T/"lean/G02BRapidityBall.lean"), "sha256": sh(T/"lean/G02BRapidityBall.lean")},
   "axiom_audit": {"path": rel(raw/"AxiomAudit.lean"), "sha256": sh(raw/"AxiomAudit.lean")},
   "compile_harness": {"path": rel(raw/"run_compile.py"), "sha256": sh(raw/"run_compile.py")}
 },
 "imports": {
   "Cas02": {"source": rel(C/"c01_c03_input_aligned_v1_20261005/lean/Cas02.lean"), "source_sha256": sh(C/"c01_c03_input_aligned_v1_20261005/lean/Cas02.lean"), "olean": rel(raw/"imports/Cas02.olean"), "olean_sha256": sh(raw/"imports/Cas02.olean"), "review": "c01_c03_independent_review_v1_20261011/RETURN.json PASS_SCOPED"},
   "InverseBound": {"source": rel(C/"c04_inverse_bound_v1_20261008/lean_clean/InverseBound.lean"), "source_sha256": sh(C/"c04_inverse_bound_v1_20261008/lean_clean/InverseBound.lean"), "olean": rel(raw/"imports/InverseBound.olean"), "olean_sha256": sh(raw/"imports/InverseBound.olean"), "note": "PR #498 payload (head c0365da5), untracked locally, byte-identical per G02-A closeout"},
   "G02BRapidityBall_olean_sha256": sh(raw/"imports/G02BRapidityBall.olean")
 },
 "toolchain": {"lean": "4.31.0 (leanprover/lean4:v4.31.0)", "mathlib": "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f", "lake_project": "/home/cosmosapjw/lean_oracles/viii_oracle"},
 "receipts": receipts,
 "print_axioms_output": axiom_lines,
 "print_axioms_count": len(axiom_lines),
 "remaining_warnings": "main compile: 5 linter.unusedSectionVars notes (InnerProductSpace auto-included, matching frozen signatures) and 1 deprecation (EuclideanSpace.norm_single); no sorry/admit/native_decide/axiom/maxHeartbeats in source",
 "first_failure": {"receipt": rel(raw/"compile_03_main.json"), "exit_code": 1, "location": "G02BRapidityBall.lean:410:16", "message": "Application type mismatch: add_le_add_left in this Mathlib produces `b + a ≤ c + a`; expected left-fixed addend", "fix": "replaced by `add_le_add le_rfl (...)` (also push_neg -> not_le.mp); compile_04_main exit 0", "substantive": False},
 "tool_axes": {"wolfram_xact": "NOT_EXECUTED", "sympy": "NOT_EXECUTED", "sage_singular": "NOT_EXECUTED", "lean": "EXECUTED"},
 "independent_review": "NOT_PERFORMED (required by card acceptance 4; author cannot self-review)",
 "not_claimed": [
   "scientific admission",
   "physical admissibility or exact-image membership of the supplied dipole/sky or of the clipped output (STAB-OFFSHELL)",
   "sharpness of the C04 constants; statistical calibration",
   "rate-amplitude-independent stability (STAB-AMPLITUDE)",
   "independent fresh review / four-axis CAS PASS",
   "Wolfram/xAct, SymPy, Sage/Singular certificates",
   "publication / commit / PR state"
 ],
 "scientific_admission": "HOLD"
}
(T/"AUTHOR_RETURN.json").write_text(json.dumps(ret, indent=1, ensure_ascii=False) + "\n")
print("ok", len(axiom_lines), len(names), helpers)
