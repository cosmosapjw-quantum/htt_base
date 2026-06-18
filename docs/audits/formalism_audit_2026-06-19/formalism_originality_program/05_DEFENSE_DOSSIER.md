# 05 — Defense Dossier (Anticipated Objection → Response)

Referee-proofing for the originality case. Each row: the strongest version of the objection (steelman), the honest response, and the supporting artifact.

---

## On whether it is "real" methodology

**O1. "This is software engineering, not statistics or physics."**
*Reframe.* The novel object is a *statistical* one: a certification semantics (an occupancy that exists iff its preconditions hold), a registered-threshold exceedance curve, a confound-separated depth contrast, and a signed projection with a cancellation invariant. The enforcement is the mechanism; the methodology is the contribution. → *§01 F2–F5; §04 E1–E4.*

**O2. "Multiverse / specification-curve analysis already does this."**
*Differentiate.* Multiverse analysis (Steegen 2016) *enumerates outcomes* across forks; it does not (a) refuse to construct an over-claimed object, (b) pin owner/tier, or (c) enforce a diagnostic↔inference type boundary. The formalism *encodes* the multiverse forks as typed policies (comparator, numerator, denominator, threshold, measure-kind) and adds the firewall and the boundary. We cite multiverse analysis as the nearest relative and state exactly what is added. → *§06; §03 U5; §04 E5.*

**O3. "Blinding/pre-registration already prevent overclaim."**
*Distinguish.* Blinding hides *results* to protect analysis *choices*; pre-registration commits to choices in advance. Neither prevents *mislabeling a diagnostic as evidence* after the fact. The semantic firewall is a structural prohibition on the label, complementary to blinding. → *§01 F1; §06.*

## On the firewall

**O4. "Reserved-language scanning is brittle / just disclaimers."**
*Concede the brittleness, defend the design.* It is one layer; it is paired with owner/tier pinning, fail-closed numerical gates, and a typed boundary, and it is validated by an adversarial fuzzer (0 successful smuggles). The audit could not break it. We document the reserved sets as a spec so they can be reviewed and extended. → *§01 F1/F9; §04 E6; §03 U3.*

**O5. "A determined author can bypass it (e.g., in free-text prose)."**
*Concede the boundary.* Correct — the firewall guards *objects and figure labels*, not arbitrary prose; that is exactly the gap the audit found (the semantic-split figure, the "detection" prose). The fix is the figure-label linter (U3) plus the prose claim-lint promoted to fail. We do not claim the firewall polices the whole manuscript. → *§03 U3; audit §8.*

## On the diagnostics themselves

**O6. "`x_C` is just the Friedmann constraint."**
*Concede the algebra, defend the packaging.* Exact by design; the contribution is the signed/sector packaging plus the cancellation invariant that prevents `x_C≈0` from reading as isotropy (verified). → *§01 F2; §04 E1.*

**O7. "`F` is just `x/x_max`; calling it a certified filling fraction is grandiose."**
*Concede the naming, defend the semantics.* The novelty is the *fail-closed certification* (no clipping, sign-clean, admissible-ceiling-only) and the paired magnitude companion; we define the name precisely and drop occupancy connotations. → *§01 F3/F8; §03 U2; §04 E2.*

**O8. "`Π` is a survival function; `G_F` is a depth ratio."**
*Concede the base, defend the guards.* `Π` adds typed threshold pre-registration + anti-post-hoc; `G_F` adds the numerator-vs-denominator-evolution split + matched-null requirement. Those guards are the contribution, and E3/E4 quantify what they buy. → *§01 F4/F5; §04 E3/E4.*

**O9. "`G_F` doesn't separate boost from tilt — so what good is it?"**
*Concede & forecast.* Correct under the current (unmatched) nulls (FPR≈1); the framework *honestly blocks* the claim. The upgrade (U4/E4) provides matched-null calibration and a depth-template discriminant, turning the limitation into a quantitative forecast. → *§03 U4; §04 E4.*

## On scope and stance

**O10. "The diagnostics detect nothing — why publish?"**
*Reframe.* The contribution is the *architecture and its guarantees*, not a detection. A framework that makes contested-anomaly reporting structurally honest is the durable result; the audit removing our overclaim is evidence the framework is needed. → *§00; §01 F1.*

**O11. "Legacy VER2 artifacts claim atlas/production-grade — your honesty story is undercut."**
*Concede & fix.* Those are quarantined as `prior_context_only`; the live firewall bars the overclaims. We over-stamp the legacy payloads' internal `atlas_available`/`production-grade` fields as `legacy_not_current` so they cannot be surfaced. → *audit §4/§9; §03 corrections.*

---

## Two-column response-letter template

> **Referee:** ⟨objection⟩
> **Response:** We thank the referee. ⟨concede the true part in one sentence⟩. ⟨state the specific guarantee/upgrade/experiment⟩ (see §⟨X⟩). ⟨note that the contribution is the architecture, not a detection⟩.

Load-bearing: **O2, O3, O5, O10** — the originality stands or falls on differentiating from multiverse/blinding (O2/O3), honestly bounding the firewall (O5), and the non-detection stance (O10). Each has a concede-and-defend answer that keeps the architectural novelty intact.
