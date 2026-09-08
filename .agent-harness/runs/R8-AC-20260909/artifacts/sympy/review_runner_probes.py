"""Isolated reproductions for scoped-capability and failure-isolation review."""
import hashlib
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

from scripts.observed_runs import run_tensor_joint_r8 as runner

directory=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='runner_review_',dir=directory) as temp:
    temp=Path(temp)
    handlers=runner.production_handlers(temp)
    attempt=temp/'attempt';attempt.mkdir()
    with patch.object(runner,'_read_owned_laws',return_value=({}, {'broken':(object(),{'query':[0.]},None)})):
        dispatch=handlers['nonsingular_dispatch'].execute(attempt,{})
        observed=handlers['gaussian_observation'].execute(attempt,{})
    try:
        malformed=runner.execute_admitted_products({'malformed':None,'well_shaped':(object(),{'query':[0.]},None)})
    except Exception as exc:
        malformed={'raised':type(exc).__name__,'message':str(exc)}
    # All adapters held must not emit an unscoped usable simulator capability.
    mock=temp/'mocks';mock.mkdir()
    (mock/'mock5.json').write_text(json.dumps({'cells':[{'law':name,'diagnostic_pass':False} for name in ('student5','mixture','selected_normal')]}))
    toy=handlers['toy_simulator_validation'].execute(attempt,{})
    for output in (dispatch,observed,toy):output.pop('evidence',None)
    print(json.dumps({'runner_sha256':hashlib.sha256(Path(runner.__file__).read_bytes()).hexdigest(),
        'all_products_failed_dispatch':dispatch,'all_products_failed_observed':observed,
        'malformed_product_isolation':malformed,'all_toys_held':toy,
        'scope':'Synthetic handler integration probes; no actual product data modified'},indent=2))
