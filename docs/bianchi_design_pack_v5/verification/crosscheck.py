
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def main():
    sym = json.loads((HERE/"symbolic_results.json").read_text())
    num = json.loads((HERE/"numeric_results.json").read_text())

    # symbolic zero checks
    zero_checks = {
        "VI_h_compose_q_to_h": sym["classB"]["VI_h_compose_q_to_h"] == "0",
        "VI_h_compose_h_to_q": sym["classB"]["VI_h_compose_h_to_q"] == "0",
        "VII_h_identity": sym["classB"]["VII_h_identity"] == "0",
        "typeVIII_even_reduction": sym["typeVIII"]["mu_even_reduction"] == "0",
        "typeVIII_odd_reduction": sym["typeVIII"]["mu_odd_reduction"] == "0",
        "typeVIII_mu_evenness": sym["typeVIII"]["mu_parity_evenness"] == "0",
        "healpix_offset_identity": sym["healpix"]["offset_difference"] == "0",
        "healpix_triangle_count": sym["healpix"]["total_coeffs_minus_triangle"] == "0",
    }

    numeric_bounds = {
        "classB_max_abs_err": num["samples"]["classB_max_abs_err"],
        "typeVIII_specialcase_max_abs_err": num["samples"]["typeVIII_specialcase_max_abs_err"],
        "fd_max_abs_err": num["samples"]["fd_max_abs_err"],
        "typeVIII_min_val": num["samples"]["typeVIII_min_val"],
    }

    ok = all(zero_checks.values()) and \
         numeric_bounds["classB_max_abs_err"] < 1e-10 and \
         numeric_bounds["typeVIII_specialcase_max_abs_err"] < 1e-20 and \
         numeric_bounds["fd_max_abs_err"] < 1e-20 and \
         numeric_bounds["typeVIII_min_val"] >= 0.0

    out = {
        "symbolic_zero_checks": zero_checks,
        "numeric_bounds": numeric_bounds,
        "crosscheck_pass": ok,
    }
    (HERE/"crosscheck_results.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
