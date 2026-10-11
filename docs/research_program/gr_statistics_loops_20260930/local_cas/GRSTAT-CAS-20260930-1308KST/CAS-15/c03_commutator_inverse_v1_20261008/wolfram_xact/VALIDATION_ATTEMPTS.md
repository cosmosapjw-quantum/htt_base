# Local validation attempts

The first engine attempt (`attempt_001.stdout.log`, `attempt_001.stderr.log`)
exited 0 with 14/14 exact checks. Attempts 002-004 also exited 0; attempt 003
corrected version attribution from xTensor's unqualified `$Version` to
`System`$Version`. Attempt 005 is the final 16/16 exact engine execution and
is bound in `axis_result.json`. All raw engine stdout and stderr files remain
preserved.

The first `cas_gate.py check-axis` invocation used `--axis-result` and exited 2:

```text
usage: cas_gate.py check-axis [-h] --contract CONTRACT --result RESULT
cas_gate.py check-axis: error: the following arguments are required: --result
```

The first invocation with `--result` exited 2 and reported:

```json
{"ok":false,"errors":["axis result must declare evidence_class exact|numerical","axis result must record completed_at"]}
```

After those two envelope fields were corrected, `check-axis` exited 0. Its
final response was `{"ok":true,"axis":"wolfram_xact","status":"PASS",
"verification_state":"STORED_ENVELOPE_ONLY",
"claim_promotion_cas_eligible":false}`. This validator result is distinct
from the direct Wolfram engine execution and from global lifecycle acceptance.
