# 02A. Hierarchy Layout and Tier-A Transport Note
## state flattening / sparse-block layout / tier-A basis and phase conventions

---

## 0. purpose

이 문서는 codex handoff에서 가장 애매해지기 쉬운 세 항목을 더 강하게 고정한다.

1. tier-B hierarchy state flattening
2. sparse block layout and operator signatures
3. tier-A ray / screen-basis / polarization phase convention

---

## 1. tier-B hierarchy flattening

### 1.1 canonical storage order

Recommended outer-to-inner order:

1. family mode label `mu`
2. species sector
3. polarization/intensity family
4. \(\ell\)
5. \(m\)

### 1.2 sector order

| sector id | content |
|---|---|
| `ph_I` | photon intensity multipoles \(I_{\ell m}\) |
| `ph_E` | photon electric polarization multipoles \(E_{\ell m}\) |
| `ph_B` | photon magnetic polarization multipoles \(B_{\ell m}\) |
| `nu_I` | neutrino intensity multipoles \(N_{\ell m}\) |
| `baryon` | \(\delta_b, v_b, v_e,\) slip and drag auxiliaries |
| `cdm` | \(\delta_c, v_c\) or chosen gauge-equivalent block |
| `src` | source-history auxiliaries |

### 1.3 flattening signature

```text
flatten(mu, sector, ell, m, local_dof=None) -> int
unflatten(index) -> tuple
```

This mapping is part of the public implementation contract.

---

## 2. sparse block architecture

The hierarchy operator is decomposed as

\[
M(\eta)\,U' = A_{\rm fs}U + A_{\rm mix}U + A_{\rm coll}U + S.
\]

- \(A_{\rm fs}\): free streaming / mode recursion
- \(A_{\rm mix}\): anisotropic-background-induced mode mixing
- \(A_{\rm coll}\): collision / TCA-stiff block
- \(S\): explicit source-history injections

### 2.1 mandatory block table

| block | couples | default treatment |
|---|---|---|
| `A_fs_ph` | photon \(I/E/B\) neighboring \(\ell,m\) | explicit |
| `A_fs_nu` | neutrino hierarchy neighboring \(\ell,m\) | explicit |
| `A_mix` | same-\(\mu\) and backend-defined cross-mode couplings | explicit |
| `A_coll_ph` | photon + baryon/electron + TCA auxiliaries | implicit |
| `A_src` | visibility / reionization injection | explicit |
| `M` | mass matrix / identity-like pack | exact as stored |

### 2.2 required operator factory outputs

```text
ModeOps(
    A_fs,
    A_mix,
    A_coll,
    source_template,
    metadata
)
```

### 2.3 family-specific translator layer

Every backend must provide

```text
label_translator(mu_native, ell, m) -> storage labels
inverse_label_translator(storage labels) -> native labels
```

No backend may silently assume the global storage order equals its native representation order.

---

## 3. tier-A ray/basis transport authority note

### 3.1 tier-A state

```text
TierAState(
    eta,
    ray_direction,
    screen_basis,
    phase,
    I_dir,
    P_dir,
    source_history
)
```

### 3.2 phase/sign convention

The package freezes the following rule:

- screen basis \((e_1^a,e_2^a)\) is right-handed with respect to \(e^a\),
- polarization phase is tracked explicitly,
- changing the basis by a sign or handedness flip without updating the phase variable is forbidden.

### 3.3 mandatory tier-A transport signature

```text
ray_rhs(eta, ray_state, bg) -> direction_dot, energy_dot
screen_basis_rhs(eta, ray_state, bg) -> basis_dot, phase_dot
collision_source_tierA(eta, ray_state, bg, electron_frame_data) -> dI_dir, dP_dir
```

### 3.4 implementation rule

Tier-A is exact/reference transport.  
It must not be replaced by “call tier-B and reinterpret output as exact”.

---

## 4. IMEX assembly signatures

```text
assemble_mass_matrix(bg, backend, truncation) -> M
assemble_explicit_block(bg, backend, truncation) -> A_fs_plus_mix
assemble_implicit_block(bg, backend, truncation, opacity_data) -> A_coll
assemble_source_vector(bg, backend, truncation, source_tables) -> S
```

### 4.1 TCA microblock contract
The TCA-implicit microblock must carry, at minimum,
- baryon-electron-photon slip variables,
- photon quadrupole / polarization source auxiliaries,
- opacity-dependent couplings.

---

## 5. hierarchy layout checklist

Before any implementation begins, the developer must freeze:

- `lmax_dev`
- `lmax_prod`
- sector order
- flattening rule
- native-to-storage label translator
- sparse matrix storage format
- truncation closure rule
- which residuals are defined at the chosen cutoff

---

## 6. not-allowed shortcuts

1. no single dense matrix pretending to be backend-generic without a frozen translator layer
2. no sector order chosen ad hoc in notebooks
3. no tier-A “placeholder exactness”
4. no using \(C_\ell\)-oriented storage order to hide lost \(m\)-information
5. no omitting \(B\)-sector placeholders when a later gate will open boost-induced or transport-induced mixing

---

## 7. one-line summary

이 노트의 목적은  
**tier-B hierarchy를 actual storage/operator contract로 고정하고, tier-A ray/basis transport의 sign/phase ambiguity를 제거하여, pseudocode가 실제 skeleton signature로 곧바로 내려가게 하는 것** 이다.
