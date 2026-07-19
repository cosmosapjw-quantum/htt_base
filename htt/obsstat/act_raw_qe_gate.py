"""PR-152: ACT DR6 raw-QE acquisition gate and release-simulation cross-fit.

An authenticated ACT DR6 lensing inventory separates the RECONSTRUCTED products
the lensing bundle provides (convergence data + 400 Monte-Carlo sims, the QE
normalisation/response, the fiducial N0, the N1 derivatives, the mask, the
validated multipole range) from the filtered raw-QE inputs it does not bundle.
The separate public DR6 map release includes four CMB splits and the estimator
software is open, but the exact filter/configuration and executed
realisation-dependent N0 are not local. On the release simulations the low-multipole
mean field is formed by an OBSERVATION-INCLUSIVE leave-one-out cross-fit over
the data plus 400 simulations.  Each member is treated once as the
pseudo-observation and debiased by the mean of all other members, making the
score transform permutation-equivariant under the release-simulation null.

The raw four-split maps and public QE software make an RDN0 reconstruction
feasible, but it is a separate large, configuration-locked rerun and is not on
disk here.  The concrete result closed here is the release-simulation-
conditioned null comparison.  No L=2..10 raw-QE sky-power limit is computed,
and released convergence plus an injected signal is NEVER called a pre-QE-stage
transfer.  ACT-release-simulation conditional result at
``roadmap_rescue_v1:C3`` only; no ACT convergence detection, anisotropy,
geometry, or Bianchi-family claim; the two CF4 P0s are untouched.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

# bind the exact-discrete exchangeable pooled-rank estimator (PR-135)
from common.finite_null_ranking import pooled_rank_p  # noqa: E402

SCHEMA_VERSION = "pr152.act_raw_qe_gate.v2"


class ACTRawQEError(ValueError):
    """Raised when the ACT raw-QE gate discipline is violated."""


RAW_QE_INPUT_FILE_FIELDS = (
    "filtering_config", "response_normalization", "analysis_mask",
    "software_lock", "simulation_input_manifest",
)
RAW_QE_OUTPUT_FILE_FIELDS = ("qe_output", "rdn0_output")
RAW_QE_RECEIPT_SCHEMA = "htt.act.raw_qe_execution_receipt.v2"
RAW_QE_LOG_SCHEMA = "htt.act.raw_qe_execution_log.v1"


def _sha256_digest(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    digest = value.removeprefix("sha256:")
    return len(digest) == 64 and all(char in "0123456789abcdef" for char in digest)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(16 << 20):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _canonical_sha256(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _verify_file_record(row: object, *, label: str) -> tuple[dict | None, list[str]]:
    errors: list[str] = []
    if not isinstance(row, dict):
        return None, [f"{label}:record_not_object"]
    path_text = row.get("path")
    size = row.get("size_bytes")
    digest = row.get("sha256")
    if not isinstance(path_text, str) or not path_text.strip():
        errors.append(f"{label}:path_missing")
    if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
        errors.append(f"{label}:size_bytes_invalid")
    if not _sha256_digest(digest):
        errors.append(f"{label}:sha256_invalid")
    if errors:
        return None, errors
    path = Path(path_text).expanduser().resolve()
    if not path.is_file():
        return None, [f"{label}:file_absent"]
    actual_size = path.stat().st_size
    actual_hash = _sha256_file(path)
    if actual_size != size:
        errors.append(f"{label}:size_mismatch")
    if actual_hash != digest:
        errors.append(f"{label}:hash_mismatch")
    return {
        "path": str(path),
        "size_bytes": actual_size,
        "sha256": actual_hash,
    }, errors


def validate_raw_qe_execution_receipt(receipt: dict | None) -> dict:
    """Validate the evidence bundle required to promote raw-QE/RDN0 readiness.

    A local-path boolean or syntactically valid digest is deliberately
    insufficient. The positive branch reopens and fully hashes every typed
    input/output record, verifies a canonical input-identity hash, and parses a
    content-addressed execution log whose command, exit status, inputs, software
    lock, and outputs cross-bind to the receipt.
    """
    if not isinstance(receipt, dict):
        return {"provided": False, "ready": False,
                "missing_or_invalid": ["typed_execution_receipt"]}
    invalid: list[str] = []
    if receipt.get("schema") != RAW_QE_RECEIPT_SCHEMA:
        invalid.append("schema")
    if receipt.get("status") != "RAW_QE_RDN0_EXECUTED":
        invalid.append("status")
    split_rows = receipt.get("four_split_maps")
    if not isinstance(split_rows, list) or len(split_rows) != 4:
        invalid.append("four_split_maps")
        split_rows = []
    split_records: list[dict] = []
    split_ids: list[int] = []
    for index, row in enumerate(split_rows):
        record, errors = _verify_file_record(row, label=f"four_split_maps[{index}]")
        invalid.extend(errors)
        split_id = row.get("split_id") if isinstance(row, dict) else None
        if not isinstance(split_id, int) or isinstance(split_id, bool):
            invalid.append(f"four_split_maps[{index}]:split_id_invalid")
        else:
            split_ids.append(split_id)
        if record is not None:
            record["split_id"] = split_id
            split_records.append(record)
    if sorted(split_ids) != [0, 1, 2, 3]:
        invalid.append("four_split_maps:split_ids_not_exact_0_to_3")
    if (len({row["path"] for row in split_records}) != len(split_records) or
            len({row["sha256"] for row in split_records}) != len(split_records)):
        invalid.append("four_split_maps:not_distinct")

    input_records: dict[str, dict] = {}
    for field in RAW_QE_INPUT_FILE_FIELDS:
        record, errors = _verify_file_record(receipt.get(field), label=field)
        invalid.extend(errors)
        if record is not None:
            input_records[field] = record
    output_records: dict[str, dict] = {}
    for field in RAW_QE_OUTPUT_FILE_FIELDS:
        record, errors = _verify_file_record(receipt.get(field), label=field)
        invalid.extend(errors)
        if record is not None:
            output_records[field] = record
    log_record, log_errors = _verify_file_record(
        receipt.get("execution_log"), label="execution_log")
    invalid.extend(log_errors)
    all_records = split_records + list(input_records.values()) + \
        list(output_records.values()) + ([log_record] if log_record else [])
    if len({row["path"] for row in all_records}) != len(all_records):
        invalid.append("file_paths_not_distinct")
    if (len(output_records) == 2 and
            output_records["qe_output"]["sha256"] ==
            output_records["rdn0_output"]["sha256"]):
        invalid.append("qe_and_rdn0_outputs_not_distinct")

    input_identity_payload = {
        "four_split_maps": sorted(
            split_records, key=lambda row: str(row.get("split_id"))),
        **{field: input_records.get(field) for field in RAW_QE_INPUT_FILE_FIELDS},
    }
    input_identity_sha256 = _canonical_sha256(input_identity_payload)
    if receipt.get("input_checksums_verified") is not True:
        invalid.append("input_checksums_verified")
    execution = receipt.get("execution")
    if not isinstance(execution, dict):
        invalid.append("execution")
        execution = {}
    command = execution.get("command")
    if not isinstance(command, str) or not command.strip():
        invalid.append("execution:command")
    if execution.get("exit_code") != 0:
        invalid.append("execution:exit_code")
    expected_lineage = {
        "input_identity_sha256": input_identity_sha256,
        "software_lock_sha256": input_records.get("software_lock", {}).get("sha256"),
        "simulation_input_manifest_sha256": input_records.get(
            "simulation_input_manifest", {}).get("sha256"),
        "qe_output_sha256": output_records.get("qe_output", {}).get("sha256"),
        "rdn0_output_sha256": output_records.get("rdn0_output", {}).get("sha256"),
        "execution_log_sha256": log_record.get("sha256") if log_record else None,
    }
    for field, expected in expected_lineage.items():
        if execution.get(field) != expected or expected is None:
            invalid.append(f"execution:{field}_mismatch")

    log_payload: dict = {}
    if log_record is not None:
        try:
            log_payload = json.loads(Path(log_record["path"]).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            invalid.append("execution_log:unparseable")
    expected_log = {
        "schema": RAW_QE_LOG_SCHEMA,
        "status": "COMPLETE",
        "command": command,
        "exit_code": 0,
        **{field: value for field, value in expected_lineage.items()
           if field != "execution_log_sha256"},
    }
    for field, expected in expected_log.items():
        if log_payload.get(field) != expected or expected is None:
            invalid.append(f"execution_log:{field}_mismatch")
    invalid = list(dict.fromkeys(invalid))
    return {
        "provided": True, "ready": not invalid,
        "missing_or_invalid": invalid,
        "schema": receipt.get("schema"), "status": receipt.get("status"),
        "verified_file_count": len(all_records),
        "verified_input_identity_sha256": input_identity_sha256,
        "verified_execution_log_sha256": (
            log_record.get("sha256") if log_record else None),
    }


# --------------------------------------------------------------------------
# authenticated inventory + upstream availability decision
# --------------------------------------------------------------------------
def act_dr6_lensing_inventory(*, present: dict, raw_qe_inputs_on_disk: bool,
                              validated_ell_range: tuple,
                              reference_url: str,
                              public_raw_qe_sources: dict | None = None,
                              raw_qe_execution_receipt: dict | None = None) -> dict:
    """Authenticate the ACT DR6 lensing bundle: reconstructed products present
    locally (each a name -> content-address) versus the raw-QE inputs not local.
    Four CMB splits exist in the separate public map release and the QE stack is
    open; that does not mean the lensing bundle includes the exact filtering or
    an executed realization-dependent N0 stage.
    """
    readiness = validate_raw_qe_execution_receipt(raw_qe_execution_receipt)
    ready = bool(raw_qe_inputs_on_disk and readiness["ready"])
    local_missing = ([] if ready else [
        "four_split_cmb_maps", "pinned_filtering_configuration",
        "response_normalization", "analysis_mask", "software_environment_lock",
        "simulation_input_manifest", "executed_quadratic_estimator_pipeline",
        "realisation_dependent_n0",
    ])
    return {
        "present_products": dict(present),
        "local_missing_raw_qe_inputs": local_missing,
        # compatibility alias retained for old consumers; these are absent
        # locally, not necessarily absent from public distribution.
        "absent_raw_qe_inputs": local_missing,
        "raw_qe_inputs_on_disk_requested": bool(raw_qe_inputs_on_disk),
        "raw_qe_inputs_on_disk": ready,
        "raw_qe_readiness_receipt": readiness,
        "public_raw_qe_sources": dict(public_raw_qe_sources or {}),
        "raw_qe_external_reproducibility": (
            "executed_and_local" if ready else
            "feasible_large_separate_pipeline_rerun"),
        "validated_ell_range": [int(validated_ell_range[0]),
                                int(validated_ell_range[1])],
        "reference_url": reference_url,
        "note": "the lensing release provides reconstructed convergence and "
                "correction/response products. Public four-split CMB maps and "
                "open QE software make an independent RDN0 rerun feasible, but "
                "the exact inputs, filtering lock, and executed raw-QE stage are "
                "not present in this repository"}


def upstream_availability_decision(inventory: dict) -> dict:
    """Separate the completed release result from the deferred public raw-QE rerun."""
    readiness = inventory.get("raw_qe_readiness_receipt") or {}
    available = bool(inventory.get("raw_qe_inputs_on_disk") and
                     readiness.get("ready") and
                     not inventory.get("local_missing_raw_qe_inputs"))
    return {
        "raw_qe_available": available,
        "decision": ("RAW_QE_E2E_INJECTION_AVAILABLE" if available else
                     "DEFER_RAW_QE_RDN0_PUBLIC_INPUTS_LARGE_RECONSTRUCTION"),
        "closed_result": ("raw_qe_e2e_injection" if available else
                          "release_simulation_conditioned_null_comparison"),
        "closed_diagnostic": ("raw_qe_e2e_injection" if available else
                              "release_simulation_conditioned_null_comparison"),
        "raw_qe_stage_status": ("executed" if available else
                                "publicly_reproducible_not_executed_locally"),
        "readiness_evidence_complete": available,
        "note": "the public inputs and software make raw-QE/RDN0 reproducible, "
                "but it remains a large separate rerun until the four splits, "
                "filter/config lock, response, masks, and execution receipt are "
                "local. The release-simulation-conditioned null comparison is "
                "a concrete result; no raw-QE L=2..10 limit is claimed"}


# --------------------------------------------------------------------------
# band statistic + leave-one-simulation cross-fit mean field
# --------------------------------------------------------------------------
def band_power(alm_low: np.ndarray, mode_weight: np.ndarray) -> float:
    """The low-multipole band power S = sum_m w_m |a_lm|^2 (w_m = 1 for m=0, 2
    for m>0 to count the +/-m pair of the real field)."""
    return float(np.sum(mode_weight * np.abs(alm_low) ** 2))


def observation_inclusive_crossfit_mean_field(
        sim_low: np.ndarray, data_low: np.ndarray,
        mode_weight: np.ndarray) -> dict:
    """Permutation-equivariant data+simulation leave-one-out mean-field rank.

    Stack the observation and simulations into ``N+1`` exchangeable units. For
    each unit, estimate the mean field from the other ``N`` units and compute
    the same band power. Under the release-simulation null this full transform
    commutes with any permutation, unlike a simulation-only LOO transform.
    """
    sim = np.asarray(sim_low)
    data = np.asarray(data_low)
    if sim.ndim != 2 or data.shape != sim.shape[1:] or sim.shape[0] < 2:
        raise ValueError("need at least two simulations with data-matched modes")
    combined = np.concatenate([data[None, :], sim], axis=0)
    n_total = combined.shape[0]
    total = combined.sum(axis=0)
    mean_other = (total[None, :] - combined) / (n_total - 1)
    residual = combined - mean_other
    scores = np.asarray([band_power(row, mode_weight) for row in residual])
    observed = float(scores[0])
    null = scores[1:]
    exceedance = int(np.count_nonzero(null >= observed))
    ties = int(np.count_nonzero(null == observed))
    p = float((1 + exceedance) / n_total)
    data_mean_field = sim.mean(axis=0)
    return {
        "n_sims": int(sim.shape[0]),
        "n_exchangeable_units": int(n_total),
        "S_data": observed,
        "simulation_band_power_mean": float(null.mean()),
        "data_mean_field_band_power": band_power(data_mean_field, mode_weight),
        "upper_exceedance_count": exceedance,
        "tie_count": ties,
        "observation_inclusive_crossfit_pooled_rank_p": p,
        "support_resolution": float(1.0 / n_total),
        "permutation_equivariant_transform": True,
        "simulation_band_powers": [float(value) for value in null],
        "note": f"the data and {sim.shape[0]} simulations are treated as "
                f"{n_total} exchangeable units; each score subtracts the mean "
                f"of the other {n_total - 1} units. "
                "The resulting release-simulation pooled rank is exact only "
                "conditional on data/simulation exchangeability after the "
                "released reconstruction pipeline"
    }


def leave_one_sim_crossfit_mean_field(sim_low: np.ndarray, data_low: np.ndarray,
                                      mode_weight: np.ndarray) -> dict:
    """Legacy simulation-only sensitivity, not the primary exact-rank transform.

    Debias the sims by a LEAVE-ONE-SIMULATION cross-fit mean field (each sim
    minus the mean of the OTHER sims) and the data by the mean over ALL sims, so
    their marginal variances differ by ``n^2/(n^2-1)``. Report the naive all-sim
    band power for comparison: it debiases each sim by a mean that INCLUDES
    itself (a treatment the data never gets), which deflates the sim residual
    band power and biases the pooled rank."""
    n = sim_low.shape[0]
    total = sim_low.sum(axis=0)
    mf_all = total / n                                     # data mean field
    # cross-fit: sim k debiased by the mean of the other n-1 sims
    mf_loo = (total[None, :] - sim_low) / (n - 1)
    resid_crossfit = sim_low - mf_loo
    resid_naive = sim_low - mf_all[None, :]                # self-mean-field
    S_cross = np.array([band_power(resid_crossfit[k], mode_weight)
                        for k in range(n)])
    S_naive = np.array([band_power(resid_naive[k], mode_weight)
                        for k in range(n)])
    S_data = band_power(data_low - mf_all, mode_weight)
    mean_cross = float(S_cross.mean())
    mean_naive = float(S_naive.mean())
    self_mf_bias_ratio = float(mean_naive / mean_cross) if mean_cross else \
        float("inf")
    # the naive/crossfit ratio is the EXACT input-independent ((n-1)/n)^2 sample-
    # size scaling (resid_naive == ((n-1)/n) resid_crossfit identically), NOT a
    # data-dependent measured bias
    algebraic_bias_ratio = float(((n - 1) / n) ** 2)
    variance_ratio = float(n * n / (n * n - 1))
    # the mean field itself: for the low-multipole band it is numerically
    # negligible, so debiasing is effectively a no-op at low ell and the
    # cross-fit is the PRINCIPLED construction rather than a large correction
    mf_band_power = band_power(mf_all, mode_weight)
    p_crossfit = float(pooled_rank_p(S_data, S_cross))
    p_naive = float(pooled_rank_p(S_data, S_naive))
    return {"n_sims": int(n),
            "S_data": S_data,
            "mean_field_band_power": mf_band_power,
            "crossfit_sim_band_power_mean": mean_cross,
            "naive_sim_band_power_mean": mean_naive,
            "self_mean_field_bias_ratio_naive_over_crossfit": self_mf_bias_ratio,
            "algebraic_bias_ratio_n_minus_1_over_n_squared": algebraic_bias_ratio,
            "simulation_over_data_residual_variance_ratio": variance_ratio,
            "joint_exchangeability_exact": False,
            "bias_ratio_is_input_independent": True,
            "naive_self_mean_field_deflates_residual":
                bool(mean_naive < mean_cross),
            "crossfit_pooled_rank_p": p_crossfit,
            "naive_pooled_rank_p": p_naive,
            "crossfit_sim_band_powers": [float(s) for s in S_cross],
            "note": "legacy simulation-only LOO sensitivity: data use the all-"
                    "simulation mean while each simulation uses the other "
                    "simulations, so the transform is not jointly permutation-"
                    "equivariant. The naive/cross-fit band-power ratio is "
                    "the EXACT input-independent ((n-1)/n)^2 sample-size scaling, "
                    "not a data-dependent measured bias, and the low-multipole "
                    "mean field is numerically negligible so the cross-fit is the "
                    "principled construction rather than a large correction on "
                    "this data --- it is reported as a secondary sensitivity"}


# --------------------------------------------------------------------------
# algebraic finite-rank ceiling of the low-multipole band
# --------------------------------------------------------------------------
def algebraic_finite_rank_ceiling(*, n_sims: int, ell_min: int,
                                  ell_max: int) -> dict:
    """Return the exact algebraic ceiling on the covariance rank.

    This is ``min(sum_ell(2 ell + 1), n_sims - 1)``. It is a support bound,
    not a numerical rank measurement of the released simulation covariance.
    """
    n_modes = int(sum(2 * ell + 1 for ell in range(ell_min, ell_max + 1)))
    sample_rank = int(n_sims - 1)
    ceiling = int(min(n_modes, sample_rank))
    return {"ell_min": int(ell_min), "ell_max": int(ell_max),
            "n_real_harmonic_dof": n_modes, "sample_rank": sample_rank,
            "finite_rank_ceiling": ceiling,
            "realized_numerical_rank_measured": False,
            "rank_limited_by": ("sample" if sample_rank < n_modes else "modes"),
            "note": "exact algebraic ceiling: the low-multipole band carries "
                    "sum(2 ell + 1) real dof, capped by the mean-field-"
                    "subtracted sample rank n_sims - 1; the realized numerical "
                    "covariance rank was not measured"}


# --------------------------------------------------------------------------
# stochastic vs fixed-template injection law
# --------------------------------------------------------------------------
def injection_law_distinction(sim_band_powers: list, *,
                              injection_amplitude: float, seed: int) -> dict:
    """Distinguish the two injection laws by their IDENTIFIABILITY under the SAME
    null.  A STOCHASTIC injection whose band-power distribution EQUALS the null's
    (an incoherent convergence field carrying the null's own power) is
    UNIDENTIFIABLE: a draw from that distribution IS a null draw, so its pooled
    rank against the null stays uniform.  A FIXED-TEMPLATE injection adds a
    COHERENT band power to every realisation --- a deterministic offset that
    shifts the rank.  Both are ranked against the SAME null, so the distinction
    is identifiable-vs-not, not an artifact of different null sets (it is NOT an
    additive stochastic field, which would itself raise the band power)."""
    rng = np.random.Generator(np.random.PCG64(seed))
    S = np.asarray(sim_band_powers, float)
    mu, sd = float(S.mean()), float(S.std(ddof=1))
    # stochastic (unidentifiable): a bootstrap draw from the SAME distribution as
    # the null, ranked against the null it cannot be told apart from -> uniform
    stochastic = np.array([float(rng.choice(S)) for _ in range(S.size)])
    p_stochastic = float(np.mean([pooled_rank_p(x, S) for x in stochastic]))
    # fixed-template (identifiable): a coherent additive band power on every draw
    fixed = S + injection_amplitude * mu
    p_fixed = float(np.mean([pooled_rank_p(x, S) for x in fixed]))
    return {"injection_amplitude": injection_amplitude,
            "sim_band_power_mean": mu, "sim_band_power_std": sd,
            "stochastic_mean_pooled_rank_p": p_stochastic,
            "fixed_template_mean_pooled_rank_p": p_fixed,
            "laws_distinct": bool(abs(p_stochastic - p_fixed) > 0.05),
            "note": "a stochastic injection whose band-power distribution equals "
                    "the null's is unidentifiable (its pooled rank against the "
                    "same null stays uniform); a fixed-template injection is a "
                    "coherent additive offset that shifts the rank; both are "
                    "ranked against the SAME null so the distinction is "
                    "identifiability, not a null-set artifact --- this is not an "
                    "additive stochastic field (which would itself raise the "
                    "band power)"}


# --------------------------------------------------------------------------
# guards
# --------------------------------------------------------------------------
def refuse_pre_qe_transfer_label(label: str) -> None:
    if label in ("released_kappa_plus_signal_is_pre_qe", "pre_qe_transfer"):
        raise ACTRawQEError(
            "released convergence plus an injected signal may not be called a "
            "pre-QE-stage transfer")


def refuse_sky_power_limit_without_raw_qe(raw_qe_available: bool,
                                          claim: str) -> None:
    if claim in ("l2_10_sky_power_limit", "sky_power_limit") \
            and not raw_qe_available:
        raise ACTRawQEError(
            "an L=2 to 10 sky-power limit may not be computed from absent raw-QE "
            "inputs")


def refuse_naive_self_mean_field(crossfit: bool) -> None:
    if not crossfit:
        raise ACTRawQEError(
            "a naive all-sim self-mean-field without the leave-one-simulation "
            "cross-fit is rejected")


def refuse_act_detection(claim: str) -> None:
    if claim in ("act_kappa_detection", "anisotropy_detection"):
        raise ACTRawQEError(
            "an ACT convergence detection or anisotropy claim is rejected")


def refuse_bianchi_from_act(claim: str) -> None:
    if claim in ("bianchi_family", "geometry"):
        raise ACTRawQEError(
            "a Bianchi-family or geometry claim from the ACT convergence is "
            "rejected")


def refuse_raw_qe_without_inputs(raw_qe_available: bool, claim: str) -> None:
    if claim in ("raw_qe_inference", "rdn0") and not raw_qe_available:
        raise ACTRawQEError(
            "a raw-QE inference without the upstream filtered-map and QE inputs "
            "is rejected")


# --------------------------------------------------------------------------
# captions
# --------------------------------------------------------------------------
_FORBIDDEN = tuple(
    a + b for a, b in (
        ("pre-qe ", "transfer"),
        ("sky-power limit ", "from absent"),
        ("naive ", "self-mean-field"),
        ("act kappa ", "detection"),
        ("bianchi family ", "from act"),
        ("anisotropy ", "detected"),
    ))


def lint_caption(text: str) -> None:
    low = text.lower()
    for phrase in _FORBIDDEN:
        if phrase in low:
            raise ACTRawQEError(f"forbidden caption phrase: {phrase!r}")


def generate_caption(inventory: dict, crossfit: dict, decision: dict) -> str:
    return (
        f"ACT DR6 lensing release-simulation cross-fit: an authenticated "
        f"inventory separates the {len(inventory['present_products'])} "
        f"reconstructed products present from the raw-QE inputs not yet local. "
        f"The low-multipole score uses an observation-inclusive leave-one-out "
        f"mean field over {crossfit['n_exchangeable_units']} units; the release-"
        f"simulation-conditioned pooled "
        f"rank of the observed band power is "
        f"{crossfit['observation_inclusive_crossfit_pooled_rank_p']:.3f} "
        f"({crossfit['upper_exceedance_count'] + 1}/"
        f"{crossfit['n_exchangeable_units']}). Public four-split maps and open "
        f"QE software make RDN0 feasible, but the configuration-locked raw-QE "
        f"rerun is deferred ({decision['decision']}). The analysed "
        f"L={crossfit['analysis_ell_range'][0]}..{crossfit['analysis_ell_range'][1]} "
        f"band is outside the release spectrum validation range "
        f"L={crossfit['release_validated_ell_range'][0]}.."
        f"{crossfit['release_validated_ell_range'][1]}; this is therefore a "
        f"conditional exploratory release-simulation comparison, not ACT low-L "
        f"validation. No convergence "
        f"detection, isotropy proof, anisotropy claim, or "
        f"Bianchi-family claim; the two CF4 P0s stay OPEN.")
