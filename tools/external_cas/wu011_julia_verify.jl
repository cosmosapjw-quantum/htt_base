#!/usr/bin/env julia

# Independent Julia direct-quadrature verification for PMG-WU-011 Task-7C.
#
# This script reconstructs the continuum wide-mask, identity-transfer,
# first-order local-observer scalar-boost response from source ell=7..12 into
# the weighted joint ell=0..5 fit and retains ell=2..5.  It uses only Julia
# standard libraries and does not read Python, Wolfram, SciPy, or repository
# response matrices.  The calculation is a numerical cross-check, not an
# interval proof or authorization for an empirical beta/Bianchi claim.

using LinearAlgebra
using Printf

const DIRECTION_NAMES = ("X", "Y", "Z", "D111", "D1M11", "D11M1")
const INV_SQRT3 = inv(sqrt(3.0))
const DIRECTIONS = (
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
    (INV_SQRT3, INV_SQRT3, INV_SQRT3),
    (INV_SQRT3, -INV_SQRT3, INV_SQRT3),
    (INV_SQRT3, INV_SQRT3, -INV_SQRT3),
)

function gauss_legendre_nodes(order::Int, lower::Float64, upper::Float64)
    order >= 2 || throw(ArgumentError("quadrature order must be at least two"))
    k = collect(1:(order - 1))
    off_diagonal = k ./ sqrt.(4.0 .* k .^ 2 .- 1.0)
    decomposition = eigen(SymTridiagonal(zeros(order), off_diagonal))
    base_nodes = decomposition.values
    base_weights = 2.0 .* decomposition.vectors[1, :] .^ 2
    nodes = 0.5 .* ((upper - lower) .* base_nodes .+ upper + lower)
    weights = 0.5 .* (upper - lower) .* base_weights
    return nodes, weights
end

function mode_registry(first_ell::Int, last_ell::Int)
    ells = Int[]
    ms = Int[]
    for ell in first_ell:last_ell
        for m in -ell:ell
            push!(ells, ell)
            push!(ms, m)
        end
    end
    return ells, ms
end

function associated_legendre(ell::Int, m::Int, x::Vector{Float64})
    (0 <= m <= ell) || throw(ArgumentError("associated-Legendre indices outside domain"))
    pmm = ones(Float64, length(x))
    if m > 0
        root = sqrt.(max.(0.0, 1.0 .- x .^ 2))
        factor = 1.0
        for _ in 1:m
            pmm .= (-factor) .* root .* pmm
            factor += 2.0
        end
    end
    ell == m && return pmm

    pmmp1 = x .* (2.0 * m + 1.0) .* pmm
    ell == m + 1 && return pmmp1

    previous = pmm
    current = pmmp1
    for degree in (m + 2):ell
        next_value = (
            (2.0 * degree - 1.0) .* x .* current
            .- (degree + m - 1.0) .* previous
        ) ./ (degree - m)
        previous = current
        current = next_value
    end
    return current
end

function factorial_ratio(ell::Int, m::Int)
    m == 0 && return 1.0
    ratio = 1.0
    for value in (ell - m + 1):(ell + m)
        ratio /= value
    end
    return ratio
end

function ylm_positive(
    ell::Int,
    m::Int,
    mu::Vector{Float64},
    phi::Vector{Float64},
)
    p = associated_legendre(ell, m, mu)
    if ell == 0
        dp_dmu = zeros(Float64, length(mu))
    else
        previous = ell - 1 >= m ? associated_legendre(ell - 1, m, mu) : zeros(length(mu))
        dp_dmu = (ell .* mu .* p .- (ell + m) .* previous) ./ (mu .^ 2 .- 1.0)
    end
    normalization = sqrt(((2.0 * ell + 1.0) / (4.0 * pi)) * factorial_ratio(ell, m))
    phase = exp.(im .* m .* phi)
    value = normalization .* p .* phase
    sin_theta = sqrt.(max.(0.0, 1.0 .- mu .^ 2))
    dtheta = normalization .* (-sin_theta .* dp_dmu) .* phase
    dphi = im .* m .* value
    return value, dtheta, dphi
end

function ylm_with_derivatives(
    ell::Int,
    m::Int,
    mu::Vector{Float64},
    phi::Vector{Float64},
)
    if m >= 0
        return ylm_positive(ell, m, mu, phi)
    end
    positive_m = -m
    value, dtheta, dphi = ylm_positive(ell, positive_m, mu, phi)
    phase = isodd(positive_m) ? -1.0 : 1.0
    return phase .* conj.(value), phase .* conj.(dtheta), phase .* conj.(dphi)
end

function expected_sigma_min(direction::NTuple{3, Float64})
    bz = direction[3]
    if abs(bz) > 0.999999999999
        return 0.006905664979696537
    elseif abs(bz) < 1.0e-14
        return 0.010490334912761
    else
        return 0.008510322776380
    end
end

function run_verification(output_directory::String)
    mkpath(output_directory)
    n_mu_piece = 48
    n_phi = 64
    source_cutoff = 12

    mu_middle, weights_middle = gauss_legendre_nodes(n_mu_piece, -0.75, 0.75)
    mu_upper, weights_upper = gauss_legendre_nodes(n_mu_piece, 0.75, 1.0)
    weights_middle .*= 0.5 .+ (2.0 / 3.0) .* mu_middle
    mu = vcat(mu_middle, mu_upper)
    mu_weights = vcat(weights_middle, weights_upper)

    phi = collect(0:(n_phi - 1)) .* (2.0 * pi / n_phi)
    mu_points = repeat(mu, inner=n_phi)
    phi_points = repeat(phi, outer=length(mu))
    weights = repeat(mu_weights, inner=n_phi) .* (2.0 * pi / n_phi)

    fit_ell, fit_m = mode_registry(0, 5)
    source_ell, source_m = mode_registry(7, source_cutoff)
    retained = findall(ell -> ell >= 2, fit_ell)

    point_count = length(mu_points)
    fit_count = length(fit_ell)
    source_count = length(source_ell)
    y_fit = zeros(ComplexF64, point_count, fit_count)
    y_source = zeros(ComplexF64, point_count, source_count)
    dtheta_source = zeros(ComplexF64, point_count, source_count)
    dphi_source = zeros(ComplexF64, point_count, source_count)

    for column in eachindex(fit_ell)
        value, _, _ = ylm_with_derivatives(
            fit_ell[column], fit_m[column], mu_points, phi_points
        )
        y_fit[:, column] = value
    end
    for column in eachindex(source_ell)
        value, dtheta, dphi = ylm_with_derivatives(
            source_ell[column], source_m[column], mu_points, phi_points
        )
        y_source[:, column] = value
        dtheta_source[:, column] = dtheta
        dphi_source[:, column] = dphi
    end

    weighted_fit = reshape(weights, :, 1) .* y_fit
    normal = adjoint(y_fit) * weighted_fit
    hermitian_residual = norm(normal - adjoint(normal)) / norm(normal)
    hermitian_residual <= 2.0e-13 || error("Julia continuum normal matrix is not Hermitian enough")

    sin_theta = sqrt.(max.(0.0, 1.0 .- mu_points .^ 2))
    cos_phi = cos.(phi_points)
    sin_phi = sin.(phi_points)

    output_path = joinpath(output_directory, "julia_continuum_l12.csv")
    open(output_path, "w") do io
        println(
            io,
            "direction,rank,sigma_max,sigma_min,condition,expected_sigma_min,relative_residual,normal_hermitian_residual",
        )
        for (name, direction) in zip(DIRECTION_NAMES, DIRECTIONS)
            bx, by, bz = direction
            b_dot_n = bx .* sin_theta .* cos_phi .+ by .* sin_theta .* sin_phi .+ bz .* mu_points
            b_theta = bx .* mu_points .* cos_phi .+ by .* mu_points .* sin_phi .- bz .* sin_theta
            b_phi = -bx .* sin_phi .+ by .* cos_phi

            generator = (
                reshape(b_dot_n, :, 1) .* y_source
                .- reshape(b_theta, :, 1) .* dtheta_source
                .- reshape(b_phi ./ sin_theta, :, 1) .* dphi_source
            )
            rhs = adjoint(y_fit) * (reshape(weights, :, 1) .* generator)
            fitted = normal \ rhs
            response = fitted[retained, :]
            singular_values = svdvals(response)
            rank_value = count(value -> value > 1.0e-10 * singular_values[1], singular_values)
            sigma_max = singular_values[1]
            sigma_min = singular_values[end]
            condition_value = sigma_max / sigma_min
            expected = expected_sigma_min(direction)
            relative_residual = abs(sigma_min - expected) / expected

            rank_value == 32 || error("Julia continuum response is not full row rank for $name")
            relative_residual <= 5.0e-8 || error("Julia sigma_min differs from frozen reference for $name")

            @printf(
                io,
                "%s,%d,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g\n",
                name,
                rank_value,
                sigma_max,
                sigma_min,
                condition_value,
                expected,
                relative_residual,
                hermitian_residual,
            )
            @printf(
                "Julia continuum %s: rank=%d sigma_min=%.17g condition=%.12g\n",
                name,
                rank_value,
                sigma_min,
                condition_value,
            )
        end
    end

    open(joinpath(output_directory, "julia_status.txt"), "w") do io
        println(io, "PASS_JULIA_WIDE_MASK_L12_ALL_SIX_FULL_ROW_RANK")
    end
end

output_directory = length(ARGS) >= 1 ? ARGS[1] : "external_cas_results"
run_verification(output_directory)
