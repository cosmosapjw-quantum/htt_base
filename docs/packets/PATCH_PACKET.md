# PATCH PACKET — W6-04 TCA sign correction + verification
## Date: 2026-04-18
## Scope: Post-verification batch fix

---

## §1. Patch summary

This patch applies corrections discovered during **systematic
cross-reference verification** between our W3-W6 implementation and the
project textbook framework document ("low-ℓ tetrad-based Bianchi solver
standard form", 2026-04-18).

### 1.1 Physics fix (P1)

**W6-04 TCA inverse formula — overall sign error**

The module wrote `Γ_T M X = -S` and inverse formulas with overall
negative sign. Correct convention per Pontzen-Challinor 2007 Eq. 5.1 and
Ma-Bertschinger 1995 Eq. 63 is `Γ_T M X = +S`:

```
Θ_2 = +Γ_T⁻¹ [(4/3) S_T − (√6/3) S_E]
E_2 = +Γ_T⁻¹ [−(√6/3) S_T + 3 S_E]
```

Physical check: S_T > 0 (positive shear source) drives Θ_2 > 0
(positive anisotropic stress), matching CAMB's `cmbmain.f90` TCA formula
π_γ ≈ (32/45)κ̇⁻¹(σ + 3q_γ/4) > 0.

### 1.2 Arithmetic typo (P4)

**Roadmap polter-ζ relation — compounded arithmetic error**

```
BEFORE:  polter = (3 I_2 + 27 E_2)/30 = (3/30) ζ
AFTER:   polter = (3 I_2 + 18 E_2)/30 = (2/15) ζ
```

Verification: (2/15) × [(3/4)I_2 + (9/2)E_2] = (1/10)I_2 + (3/5)E_2
matches the literal formula pig/10 + 9 E_2/15 ✓. Code was correct; only
the roadmap comment had the two compounded typos.

---

## §2. Files changed

| File | Change | Lines |
|------|--------|-------|
| `bass/closure/quadrupole_tca.py` | Module header docstring + 2 function signs | ~50 |
| `bass/closure/test_quadrupole_tca.py` | 2 fixtures + 1 comment | ~20 |
| `MASTER_PROMPT_LIST_bass_py.md` | W6-04 spec + W7-02 spec + §18 revision | ~40 |

---

## §3. Why the 52 tests did not catch it

The W6-04 test suite is **self-consistent but sign-blind** for the
tested quantities. A systematic analysis:

| Test | Sign-sensitive? | Reasoning |
|------|-----------------|-----------|
| `test_formula_S_T_only` | Was wrong | Hard-coded the wrong expected value, verifying the wrong formula |
| `test_formula_S_E_only` | Was wrong | Same |
| `test_ratio_sqrt6_over_4` | No | Θ_2 → -Θ_2, E_2 → -E_2 preserves ratio |
| `test_pi_equals_5_over_2_theta` | No | Π → -Π, Θ_2 → -Θ_2 preserves ratio |
| `test_linearity_in_sources` | No | Both sides scale identically |
| `test_scales_inversely_with_gamma` | No | Both sides scale identically |
| `test_agreement_across_source_range` | No | numpy.linalg.solve applied to the wrong-sign system gives the wrong-sign answer consistently |
| `test_subleading_ratio_zero_in_S_E_zero_case` | No | Ratio test |
| `test_matrix_determinant` | No | Matrix structure only |

**Pattern**: The only sign-sensitive assertions (`test_formula_S_T_only`
and `test_formula_S_E_only`) hard-coded the *wrong* expected values.
All other tests are structural or ratio-based.

**Lesson**: For any closed-form inverse, include at least ONE
`assert quantity > 0` or `assert quantity < 0` against an *externally
predictable* physical sign (e.g., "shear makes anisotropic stress
point the same way"). The fixed tests now include these
(`assert theta > 0`, `assert E < 0`) so the bug cannot re-enter.

---

## §4. Verification evidence

### 4.1 Test-suite result post-patch

```
bass/closure/test_quadrupole_tca.py: 52/52 passing
Full regression (bass/ + tsc/):      1,372/1,372 passing
test_ownership_freeze.py:              62/62 passing
Cumulative:                           1,434 total passing
```

### 4.2 Independent physical verification script

A standalone script (not committed, but re-runnable) verified all
physical-sign expectations post-fix:

```
[Test 1: S_T>0, S_E=0, Γ_T>0 → Θ_2>0 (CAMB convention)]
  Θ_2 = +1.333333e-06  POSITIVE ✓
  E_2 = -8.164966e-07  NEGATIVE ✓

[Test 2: Subleading S_E → E_2/Θ_2 = −√6/4, Π = (5/2)Θ_2 (POSITIVE)]
  E_2/Θ_2 = -0.612372  expected -0.612372  ✓
  Π       = +3.333333e-06  POSITIVE ✓

[Test 3: Linearity — S_T<0 should flip all signs]
  Θ_2(-S_T) = -Θ_2(+S_T)  bit-exact ✓

[Test 4: Matrix residual check]
  Γ_T M X |_T = S_T        residual 0 (exact)
  Γ_T M X |_E = S_E        residual 5.29e-20 (machine precision)

[Test 5: Schematic comparison with CAMB (σ=1, Γ_T=1, Σ_2=1)]
  Our Θ_2 = +1.333333 (POSITIVE)
  CAMB π_γ/(σ Σ_2) ∝ +32/45 ≈ +0.711 (POSITIVE)
  Sign agreement ✓
```

---

## §5. Broader verification findings (informational)

The systematic cross-reference also identified items that are NOT
bugs but scheduled design improvements:

### 5.1 API-level: Damping interface ambiguity (W5-A → W7-01)

**Finding B.1/C.1**: W5-A applies uniform Γ across all ℓ; document
§3.3 collision formula requires ℓ=0 to have NO Thomson damping, and
ℓ=2 to have `(9/10)τ̇ + √6/10 τ̇ E_2/Θ_2` rather than simple τ̇. W6-02
adds τ̇ at ℓ=1 on top, creating double-counting risk if callers put
Thomson into the W5-A baseline.

**Resolution (scheduled W7-01)**: Introduce `DampingProfile` spec:
```python
@dataclass(frozen=True)
class DampingProfile:
    hubble_rate: float               # applied to all ℓ
    thomson_rate: float              # ℓ-dependent via collision formula
    ell_weights: dict[int, float]    # per-ℓ overrides (e.g. 9/10 at ℓ=2)
```

**Interim contract**: callers set `W5-A damping_rate = hubble_rate`
only; Thomson enters via `BaryonCoupling` in W6-02 exclusively.

### 5.2 W5-C Wigner normalization (axisymmetric-inert)

**Finding B.2**: `decompose_shear_to_m_channels` lacks Wigner factors
for m=±2. Axisymmetric reductions (s_plus=0) unaffected; full Bianchi I
off-axis requires correction. Scheduled W7+, declared in docstring.

### 5.3 Cosmetic (W12): v_b → v_e rename

**Finding C.2**: `BaryonCoupling.v_b` should be `v_e` for full-tilt
generality. Equal under single-tilt assumption (current scope). Schedule
at W12 tilt PDE integration.

### 5.4 All other items: consistent with document ✓

See §5.4 table of WEEK6_04_PACKET.md companion verification matrix
for the full inventory of 17 items verified consistent.

---

## §6. Score card

```
Patch type:        P1 physics fix + P4 arithmetic typo
Tests passing:     1,434 / 1,434 (unchanged count)
New tests added:   0 (existing tests repurposed with correct expected values)
Physical sign asserts added: 4 (2 in test_formula_S_T_only,
                               2 in test_formula_S_E_only)
Downstream impact: None (W7 not yet implemented; patch lands before
                   any consumer of solve_tca_closure output)
Roadmap version:   v1.1 → v1.2
Status:            VALIDATED
```

---

## §7. Replay protocol

If this sign error had been caught in production (after W7 or W10
consumed the wrong-sign Θ_2), the fix complexity would have been
O(downstream cascade). Current detection at W6-04 leaf means:

1. ✓ No downstream code depends on the sign yet
2. ✓ Fix is 2-line sign flip plus docstring rewrite
3. ✓ Tests immediately re-verify correct physics via the new
   `assert > 0` / `assert < 0` physical sign checks

The "cost of catching this now" is ~100 lines of diff and 1 full
regression run (35s). The "cost of catching this at W10-02 CAMB gate"
would have been debugging wrong D_2 values across the entire forward
spectrum, with blast radius across W7-01, W7-02, W8-03, W10-01.

**Pattern codified**: Every new algebraic inverse formula should be
verified against an externally-known physical sign convention, with
explicit `assert` statements on the sign of at least one output.

---

## §8. Next actions

- W7-01 (E-mode hierarchy + spin-2 streaming): **ready to start**.
  Will consume `combined_source_pi` from W6-04 (now with correct sign).
  W7-01 design notes in v1.2 will drive the `DampingProfile`
  refactoring simultaneously.

- ch05 manuscript retrofit review: still pending (W6-01 Thomson sign
  item from v1.1). Non-blocking.

- Cumulative state unchanged from W6-03 packet (test count, module
  count, Document 12 ceiling progress).

---

**End of PATCH v1.2 packet.**
