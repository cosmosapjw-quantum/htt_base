// SPDX-License-Identifier: GPL-3.0-or-later
// CORAS survey setup follows Lilow & Nusser, upstream commit 45ab25635.
// Build independently of htt_base; see coras_build.py. Run with cwd=CORAS.
#include "configuration.hpp"
#include "src/ConstrainedRealizations.hpp"
#include "src/FileTable.hpp"
#include "src/NormalizedPowerSpectrum.hpp"
#include "src/survey.hpp"
#include <fftw3.h>
#include <omp.h>
#include <array>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <vector>

struct Site { long long id; double radius, theta, phi; };

int main(int argc, char **argv) {
    if (argc != 9) {
        std::cerr << "usage: coras_radial sites output_dir first last radial_resolution ell_max fft_bins smooth_Mpch\n";
        return 2;
    }
    const std::string dest = std::string(argv[2]) + "/";
    const int first = std::stoi(argv[3]), last = std::stoi(argv[4]);
    const int resolution = std::stoi(argv[5]), ell = std::stoi(argv[6]), fft = std::stoi(argv[7]);
    const double smooth = std::stod(argv[8]);
    if (first < 1 || last < first || ell < 1 || resolution <= ell + 3 || fft < 8 || !(smooth >= 1.0)) return 2;
    std::ifstream input(argv[1]);
    Site s;
    std::vector<Site> sites;
    while (input >> s.id >> s.radius >> s.theta >> s.phi) {
        if (!(s.radius > 0 && s.radius <= 200 && s.theta >= 0 && s.theta <= M_PI &&
              s.phi >= 0 && s.phi < 2*M_PI)) return 2;
        sites.push_back(s);
    }
    if (!input.eof() || sites.empty()) return 2;
    fftw_init_threads();
    fftw_plan_with_nthreads(omp_get_max_threads());
    const FileTable power(FIDUCIAL_POWER_SPECTRUM_FILE_NAME,2);
    NormalizedPowerSpectrum spectrum(power.column<double>(0),power.column<double>(1),FIDUCIAL_HUBBLE,SIGMA_SCALE);
    const FileTable galaxies(REDSHIFT_CATALOG_FILE_NAME,10,'\t');
    const auto redshift=galaxies.column<double>(9), helio=galaxies.column<double>(3);
    const auto lat=galaxies.column<double>(1), lon=galaxies.column<double>(2), mag=galaxies.column<double>(4);
    std::vector<double> z,kz,r,theta,phi,ks;
    prepare_2MRS_data(redshift,helio,lat,lon,mag,get_reference_frame_change(HELIOCENTRIC_FRAME,CMB_FRAME),
        RECONSTRUCTION_MAX_RADIUS,REDSHIFT_CATALOG_VOLUME_LIMIT_RADIUS,REDSHIFT_CATALOG_MAX_APPARENT_MAGNITUDE,
        FIDUCIAL_OMEGA_MATTER,luminosity_evolution_correction_2MRS,k_correction_2MRS,z,kz,r,theta,phi,ks);
    Cartesian1DGridFunction sigma, selection, derivative, radial_distribution;
    std::vector<std::size_t> counts;
    estimate_sigma_galaxy(z,kz,theta,phi,ks,REDSHIFT_CATALOG_VOLUME_LIMIT_RADIUS,RECONSTRUCTION_MAX_RADIUS,
        SIGMA_GALAXY_RADIAL_BIN_NUMBER,REDSHIFT_CATALOG_MAX_APPARENT_MAGNITUDE,FIDUCIAL_OMEGA_MATTER,
        SIGMA_SCALE,luminosity_evolution_correction_2MRS,k_correction_2MRS,sigma,counts);
    auto galaxy_sigma=[&](double x){return x<sigma.coordinate(0) ? sigma.value(0) : sigma(x);};
    estimate_selection_function(z,kz,ks,REDSHIFT_CATALOG_MAX_APPARENT_MAGNITUDE,RECONSTRUCTION_MAX_RADIUS,
        SELECTION_FUNCTION_BIN_NUMBER,FIDUCIAL_OMEGA_MATTER,luminosity_evolution_correction_2MRS,k_correction_2MRS,
        selection,derivative,radial_distribution);
    const double density=estimate_mean_density(RECONSTRUCTION_MAX_RADIUS,r,selection);
    // Resolution in kr, angular harmonics, output sampling, then FFT input bins as in the donor API.
    ConstrainedRealizations flow(r,theta,phi,CMB_FRAME,RECONSTRUCTION_MAX_RADIUS,resolution,ell,
        std::max(25,resolution),std::max(17,2*ell+1),std::max(32,4*ell),
        RECONSTRUCTION_FFT_PERIODIC_BOUNDARY_DISTANCE,fft,RECONSTRUCTION_LOG_TRAFO_SMOOTHING_SCALE,
        density,selection,derivative,galaxy_sigma,spectrum,dest,"_private",false);
    auto mean=flow.get_survey_estimate_radial_velocity(ESTIMATED_NORMALIZED_GROWTH_RATE,smooth);
    std::cout << "2MRS input=" << redshift.size() << " selected=" << r.size() << " sites=" << sites.size() << std::endl;
    for(int seed=first-1;seed<=last;++seed){
        const bool expectation=(seed==first-1);
        // Write conditional mean once and centered random-signal minus mock-estimate for each seed.
        auto field=mean;
        if(!expectation){
            flow.generate(seed);
            field=flow.get_noise_radial_velocity(ESTIMATED_NORMALIZED_GROWTH_RATE,smooth);
        }
        const std::string file=dest+(expectation?"mean":("residual_"+std::to_string(seed)))+".tsv";
        std::ofstream out(file);
        out << std::setprecision(14);
        for(const auto &site:sites){
            double vr=field(site.radius,site.theta,site.phi);
            if(expectation){
                const double st=std::sin(site.theta);
                vr += st*(ESTIMATED_EXTERNAL_BULK_X_VELOCITY*std::cos(site.phi)
                        +ESTIMATED_EXTERNAL_BULK_Y_VELOCITY*std::sin(site.phi))
                        +ESTIMATED_EXTERNAL_BULK_Z_VELOCITY*std::cos(site.theta);
            }
            if(!std::isfinite(vr)) throw std::runtime_error("invalid radial velocity");
            out << site.id << '\t' << vr << '\n';
        }
        out.close();
        if(!out) throw std::runtime_error("write failed");
        std::cout << (expectation?"mean":"draw") << " " << seed << std::endl;
    }
    return 0;
}
