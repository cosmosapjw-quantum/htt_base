// Mathematical utilities.

pub(crate) fn clip(x: f64, lo: f64, hi: f64) -> f64 {
    x.max(lo).min(hi)
}

pub(crate) fn gradient_abs_nonuniform(x: &[f64], y: &[f64]) -> Vec<f64> {
    let n = x.len();
    if n == 0 { return Vec::new(); }
    if n == 1 { return vec![0.0]; }
    let mut g = vec![0.0; n];
    g[0] = ((y[1] - y[0]) / (x[1] - x[0]).abs().max(1e-30)).abs();
    for i in 1..(n - 1) { g[i] = ((y[i + 1] - y[i - 1]) / (x[i + 1] - x[i - 1]).abs().max(1e-30)).abs(); }
    g[n - 1] = ((y[n - 1] - y[n - 2]) / (x[n - 1] - x[n - 2]).abs().max(1e-30)).abs();
    g
}

pub(crate) fn natural_cubic_second_derivatives(x: &[f64], y: &[f64]) -> Result<Vec<f64>, String> {
    let n = x.len();
    if y.len() != n { return Err("x and y must have matching lengths".to_string()); }
    if n < 2 { return Ok(vec![0.0; n]); }
    let mut u = vec![0.0; n - 1];
    let mut y2 = vec![0.0; n];
    y2[0] = 0.0; u[0] = 0.0;
    for i in 1..(n - 1) {
        let h_im1 = x[i] - x[i - 1]; let h_i = x[i + 1] - x[i];
        if h_im1 <= 0.0 || h_i <= 0.0 { return Err("x grid must be strictly increasing for cubic spline calibration".to_string()); }
        let sig = h_im1 / (h_im1 + h_i); let p = sig * y2[i - 1] + 2.0;
        y2[i] = (sig - 1.0) / p;
        let ddydx = (y[i + 1] - y[i]) / h_i - (y[i] - y[i - 1]) / h_im1;
        u[i] = (6.0 * ddydx / (h_im1 + h_i) - sig * u[i - 1]) / p;
    }
    y2[n - 1] = 0.0;
    for k in (0..(n - 1)).rev() { y2[k] = y2[k] * y2[k + 1] + u[k]; }
    Ok(y2)
}

pub(crate) fn cubic_spline_eval(x: &[f64], y: &[f64], y2: &[f64], xp: f64) -> f64 {
    let n = x.len();
    if n == 0 { return 0.0; }
    if n == 1 { return y[0]; }
    let xp_clamped = clip(xp, x[0], x[n - 1]);
    let mut klo = 0usize; let mut khi = n - 1;
    while khi - klo > 1 { let k = (khi + klo) >> 1; if x[k] > xp_clamped { khi = k; } else { klo = k; } }
    let h = (x[khi] - x[klo]).abs().max(1e-30);
    let a = (x[khi] - xp_clamped) / h; let b = (xp_clamped - x[klo]) / h;
    a * y[klo] + b * y[khi] + ((a*a*a-a)*y2[klo] + (b*b*b-b)*y2[khi]) * h*h / 6.0
}

pub(crate) fn solve_positive_root(a: f64, b: f64, c: f64) -> f64 {
    if a.abs() < 1e-30 {
        if b.abs() < 1e-30 {
            return 0.0;
        }
        return (-(c / b)).max(0.0);
    }
    let disc = (b * b - 4.0 * a * c).max(0.0);
    ((-b + disc.sqrt()) / (2.0 * a)).max(0.0)
}

