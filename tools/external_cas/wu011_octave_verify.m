function wu011_octave_verify(output_dir)
  % Independent GNU Octave direct-quadrature verification for PMG-WU-011.
  %
  % The script reconstructs the continuum wide-mask, identity-transfer,
  % first-order boost response from source ell=7..12 into a weighted joint
  % ell=0..5 fit, then retains ell=2..5.  It uses no Python or repository
  % response matrices.  The complex harmonic representation is the
  % complexification of the scientific stored-real carrier, so its singular
  % values and row rank agree with the metric-whitened stored-real operator.
  %
  % This is an external numerical cross-check, not a formal interval proof and
  % not authorization for an empirical beta or Bianchi attribution.

  if nargin < 1
    output_dir = "external_cas_results";
  endif
  if exist(output_dir, "dir") ~= 7
    mkdir(output_dir);
  endif

  n_mu_piece = 48;
  n_phi = 64;
  source_cutoff = 12;

  [mu_mid, w_mid] = gl_nodes(n_mu_piece, -0.75, 0.75);
  [mu_top, w_top] = gl_nodes(n_mu_piece, 0.75, 1.0);
  w_mid = w_mid .* (0.5 + (2.0 / 3.0) .* mu_mid);
  mu = [mu_mid; mu_top];
  w_mu = [w_mid; w_top];

  phi = (0:(n_phi - 1))' .* (2.0 * pi / n_phi);
  n_mu = length(mu);
  mu_points = kron(mu, ones(n_phi, 1));
  phi_points = repmat(phi, n_mu, 1);
  weights = kron(w_mu, ones(n_phi, 1) .* (2.0 * pi / n_phi));

  [fit_l, fit_m] = mode_registry(0, 5);
  [src_l, src_m] = mode_registry(7, source_cutoff);
  retained = find(fit_l >= 2);

  n_points = length(mu_points);
  n_fit = length(fit_l);
  n_src = length(src_l);
  y_fit = complex(zeros(n_points, n_fit));
  y_src = complex(zeros(n_points, n_src));
  dtheta_src = complex(zeros(n_points, n_src));
  dphi_src = complex(zeros(n_points, n_src));

  for column = 1:n_fit
    [value, ~, ~] = ylm_with_derivatives(
      fit_l(column), fit_m(column), mu_points, phi_points
    );
    y_fit(:, column) = value;
  endfor
  for column = 1:n_src
    [value, dtheta, dphi] = ylm_with_derivatives(
      src_l(column), src_m(column), mu_points, phi_points
    );
    y_src(:, column) = value;
    dtheta_src(:, column) = dtheta;
    dphi_src(:, column) = dphi;
  endfor

  normal = y_fit' * bsxfun(@times, weights, y_fit);
  hermitian_residual = norm(normal - normal', "fro") / norm(normal, "fro");
  if hermitian_residual > 2.0e-13
    error("Octave continuum normal matrix is not Hermitian enough");
  endif

  sin_theta = sqrt(max(0.0, 1.0 - mu_points .^ 2));
  cos_phi = cos(phi_points);
  sin_phi = sin(phi_points);

  direction_names = {"X", "Y", "Z", "D111", "D1M11", "D11M1"};
  directions = [
    1.0, 0.0, 0.0;
    0.0, 1.0, 0.0;
    0.0, 0.0, 1.0;
    1.0 / sqrt(3.0), 1.0 / sqrt(3.0), 1.0 / sqrt(3.0);
    1.0 / sqrt(3.0), -1.0 / sqrt(3.0), 1.0 / sqrt(3.0);
    1.0 / sqrt(3.0), 1.0 / sqrt(3.0), -1.0 / sqrt(3.0)
  ];

  output_path = fullfile(output_dir, "octave_continuum_l12.csv");
  fid = fopen(output_path, "w");
  if fid < 0
    error("could not open Octave output file");
  endif
  fprintf(fid, [
    "direction,rank,sigma_max,sigma_min,condition,expected_sigma_min,", ...
    "relative_residual,normal_hermitian_residual\n"
  ]);

  for direction_index = 1:rows(directions)
    b = directions(direction_index, :);
    bdotn = (
      b(1) .* sin_theta .* cos_phi
      + b(2) .* sin_theta .* sin_phi
      + b(3) .* mu_points
    );
    btheta = (
      b(1) .* mu_points .* cos_phi
      + b(2) .* mu_points .* sin_phi
      - b(3) .* sin_theta
    );
    bphi = -b(1) .* sin_phi + b(2) .* cos_phi;

    generator = (
      bsxfun(@times, bdotn, y_src)
      - bsxfun(@times, btheta, dtheta_src)
      - bsxfun(@times, bphi ./ sin_theta, dphi_src)
    );
    rhs = y_fit' * bsxfun(@times, weights, generator);
    fitted = normal \ rhs;
    response = fitted(retained, :);
    singular_values = svd(response);
    rank_value = sum(singular_values > 1.0e-10 * singular_values(1));
    sigma_max = singular_values(1);
    sigma_min = singular_values(end);
    condition_value = sigma_max / sigma_min;

    if abs(b(3)) > 0.999999999999
      expected = 0.006905664979696537;
    elseif abs(b(3)) < 1.0e-14
      expected = 0.010490334912761;
    else
      expected = 0.008510322776380;
    endif
    relative_residual = abs(sigma_min - expected) / expected;

    if rank_value ~= 32
      error("Octave continuum response is not full row rank");
    endif
    if relative_residual > 5.0e-8
      error("Octave continuum sigma_min differs from the frozen reference");
    endif

    fprintf(
      fid,
      "%s,%d,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g\n",
      direction_names{direction_index}, rank_value, sigma_max, sigma_min,
      condition_value, expected, relative_residual, hermitian_residual
    );
    fprintf(
      "Octave continuum %s: rank=%d sigma_min=%.17g condition=%.12g\n",
      direction_names{direction_index}, rank_value, sigma_min, condition_value
    );
  endfor

  fclose(fid);
  status_path = fullfile(output_dir, "octave_status.txt");
  fid = fopen(status_path, "w");
  fprintf(fid, "PASS_OCTAVE_WIDE_MASK_L12_ALL_SIX_FULL_ROW_RANK\n");
  fclose(fid);
endfunction

function [nodes, weights] = gl_nodes(order, lower, upper)
  k = (1:(order - 1))';
  off_diagonal = k ./ sqrt(4.0 .* k .^ 2 - 1.0);
  jacobi = diag(off_diagonal, 1) + diag(off_diagonal, -1);
  [vectors, diagonal] = eig(jacobi);
  [base_nodes, permutation] = sort(diag(diagonal));
  base_weights = 2.0 .* (vectors(1, permutation)').^2;
  nodes = 0.5 .* ((upper - lower) .* base_nodes + upper + lower);
  weights = 0.5 .* (upper - lower) .* base_weights;
endfunction

function [ells, ms] = mode_registry(first_ell, last_ell)
  ells = [];
  ms = [];
  for ell = first_ell:last_ell
    for m = -ell:ell
      ells(end + 1, 1) = ell;
      ms(end + 1, 1) = m;
    endfor
  endfor
endfunction

function value = associated_legendre_scalar(ell, m, x)
  if m < 0 || ell < m
    error("associated Legendre indices outside domain");
  endif
  pmm = ones(size(x));
  if m > 0
    root = sqrt(max(0.0, 1.0 - x .^ 2));
    factor = 1.0;
    for index = 1:m
      pmm = -factor .* root .* pmm;
      factor = factor + 2.0;
    endfor
  endif
  if ell == m
    value = pmm;
    return;
  endif
  pmmp1 = x .* (2.0 * m + 1.0) .* pmm;
  if ell == m + 1
    value = pmmp1;
    return;
  endif
  previous = pmm;
  current = pmmp1;
  for degree = (m + 2):ell
    next = (
      (2.0 * degree - 1.0) .* x .* current
      - (degree + m - 1.0) .* previous
    ) ./ (degree - m);
    previous = current;
    current = next;
  endfor
  value = current;
endfunction

function ratio = factorial_ratio(ell, m)
  ratio = 1.0;
  if m == 0
    return;
  endif
  for value = (ell - m + 1):(ell + m)
    ratio = ratio / value;
  endfor
endfunction

function [value, dtheta, dphi] = ylm_positive(
  ell, m, mu, phi
)
  p = associated_legendre_scalar(ell, m, mu);
  if ell == 0
    dp_dmu = zeros(size(mu));
  else
    if ell - 1 >= m
      previous = associated_legendre_scalar(ell - 1, m, mu);
    else
      previous = zeros(size(mu));
    endif
    dp_dmu = (
      ell .* mu .* p - (ell + m) .* previous
    ) ./ (mu .^ 2 - 1.0);
  endif
  normalization = sqrt(
    ((2.0 * ell + 1.0) / (4.0 * pi)) * factorial_ratio(ell, m)
  );
  phase = exp(1i .* m .* phi);
  value = normalization .* p .* phase;
  dtheta = normalization .* (
    -sqrt(max(0.0, 1.0 - mu .^ 2)) .* dp_dmu
  ) .* phase;
  dphi = 1i .* m .* value;
endfunction

function [value, dtheta, dphi] = ylm_with_derivatives(
  ell, m, mu, phi
)
  if m >= 0
    [value, dtheta, dphi] = ylm_positive(ell, m, mu, phi);
    return;
  endif
  positive_m = -m;
  [positive_value, positive_dtheta, positive_dphi] = ylm_positive(
    ell, positive_m, mu, phi
  );
  phase = (-1) ^ positive_m;
  value = phase .* conj(positive_value);
  dtheta = phase .* conj(positive_dtheta);
  dphi = phase .* conj(positive_dphi);
endfunction
