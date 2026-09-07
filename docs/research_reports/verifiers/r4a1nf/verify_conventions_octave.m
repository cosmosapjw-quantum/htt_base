% Independent GNU Octave checks for Report A R4A1NF conventions.
% This is a numerical smoke test, not an observational or finite-HEALPix run.

format long e;
eta = diag([-1, 1, 1, 1]);
u = [1; 0; 0; 0];
e = [0; 1; 0; 0];
Egamma = 3.0;
c = 2.0;
p = (Egamma / c) * (u + e);

photon_norm = p' * eta * p;
measured_energy_residual = -c * (p' * eta * u) - Egamma;

beta = [0; 0.3; 0; 0];
beta2 = beta' * eta * beta;
gamma = 1 / sqrt(1 - beta2);
utilde = gamma * (u + beta);
boosted_norm_residual = utilde' * eta * utilde + 1;

E1 = [1, 0; 0, 0];
E2 = [0, 1; 1, 0];
r1 = 2.0;
r2 = 0.5;
lambda_reg = 0.25;
Nfam = 2;
GammaE = Nfam * (r1^2 * (E1 * E1') + r2^2 * (E2 * E2')) ...
         + lambda_reg^2 * eye(2);
min_eigenvalue = min(eig(GammaE));

assert(abs(photon_norm) < 1e-13);
assert(abs(measured_energy_residual) < 1e-13);
assert(abs(boosted_norm_residual) < 1e-13);
assert(min_eigenvalue > 0);

printf('photon_norm_residual=%.17e\n', photon_norm);
printf('measured_energy_residual=%.17e\n', measured_energy_residual);
printf('boosted_norm_residual=%.17e\n', boosted_norm_residual);
printf('minimum_GammaE_eigenvalue=%.17e\n', min_eigenvalue);
