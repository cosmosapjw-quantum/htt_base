// Boltzmann hierarchy coupling coefficients.

pub(crate) fn bp_shear_coupling_down(ell: usize) -> f64 {
    if ell < 2 { 0.0 } else { (ell as f64) * ((ell - 1) as f64) / (((2 * ell - 1) as f64) * ((2 * ell + 1) as f64)) }
}

pub(crate) fn bp_shear_coupling_up(ell: usize) -> f64 {
    ((ell + 1) as f64) * ((ell + 2) as f64) / (((2 * ell + 1) as f64) * ((2 * ell + 3) as f64))
}

pub(crate) fn bp_streaming_coupling_down(ell: usize) -> f64 {
    if ell < 1 { 0.0 } else { (ell as f64) / ((2 * ell + 1) as f64) }
}

pub(crate) fn bp_streaming_coupling_up(ell: usize) -> f64 {
    ((ell + 1) as f64) / ((2 * ell + 1) as f64)
}

pub(crate) fn bp_advection_coefficient(m: i32, ell: usize, ell_prime: usize, sqrt_h: f64, delta_n: f64) -> (f64, f64) {
    let m_f = m as f64;
    if ell_prime + 1 == ell {
        if ell < 1 { return (0.0, 0.0); }
        let geom = (((ell * ell) as f64 - m_f * m_f) / (((2 * ell - 1) as f64) * ((2 * ell + 1) as f64))).max(0.0).sqrt();
        let phase_re = ((ell - 1) as f64) * sqrt_h;
        let phase_im = m_f * delta_n;
        (geom * phase_re, geom * phase_im)
    } else if ell_prime == ell + 1 {
        let geom = ((((ell + 1) * (ell + 1)) as f64 - m_f * m_f) / (((2 * ell + 1) as f64) * ((2 * ell + 3) as f64))).max(0.0).sqrt();
        let phase_re = -((ell + 2) as f64) * sqrt_h;
        let phase_im = m_f * delta_n;
        (geom * phase_re, geom * phase_im)
    } else {
        (0.0, 0.0)
    }
}

pub(crate) fn bp_apply_damping(mat: &mut [f64], n_complex: usize, ell_max: usize, abs_m: usize, alpha_damp: f64, n_damp: usize) {
    if n_damp == 0 || alpha_damp == 0.0 { return; }
    let ell_d = ell_max.saturating_sub(n_damp);
    for i in 0..n_complex.saturating_sub(1) {
        let ell = abs_m + i;
        if ell > ell_d {
            let denom = (ell_max.saturating_sub(ell_d)).max(1) as f64;
            let frac = (ell.saturating_sub(ell_d)) as f64 / denom;
            add_real_block_entry(mat, n_complex, i, i, -alpha_damp * frac * frac, 0.0);
        }
    }
}



pub(crate) fn set_real_block_entry(mat: &mut [f64], n_complex: usize, i: usize, j: usize, re: f64, im: f64) {
    let n_real = 2 * n_complex;
    let idx = |r: usize, c: usize| -> usize { r * n_real + c };
    mat[idx(i, j)] = re;
    mat[idx(i, j + n_complex)] = -im;
    mat[idx(i + n_complex, j)] = im;
    mat[idx(i + n_complex, j + n_complex)] = re;
}

pub(crate) fn add_real_block_entry(mat: &mut [f64], n_complex: usize, i: usize, j: usize, re: f64, im: f64) {
    let n_real = 2 * n_complex;
    let idx = |r: usize, c: usize| -> usize { r * n_real + c };
    mat[idx(i, j)] += re;
    mat[idx(i, j + n_complex)] += -im;
    mat[idx(i + n_complex, j)] += im;
    mat[idx(i + n_complex, j + n_complex)] += re;
}
