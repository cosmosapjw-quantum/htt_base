#!/usr/bin/env python3
"""CAS-07 M02 Sage/Singular axis. Invoke with Sage 10.9's ``sage -python``.

The symbolic derivative calculation is the FTC/integration-by-parts schema.
The universal bound additionally uses the explicit real-order argument below;
polynomial calculations are boundary examples and independent exact checks.
"""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback


AXIS = Path(__file__).resolve().parents[1]
FROZEN = AXIS.parent
ROOT = Path.cwd()
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")
SOURCE = Path(__file__).resolve()
SINGULAR_SOURCE = SOURCE.with_name("endpoint_weight.sing")
EXPECTED = {
    "contract": "eacc294fa147bd4cabaf295c76f29814b461cae2c8d10eb0a44fdbe2254e0799",
    "admitted_inputs": "18bfcfb302209caaeac08df72137040ea0939826c551045e7f798d86921db125",
    "common_spec": "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    "singular_binary": "9430832b7c972b6b26d29ded4d91a3e1df8fd87d67f4b8d3f14d8201a75f923c",
}
INPUTS = {
    "contract": FROZEN / "EXECUTION_CONTRACT.json",
    "admitted_inputs": FROZEN / "ADMITTED_INPUTS.json",
    "common_spec": ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md",
    "singular_binary": SINGULAR,
}
CHECK_NAMES = (
    "CAS-07-M02-REMAINDER-IDENTITY",
    "CAS-07-M02-REMAINDER-BOUND",
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture(label, argv):
    completed = subprocess.run(argv, capture_output=True, text=True, timeout=120)
    (AXIS / (label + ".stdout.log")).write_text(completed.stdout)
    (AXIS / (label + ".stderr.log")).write_text(completed.stderr)
    return {
        "argv": [str(x) for x in argv],
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def main():
    result = {
        "axis": "sage_singular",
        "contract_id": "GRSTAT-20260930-CAS-07-M02-TAYLOR-REMAINDER-V1",
        "checks": {key: False for key in CHECK_NAMES},
        "domain_assumption_diff": [],
        "counterexample": None,
        "global_launch_id": None,
        "global_authority": "unavailable; owner-authorized direct local axis execution",
        "actual_model": "UNKNOWN",
        "actual_effort": "UNKNOWN",
        "scientific_admission": "HOLD",
    }
    try:
        actual = {key: sha256(path) for key, path in INPUTS.items()}
        result["input_and_binary_sha256"] = actual
        result["source_sha256"] = {
            "run.py": sha256(SOURCE),
            "endpoint_weight.sing": sha256(SINGULAR_SOURCE),
        }
        if actual != EXPECTED:
            result["domain_assumption_diff"] = [
                "Frozen input or Singular binary SHA-256 mismatch: " + key
                for key in EXPECTED if actual.get(key) != EXPECTED[key]
            ]
            return result

        from sage.all import SR, diff, function, integral, var
        from sage.version import version as sage_version

        result["tool_versions"] = {"sage": sage_version}
        t, s, z0, v, m2 = var("t s z0 v m2")
        Z = function("Z")
        z1 = diff(Z(t), t)
        z2 = diff(Z(t), t, 2)
        primitive = (s - t) * z1 + Z(t)
        derivative_residual = (diff(primitive, t) - (s - t) * z2).simplify_full()
        endpoint_residual = (
            primitive.subs({t: s}) - primitive.subs({t: 0})
            - (Z(s) - Z(0) - s * z1.subs({t: 0}))
        ).simplify_full()
        weight_integral_residual = (integral(s - t, t, 0, s) - s**2 / 2).simplify_full()
        affine = z0 + v * t
        quadratic = affine + m2 * t**2 / 2
        examples = {
            "s_zero": bool((primitive.subs({t: 0, s: 0}) - Z(0)).simplify_full() == 0),
            "affine_zero_remainder": bool((affine.subs({t: s}) - affine.subs({t: 0}) - s * diff(affine, t).subs({t: 0})).simplify_full() == 0),
            "quadratic_saturation": bool((quadratic.subs({t: s}) - quadratic.subs({t: 0}) - s * diff(quadratic, t).subs({t: 0}) - m2 * s**2 / 2).simplify_full() == 0),
        }
        sage_schema_ok = all(bool(x == 0) for x in (derivative_residual, endpoint_residual, weight_integral_residual))
        result["sage_exact"] = {
            "primitive": str(primitive),
            "derivative_residual": str(derivative_residual),
            "endpoint_residual": str(endpoint_residual),
            "weight_integral_residual": str(weight_integral_residual),
            "boundary_examples": examples,
        }

        version = capture("singular_version", [SINGULAR, "--version"])
        execution = capture("singular", [SINGULAR, "-q", SINGULAR_SOURCE])
        result["singular"] = {
            "version_argv": version["argv"],
            "version_exit_code": version["exit_code"],
            "argv": execution["argv"],
            "exit_code": execution["exit_code"],
            "raw_logs": ["singular_version.stdout.log", "singular_version.stderr.log", "singular.stdout.log", "singular.stderr.log"],
        }
        result["tool_versions"]["singular_first_line"] = version["stdout"].splitlines()[0] if version["stdout"] else ""
        markers = (
            "SINGULAR_SCHEMA_DERIVATIVE=0",
            "SINGULAR_SCHEMA_ENDPOINTS=0",
            "SINGULAR_WEIGHT_INTEGRAL=0",
            "SINGULAR_QUADRATIC_REMAINDER=0",
        )
        singular_ok = (
            version["exit_code"] == 0
            and "4.4.1 (44100" in version["stdout"]
            and execution["exit_code"] == 0
            and not version["stderr"].strip()
            and not execution["stderr"].strip()
            and all(marker in execution["stdout"].splitlines() for marker in markers)
            and not any(line.lstrip().startswith("?") for line in execution["stdout"].splitlines())
        )
        result["singular"]["expected_markers_present"] = singular_ok

        # FTC on [0,s]: integral_0^s primitive' = primitive(s)-primitive(0).
        # The derivative identity and endpoints above produce the claimed
        # integral remainder for arbitrary twice differentiable Z with continuous Z2.
        identity_ok = sage_schema_ok and singular_ok and all(examples.values()) and sage_version.startswith("10.9")
        result["checks"][CHECK_NAMES[0]] = identity_ok

        # Universal real-order step, for every 0<=s<=L and t in [0,s]:
        # w=s-t>=0, |Z2(t)|<=M2, and M2>=0. Consequently
        # |integral w*Z2| <= integral w*|Z2| <= M2*integral w
        # = M2*s^2/2. No polynomial assumption or sampled inference enters.
        result["universal_bound_certificate"] = {
            "domain": "L>0, 0<=s<=L, M2>=0, t in [0,s]",
            "weight_nonnegative": "s-t>=0 from t<=s",
            "pointwise": "abs((s-t)*Z2(t))=(s-t)*abs(Z2(t))<=(s-t)*M2",
            "integration": "triangle inequality and monotonicity of real integrals",
            "exact_weight_integral": "integral_0^s (s-t) dt=s^2/2",
            "regularity": "Z2 continuous on [0,L], so the weighted integrand is integrable; FTC applies to the primitive",
            "s_zero": "both sides vanish",
            "m2_zero": "the pointwise bound forces Z2=0, hence zero remainder",
        }
        result["checks"][CHECK_NAMES[1]] = bool(identity_ok and weight_integral_residual == 0)
        if not all(result["checks"].values()):
            result["counterexample"] = "No mathematical counterexample found; an axis diagnostic or schema check failed. Inspect raw logs."
    except Exception as exc:
        result["counterexample"] = "Execution error, not a mathematical counterexample: " + repr(exc)
        result["traceback"] = traceback.format_exc()
    return result


if __name__ == "__main__":
    print(json.dumps(main(), sort_keys=True))
