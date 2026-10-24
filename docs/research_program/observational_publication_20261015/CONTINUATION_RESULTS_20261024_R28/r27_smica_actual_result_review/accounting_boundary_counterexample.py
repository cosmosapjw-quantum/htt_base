"""Read-only deterministic counterexample; no producer imports or process launch."""
import ast
import hashlib
import json
import math
from pathlib import Path

source = Path('/mnt/extdrive/workdir/htt_open_data/r26_smica_exact_product_adapter_numeric/run_smica.py')
body = source.read_bytes()
assert hashlib.sha256(body).hexdigest() == '0522aad2732dc81f699fa812c598bc5d35ae6292c82e916e2b13f7c729095c52'
module = ast.parse(body)
debit_node = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == 'debit')
clock = [10.0]
def persist(_ledger):
    # Model a successful five-second fsync. This is a virtual clock, no sleep.
    clock[0] += 5.0
ns = {'math': math, 'CAP': 900.0, 'persist': persist}
exec(compile(ast.Module(body=[debit_node], type_ignores=[]), str(source), 'exec'), ns)
ledger = {'charges': [], 'delta_charged_seconds': {'SMICA': 0.0}, 'cumulative_charged_seconds': {'SMICA': 0.0}}
phase_start = 0.0
control_elapsed = clock[0] - phase_start
ns['debit'](ledger, control_elapsed, ('SMICA',), 'COMMON_PREPARATION_AND_FORMAT_CONTROL')
phase_start = clock[0]  # Actual run_smica.py line 325 resets after persistence.
clock[0] += 1.0
next_elapsed = clock[0] - phase_start
charged_at_next_timestamp = sum(row['elapsed_seconds'] for row in ledger['charges']) + next_elapsed
result = {
    'source_sha256': hashlib.sha256(body).hexdigest(),
    'source_function_executed': 'AST-extracted debit only; persist replaced by virtual clock',
    'source_transition_lines': [323, 324, 325],
    'virtual_seconds_before_first_debit': 10.0,
    'virtual_persistence_seconds': 5.0,
    'virtual_seconds_after_next_phase': clock[0],
    'charged_seconds_through_same_timestamp': charged_at_next_timestamp,
    'omitted_seconds': clock[0] - charged_at_next_timestamp,
    'production_launches': 0,
    'native_data_reads': 0,
}
assert result['omitted_seconds'] == 5.0
print(json.dumps(result, indent=2))
