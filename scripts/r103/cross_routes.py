"""Compute conditional bounds from the signed, source-identified R78 summaries."""
import math

import numpy as np


def cross_routes(dag):
    records = {n['id']: n['observable_evidence'] for n in dag['nodes']
               if n.get('node_class') == 'physical_cross_route'}
    results = {}

    # In the Frobenius metric, the matched-filter window W is the Riesz
    # representative of S -> Tr(SW) on the traceless symmetric tensors.
    first = records['PHY-01']
    w = np.array(first['mask_quadrupole_window_difference_eigenvalues'])
    w -= w.mean()
    strength = first['TypeV_shear_eigen_amplitude']
    zero_flux = strength * np.ptp(w)
    unrestricted = math.sqrt(2) * strength * np.linalg.norm(w)
    results['PHY-01'] = {
        'source': first['source'], 'source_groups': first['selected_n'],
        'shear_frobenius_radius': math.sqrt(2) * strength,
        'free_stf_optimal_leakage': float(unrestricted),
        'fixed_zero_flux_shape_optimal_leakage': float(zero_flux),
        'shape_efficiency': float(zero_flux / unrestricted),
    }

    # Projection of the photon moment spectrahedron onto f: P - f f^T >= 0.
    # The ellipsoid's principal radii are sqrt(lambda_i(P)).
    second = records['PHY-02']['R66_same_sky_finiteband_photon_pressure']
    results['PHY-02'] = {}
    for release, source in second.items():
        eig = np.array(source['P_eigenvalues'])
        radii = np.sqrt(eig)
        results['PHY-02'][release] = {
            'max_normalized_photon_flux': float(max(radii)),
            'min_directional_radius': float(min(radii)),
            'fractional_radius_spread': float(np.ptp(radii) / min(radii)),
            'source_frame_flux_observed': source['same_frame_flux_observed'],
        }

    # At unit Frobenius norm, normalized positive uniaxial STF templates
    # U(n)=(3nn^T-I)/sqrt(6) attain max <S,U>=sqrt(3/2)*lambda_max(S).
    # The cubic for S gives this cosine as cos(arccos(chi)/3).
    third = records['PHY-03']['actual_R66_finiteband_stress']
    results['PHY-03'] = {}
    for release, source in third.items():
        chi = source['R66_signed_chi_finiteband']
        angle = math.acos(chi) / 3
        results['PHY-03'][release] = {
            'source_signed_chi': chi, 'positive_uniaxial_max_cosine': math.cos(angle),
            'best_amplitude_axis_relative_residual': math.sin(angle),
        }

    # For whitened E and B blocks with singular correlation rho, the
    # conditional information in that E direction is 1-rho**2.
    fourth = records['PHY-04']
    results['PHY-04'] = {}
    for sky in ('quality', 'north', 'south'):
        rho = fourth[f'R69_actual_Gaia_{sky}_EB2_maxFisherCanonical']
        results['PHY-04'][sky] = {
            'canonical_correlation': rho,
            'worst_remaining_information_fraction_after_B_profile': 1-rho**2,
            'worst_formal_variance_inflation': 1/(1-rho**2),
        }

    fifth = records['PHY-05']
    matrix = np.asarray(fifth['exceptional_M_signed_STF5_to_u'], dtype=float)
    normal = np.asarray(fifth['exceptional_left_normal_flux_constraint'], dtype=float)
    normal /= np.linalg.norm(normal)
    singular = np.linalg.svd(matrix, compute_uv=False)
    results['PHY-05'] = {
        'left_null_normalized': normal.tolist(),
        'shear_jacobian_left_null_residual': float(np.linalg.norm(normal @ matrix)),
        'observable_coordinate_singular_values': singular[:2].tolist(),
        'condition_on_image_in_saved_coordinates': float(singular[0] / singular[1]),
        'independent_normal_flux_observed': fifth['actual_independent_normal_j_source'],
    }

    # Two physical distributions have identical input moments and different
    # output. Every deterministic estimator of that output from those inputs
    # takes the same value on both, hence L_infty risk >= half the separation.
    pair = list(records['PHY-06']['photon_nonclosed_smooth_positive_sky_cases'].values())
    if len(pair) != 2 or not all(s['same_initial_f_and_STF5_zero'] for s in pair):
        raise ValueError('PHY-06 requires the two equal-input closure witnesses')
    results['PHY-06'] = {
        label: abs(pair[0][key] - pair[1][key])/2
        for label, key in [('minimax_cap_absolute_error_lower_bound', 'actual_kinetic_synthetic_cap_F'),
                           ('minimax_stress_rate_absolute_error_lower_bound', 'instantaneous_dS_gamma_zz')]
    }

    # x and u=(r0/r)x use the same positive-weight sky-direction column.
    # The Kantorovich inequality gives corr(x,u)>=2*sqrt(a*b)/(a+b)
    # for the uncentered weighted cosine and r in [a,b].
    results['PHY-07'] = {}
    for shell, source in records['PHY-07']['CF4_full_group_geometric_radial_leverage'].items():
        a, b = map(float, shell.split('-'))
        rho = 2 * math.sqrt(a*b) / (a+b)
        floor = (math.sqrt(b) + math.sqrt(a)) / (math.sqrt(b) - math.sqrt(a))
        measured = source['column_normalized_condition']
        if measured < floor * (1-1e-11):
            raise ValueError(f'PHY-07 shell {shell}: recorded condition below its lower bound')
        results['PHY-07'][shell] = {
            'groups': source['actual_unweighted_CF4_table4_n'],
            'uncentered_dipole_column_cosine_lower_bound': rho,
            'normalized_design_condition_lower_bound': floor,
            'source_measured_condition': measured,
        }
    return results
