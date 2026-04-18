// Boost cascade: Lorentz boost of temperature multipoles.
// BB-05: From Paper I, Theorem 6 (P-I.T6).
//
// Under a boost v_a, the PSTF multipoles transform:
//   T̃_a = T_a + v_a − (4/5)T_{ab}v^b + O(v²)
//   T̃_{ab} = T_{ab} + 2v_{⟨a}T_{b⟩} + v_{⟨a}v_{b⟩} + O(v³)
//
// Key property: L ≤ 2 input → L ≤ 3 output after boost.

/// Boost the dipole T_a by velocity v_a.
///
/// T̃_a = T_a + v_a − (4/5)T_{ab}v^b + O(v²)
///
/// `t_a`: input dipole [3]
/// `t_ab`: input quadrupole (symmetric trace-free, 5 independent) stored as [3][3]
/// `v_a`: boost velocity [3]
///
/// Returns boosted dipole [3].
pub(crate) fn boost_dipole(
    t_a: &[f64; 3],
    t_ab: &[[f64; 3]; 3],
    v_a: &[f64; 3],
) -> [f64; 3] {
    let mut result = [0.0; 3];
    for i in 0..3 {
        let mut tab_v = 0.0;
        for j in 0..3 {
            tab_v += t_ab[i][j] * v_a[j];
        }
        result[i] = t_a[i] + v_a[i] - (4.0/5.0) * tab_v;
    }
    result
}

/// Boost the quadrupole T_{ab} by velocity v_a.
///
/// T̃_{ab} = T_{ab} + 2v_{⟨a}T_{b⟩} + v_{⟨a}v_{b⟩} + O(v³)
///
/// The ⟨⟩ denotes the symmetric trace-free projection.
///
/// Returns boosted quadrupole [3][3] (symmetric, trace-free).
pub(crate) fn boost_quadrupole(
    t_ab: &[[f64; 3]; 3],
    t_a: &[f64; 3],
    v_a: &[f64; 3],
) -> [[f64; 3]; 3] {
    let mut result = [[0.0; 3]; 3];

    // T_{ab} + 2v_{⟨a}T_{b⟩} + v_{⟨a}v_{b⟩}
    for i in 0..3 {
        for j in 0..3 {
            result[i][j] = t_ab[i][j]
                + v_a[i] * t_a[j] + v_a[j] * t_a[i]  // 2v_{(a}T_{b)}
                + v_a[i] * v_a[j];                      // v_a v_b
        }
    }

    // Project to STF: remove trace
    let tr = result[0][0] + result[1][1] + result[2][2];
    for i in 0..3 {
        result[i][i] -= tr / 3.0;
    }
    result
}

/// Induced octupole from boost (L=2 → L=3 leakage).
///
/// A boost of a pure quadrupole generates an octupole contribution
/// of order O(v × T_{ab}). The exact form involves the STF projection
/// of v_{⟨a}T_{bc⟩}.
///
/// Returns nonzero if input has L=2 and boost is nonzero.
pub(crate) fn boost_induces_octupole(t_ab_norm: f64, v_norm: f64) -> f64 {
    // Order-of-magnitude: |T̃_{abc}| ~ v × |T_{ab}|
    v_norm * t_ab_norm
}

/// Count maximum output multipole after boosting input up to L_max.
///
/// Key property: L input → L+1 output (one ℓ leakage per boost order).
pub(crate) fn max_output_ell(l_max_input: usize, boost_order: usize) -> usize {
    l_max_input + boost_order
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_zero_boost_identity() {
        let t_a = [1.0, 2.0, 3.0];
        let t_ab = [[0.1, 0.0, 0.0], [0.0, -0.05, 0.0], [0.0, 0.0, -0.05]];
        let v = [0.0; 3];
        let boosted = boost_dipole(&t_a, &t_ab, &v);
        for i in 0..3 {
            assert!((boosted[i] - t_a[i]).abs() < 1e-15);
        }
    }

    #[test]
    fn test_boost_adds_velocity_to_dipole() {
        // Pure monopole + boost: T̃_a = v_a (dipole from boost)
        let t_a = [0.0; 3];
        let t_ab = [[0.0; 3]; 3];
        let v = [0.001, 0.0, 0.0];
        let boosted = boost_dipole(&t_a, &t_ab, &v);
        assert!((boosted[0] - 0.001).abs() < 1e-15);
    }

    #[test]
    fn test_l2_to_l3_leakage() {
        // L=2 input → L=3 output after first-order boost
        assert_eq!(max_output_ell(2, 1), 3);
        // L=2 → L=4 after second-order boost
        assert_eq!(max_output_ell(2, 2), 4);
    }

    #[test]
    fn test_octupole_induction_nonzero() {
        // Nonzero quadrupole + nonzero boost → nonzero octupole
        let oct = boost_induces_octupole(1e-5, 1e-3);
        assert!(oct > 0.0);
        assert!(oct < 1e-7); // O(v × T)
    }

    #[test]
    fn test_boosted_quadrupole_tracefree() {
        let t_ab = [[0.1, 0.02, 0.0], [0.02, -0.05, 0.01], [0.0, 0.01, -0.05]];
        let t_a = [0.01, 0.0, 0.0];
        let v = [0.001, 0.0005, 0.0];
        let boosted = boost_quadrupole(&t_ab, &t_a, &v);
        let tr = boosted[0][0] + boosted[1][1] + boosted[2][2];
        assert!(tr.abs() < 1e-14, "Boosted quadrupole trace: {:.2e}", tr);
    }
}
