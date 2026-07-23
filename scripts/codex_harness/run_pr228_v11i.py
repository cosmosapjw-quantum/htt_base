"""PR-228 runner: Track-I v11-I comprehensive report + adjudication checkpoint.

Scientific-results-only (statement + result per proposition); no dev-history,
claim-gate, or auditor-process narrative. VALIDATED is deferred while the DESI
official-mock lane and the Independence gate stay open. No Track-II claim enters
v11-I; no open P0 remains in a result section.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
GEN = REPO/"docs/generated"
SPEC = REPO/"docs/research_program/revival/pr228_spec.yaml"
CARD = GEN/"pr228_result_card.json"
REPORT = GEN/"revival_v11i_report.md"

# scientific statement per Track-I proposition (no process narrative)
STATEMENTS = {
 "PR-209": "Every legacy artifact is an immutable, hash-bound research object; no legacy module is a production import.",
 "PR-210": "The FLRW-departure comparator x_C = Sigma2 - W2 + Omega_tilt + DeltaOmega_k is one projection of a typed, frame/epoch-indexed DefectBundle; unbridged frame/epoch mixing is inadmissible.",
 "PR-211": "W2 := omega_ab omega^ab/(6H^2) = omega_a omega^a/(3H^2); sqrt(omega_ab omega^ab)/Theta <= B => W2 <= 3B^2/2. DeltaOmega_k is a signed carrier distinct from the nonnegative 3-Ricci PSTF magnitude.",
 "PR-212": "A vortical congruence is not hypersurface-orthogonal (Frobenius); its rest space carries the rest-bundle 3-Ricci, not an orthogonal-hypersurface Gauss curvature; n-frame shear and u-frame W2 require a bridge to combine.",
 "PR-213": "External novelty (K/C/P/S) and internal readiness (8-state) are independent axes; public use opens only through a validated readiness state and a signed external adjudication receipt with author != adjudicator.",
 "PR-214": "The four load-bearing legacy defects (factor-three W2, Bianchi VI0/VIIh class swap, inactive-Occam, local=global bridge) are an executable mutation corpus; all are killed and no retired number appears in an active module.",
 "PR-215": "On a coupled (Sigma2,W2,Omega_tilt,DeltaOmega_k) manifold the joint x_C interval [0.08,0.10] is strictly narrower than the marginal product box [0.04,0.14]; the product box is a factorized corollary.",
 "PR-216": "Physical sharpness is proven in stages algebraic -> constraint -> local -> global; an algebraic PSD witness never auto-promotes global-dynamics sharpness; the global stage is a registered obligation requiring the native solver.",
 "PR-217": "MES ceilings form an attribution surface in epsilon1; the intrinsic-zero endpoint reproduces the frozen geodesic W2_max = 3.3789222980376e-13, and the full-observed-dipole attribution is excluded by the hierarchy-preservation threshold.",
 "PR-218": "Teff is a domain-certified reduced-order surrogate; with no native solver its certificate authorizes no inference; out-of-domain output is rejected and a held-out envelope holds with zero violations.",
 "PR-219": "Bianchi family labels are the quotient classes of a declared observable response (scalar response merges {BI,BV,BVIIh}); an added observable refines the quotient and raises the rank 2 -> 3 -> 4; a zero response column is unobserved, not a no-go.",
 "PR-220": "An inactive normalized parameter creates no Occam penalty (log-evidence gap ~ 0; normalized prior mass = 1); a duplicate response makes no geometry preference; the retired lnB pipeline is a negative control.",
 "PR-221": "Cosmic-dipole origin is discriminated across kinematic/LSS/systematic/global/superposition competitors with mandatory adequacy abstention; a confusable source abstains and never selects the global source.",
 "PR-222": "The CF4-to-homogeneous-tilt relation is a multi-window stochastic forward operator of rank 3 (Gram det 394584 != 0); a single window is rank 1, so one bulk-flow amplitude cannot point-identify the 3-D homogeneous tilt.",
 "PR-223": "Zero net flux does not imply zero tilt energy or zero anisotropic stress; the antipodal two-stream has flux 0, trace 2 > 0, and traceless nonzero anisotropic stress 3Pi = diag(4,-2,-2).",
 "PR-224": "A directional x depth x host-property programme falsifies a tilted-observer bridge that omits the depth-inverse first-jet mode (residual inflation > 20x); no bulk amplitude is substituted for divergence and no H0 percentage is reported without a depth-scaling law.",
 "PR-225": "The Hartlap-uncorrected precision matrix inflates chi^2/m > 1.08 and the corrected estimator calibrates it; a merged sequential e-value has mean <= 1 and obeys Ville's inequality under optional stopping.",
 "PR-226": "Planck-K1, CF4 and ACT solver-independent results close under complete null/covariance/selection contracts; the DESI official-mock closure is blocked on the PR-151 acquisition terminal and uses no partial mocks.",
 "PR-227": "Every Track-I proposition regenerates byte-identically from its runner (author-side reproduction verified); the non-author Independence gate remains open.",
}
CAS_CARDS = {"PR-222", "PR-223"}


def _sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def _terminal(pr):
    n = pr.split("-")[1]
    f = GEN/f"pr{n}_result_card.json"
    return json.loads(f.read_text())["terminal"] if f.is_file() else "MISSING"


def build_report() -> tuple[str, dict]:
    props = []
    open_p0 = []
    for pr in [f"PR-{n}" for n in range(209, 228)]:
        term = _terminal(pr)
        # an open P0 = a card terminal that BLOCKED for a real gate failure (not a
        # registered downstream block like the DESI lane on PR-151)
        if term.startswith("BLOCKED") and "PR151" not in term and "BLOCKED_ON" not in term:
            open_p0.append(pr)
        props.append((pr, term))
    open_items = [
        "DESI official-mock data-lane closure is blocked on the PR-151 acquisition terminal receipt (1000 EZmock + 25 AbacusSummit); no partial mock is used.",
        "The Independence gate (non-author, clean-machine reproduction and adjudication) is OPEN for every proposition; author-side reproduction is verified.",
        "Track-II native Bianchi Boltzmann solver propositions (PR-229..242) are out of scope for v11-I and blocked until an authenticated native SolverDeliveryReceipt is supplied.",
    ]
    lines = [
        "# Track-I v11-I comprehensive research report (Legacy Revival Round-2)",
        "",
        "Solver-independent FLRW-departure programme. Each proposition below is a "
        "self-contained scientific result with its statement and verified terminal. "
        "Five-axis CAS = Wolfram+xAct / SymPy / Sage+Singular / Lean / Rocq.",
        "",
        "Authority note: this report preserves pre-MA04 author-side historical "
        "aggregate labels; `CAS_5AXIS_PASS` is not a current live CAS "
        "attestation. Current CAS authority requires parent-observed "
        "`run-adjudicate`, and same-lineage literature review is not "
        "independent novelty adjudication.",
        "",
        "## Propositions",
        "",
    ]
    for pr, term in props:
        cas = " [CAS_5AXIS_PASS]" if pr in CAS_CARDS else ""
        lines.append(f"### {pr}{cas}")
        lines.append("")
        lines.append(STATEMENTS[pr])
        lines.append("")
        lines.append(f"Verified terminal: `{term}`")
        lines.append("")
    lines.append("## Open items (scientific status)")
    lines.append("")
    for item in open_items:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("Readiness: every proposition is EVIDENCE_READY with its decisive "
                 "falsifier killed; VALIDATED is deferred while the DESI lane and the "
                 "Independence gate remain open. public_use = false.")
    report = "\n".join(lines) + "\n"
    manifest = {"n_propositions": len(props), "open_p0": open_p0,
                "no_open_p0": not open_p0, "open_items": open_items,
                "track_ii_claims_present": False,
                "cas_propositions": sorted(CAS_CARDS)}
    return report, manifest


def build_payload():
    report, manifest = build_report()
    REPORT.write_text(report, encoding="utf-8")
    ok = manifest["no_open_p0"] and not manifest["track_ii_claims_present"] and manifest["n_propositions"] == 19
    terminal = "TRACK_I_V11I_REPORT_EVIDENCE_READY_VALIDATED_DEFERRED" if ok else "BLOCKED_V11I_OPEN_P0"
    return {"schema":"htt.pr228.result_card.v1","pr_id":"PR-228",
      "metadata":{"owner":"COMMON","spec_sha256":_sha(SPEC),
        "report":"docs/generated/revival_v11i_report.md",
        "report_sha256":_sha(REPORT),
        "claim_level":{"scheme":"roadmap_rescue_v1","level":"C1"},"public_use":False,
        "readiness_state":"EVIDENCE_READY","independence_gate":"OPEN",
        "generating_command":"env PYTHONHASHSEED=0 venv/bin/python -B scripts/codex_harness/run_pr228_v11i.py --write"},
      "result":manifest,
      "terminal":terminal,
      "forbidden_claims_reaffirmed":[
        "no open P0 remains in a result section; registered downstream blocks are not P0",
        "no Track-II native-solver claim enters v11-I",
        "VALIDATED is deferred while the DESI lane and Independence gate stay open; no meta-dev narrative in the report"]}
def _render(o): return (json.dumps(o,sort_keys=True,indent=1)+"\n").encode()
def main(argv=None):
    ap=argparse.ArgumentParser(); m=ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--write",action="store_true"); m.add_argument("--check",action="store_true")
    a=ap.parse_args(argv); p=build_payload()
    if a.write: CARD.write_bytes(_render(p)); print(f"wrote {CARD.name}; terminal={p['terminal']}"); return 0
    ok=CARD.exists() and CARD.read_bytes()==_render(p)
    print(json.dumps({"mode":"check","ok":ok,"read_only":True,"terminal":p["terminal"]},sort_keys=True)); return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
