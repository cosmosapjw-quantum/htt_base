"""Same-thread direct author followups, without a workspace job or new launch.

The real PreToolUse invocation consumes an observed ended turn once. Runtime and
cumulative accounting observations are semantic metadata, not transcript hashes.
Original registrations, exits, validators and review reservations remain intact.
"""
from copy import deepcopy
import json
from pathlib import Path

from cuhg.codex_hooks.child_lifecycle import LifecycleStore, _fail, _sandbox
from cuhg.models.mixed_worker_routing import PROFILES

UNKNOWN = 'NOT_MEASURED'


def is_direct_author(record):
    return (record.get('continuation_context') is None and
            PROFILES.get(record.get('profile', {}).get('profile_id'), {}).get('role') == 'implement')


def _observe(record):
    """Read only runtime/usage fields; do not interpret candidate text or results."""
    child = record.get('child') or {}
    saved = child.get('runtime_observation', {})
    latest = record.get('exits', {}).get(record.get('last_exit_digest'), {})
    if (saved.get('state') != 'MATCH' or not saved.get('turn_id') or
            latest.get('runtime_observation', {}).get('state') != 'MATCH' or
            latest['runtime_observation'].get('turn_id') != saved['turn_id']):
        raise _fail('DIRECT_AUTHOR_RUNTIME_UNVERIFIED', 'A lifecycle-observed ended runtime is required.')
    meta = context = terminal = None
    usage = UNKNOWN
    high_water = None
    with Path(child['transcript_ref']).open(encoding='utf-8') as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            payload = row.get('payload', {})
            if row.get('type') == 'session_meta':
                meta = payload
                if meta.get('id') != child['child_id']:
                    raise _fail('DIRECT_AUTHOR_RUNTIME_MISMATCH', 'Transcript belongs to another child.')
            elif row.get('type') == 'turn_context':
                if context is None or context.get('turn_id') != payload.get('turn_id'):
                    usage = UNKNOWN
                context = {k: payload.get(k) for k in ('turn_id', 'model', 'effort', 'cwd', 'sandbox_policy')}
            elif row.get('type') == 'event_msg':
                kind = payload.get('type')
                if kind in {'task_started', 'task_complete', 'turn_aborted'}:
                    terminal = (kind, payload.get('turn_id'))
                elif kind == 'token_count':
                    info = payload.get('info') or {}
                    total = (info.get('total_token_usage') or {}).get('total_tokens')
                    usage = total if type(total) is int and total >= 0 else UNKNOWN
                    if usage != UNKNOWN:
                        if high_water is not None and usage < high_water:
                            raise _fail('DIRECT_AUTHOR_USAGE_DECREASED', 'Cumulative usage cannot reset.')
                        high_water = usage
    turn = saved['turn_id']
    if meta is None or context is None or context.get('turn_id') != turn or terminal != ('task_complete', turn):
        raise _fail('DIRECT_AUTHOR_NOT_ENDED', 'Latest execution must have an observed terminal turn.')
    source = meta.get('source')
    spawn = source.get('subagent', {}).get('thread_spawn', {}) if isinstance(source, dict) else {}
    if (spawn.get('parent_thread_id', record['session_id']) != record['session_id'] or
            spawn.get('agent_role', record['profile']['profile_id']) != record['profile']['profile_id'] or
            (spawn.get('agent_path') and record.get('task_name') and
             spawn['agent_path'].rsplit('/', 1)[-1] != record['task_name'])):
        raise _fail('DIRECT_AUTHOR_RUNTIME_MISMATCH', 'Native parent, role or task differs from the binding.')
    profile = record['profile']
    expected = (profile['model'], profile['effort'], record['identity']['worktree_root'],
                _sandbox(profile.get('sandbox_policy')))
    actual = (context['model'], context['effort'], context['cwd'], _sandbox(context['sandbox_policy']))
    if expected[-1] is None or actual != expected:
        raise _fail('DIRECT_AUTHOR_RUNTIME_MISMATCH', 'Observed settings differ from the registered author.')
    return {'turn_id': turn, 'runtime': dict(zip(('model', 'effort', 'cwd', 'sandbox_policy'), actual)),
            'transcript_ref': child['transcript_ref'], 'cumulative_tokens': usage,
            'observed_token_high_water': high_water if high_water is not None else UNKNOWN,
            'cost_usd': UNKNOWN}


def _validate(store, record, session_id, child_id, client_cwd):
    if (not is_direct_author(record) or record.get('session_id') != session_id or
            not record.get('claim') or record['claim'].get('session_id') != session_id or
            (record.get('child') or {}).get('child_id') != child_id):
        raise _fail('DIRECT_AUTHOR_IDENTITY_MISMATCH', 'Retain the existing direct author and parent/task binding.')
    store._validate_event_identity(record, {'session_id': session_id, 'cwd': client_cwd}, require_cwd=True)
    # Existing frozen source checks are preserved; no candidate or validator runs.
    store._revalidate_frozen_validator(record)
    return _observe(record)


def _return(receipt, observed):
    if receipt['baseline']['turn_id'] == observed['turn_id']:
        raise _fail('DIRECT_AUTHOR_OUTCOME_PENDING', 'No new ended turn has been observed after the consumed followup.')
    before, after = receipt['baseline']['cumulative_tokens'], observed['cumulative_tokens']
    floor = receipt['baseline']['observed_token_high_water']
    if after != UNKNOWN and floor != UNKNOWN and after < floor:
        raise _fail('DIRECT_AUTHOR_USAGE_DECREASED', 'Prior cumulative expense must be retained.')
    delta = after - before if before != UNKNOWN and after != UNKNOWN else UNKNOWN
    result = {'observed': observed, 'additional_tokens': delta, 'cost_usd': UNKNOWN, 'claim_admitted': False}
    if receipt.get('return') is not None:
        if receipt['return'] != result:
            raise _fail('DIRECT_AUTHOR_RETURN_CHANGED', 'Preserve the recorded continuation return.')
    else:
        receipt.update(status='AUTHOR_RETURNED', **{'return': result})
    return receipt


def _budget(state, record, observed):
    from cuhg.models.continuous_policy import load_policy, validate_budget
    # The current policy has a soft target, not an implicit historical token cap.
    # Frozen explicit caps, if present, cannot be loosened by a newer default.
    same_task = [other for other in state['launches'].values()
                 if (other.get('run_id'), other.get('task_id'), other.get('identity', {}).get('repo_root')) ==
                    (record['run_id'], record['task_id'], record['identity']['repo_root'])]
    policies = [load_policy().get('budget'), *(other.get('adaptive_budget') for other in same_task)]
    limits = [validate_budget(p)['explicit_hard_limit'] for p in policies if p is not None]
    for other in same_task:
        for receipt in state.get('direct_author_continuations', {}).get(other['launch_id'], []):
            limits.append(receipt['budget']['explicit_hard_limit'])
    limits = [limit for limit in limits if limit is not None]
    if not limits:
        return {'explicit_hard_limit': None, 'task_tokens': UNKNOWN}
    limit = min(limits)
    totals = {record['child']['child_id']: observed['cumulative_tokens']}
    for other in same_task:
        if other['launch_id'] == record['launch_id'] or not other.get('claim'):
            continue
        value = _observe(other)
        totals[other['child']['child_id']] = value['cumulative_tokens']
    if UNKNOWN in totals.values() or sum(totals.values()) >= limit:
        raise _fail('DIRECT_AUTHOR_EXPLICIT_CAP', 'Same-task usage is unknown or the explicit hard limit is exhausted.')
    return {'explicit_hard_limit': limit, 'task_tokens': sum(totals.values())}


def consume(root, *, launch_id, session_id, child_id, client_cwd, tool_use_id):
    """Called only for the real parent followup; the invocation is its own claim."""
    if not isinstance(tool_use_id, str) or not tool_use_id.strip():
        raise _fail('DIRECT_AUTHOR_TOOL_ID_REQUIRED', 'A real native followup invocation is required.')
    store = LifecycleStore(Path(root) / 'lifecycle')
    with store._locked() as state:
        record = state['launches'][launch_id]
        observed = _validate(store, record, session_id, child_id, client_cwd)
        history = state.get('direct_author_continuations', {}).get(launch_id, [])
        if tool_use_id == record['claim']['tool_use_id'] or any(r['tool_use_id'] == tool_use_id for r in history):
            raise _fail('DIRECT_AUTHOR_TOOL_ID_REUSED', 'Never replay a consumed invocation.')
        if history:
            _return(history[-1], observed)
        budget = _budget(state, record, observed)
        receipt = {'status': 'CONSUMED_OUTCOME_UNKNOWN', 'launch_id': launch_id,
                   'session_id': session_id, 'child_id': child_id,
                   'run_id': record['run_id'], 'task_id': record['task_id'],
                   'tool_use_id': tool_use_id, 'baseline': observed, 'budget': budget,
                   'dispatch_refunded': False, 'claim_admitted': False}
        state.setdefault('direct_author_continuations', {}).setdefault(launch_id, []).append(receipt)
        return deepcopy(receipt)


def inspect(root, *, launch_id, session_id, child_id, client_cwd):
    """Prospective check only; does not reserve or synthesize a hook event."""
    store = LifecycleStore(Path(root) / 'lifecycle')
    with store._locked(read_only=True) as state:
        record = state['launches'][launch_id]
        observed = _validate(store, record, session_id, child_id, client_cwd)
        history = state.get('direct_author_continuations', {}).get(launch_id, [])
        if history:
            _return(deepcopy(history[-1]), observed)
        return {'status': 'DIRECT_AUTHOR_FOLLOWUP_AVAILABLE', 'launch_id': launch_id,
                'observed': observed, 'budget': _budget(state, record, observed),
                'consumptions': len(history), 'claim_admitted': False, 'read_only': True}


def record_return(root, *, launch_id, session_id, child_id, client_cwd):
    """Append accounting from the real terminal lifecycle; never replay validators."""
    store = LifecycleStore(Path(root) / 'lifecycle')
    with store._locked() as state:
        record = state['launches'][launch_id]
        observed = _validate(store, record, session_id, child_id, client_cwd)
        history = state.get('direct_author_continuations', {}).get(launch_id, [])
        if not history:
            raise _fail('DIRECT_AUTHOR_NOT_CONSUMED', 'No direct author followup was consumed.')
        return deepcopy(_return(history[-1], observed))


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('inspect', 'record-return'))
    parser.add_argument('--root', type=Path, required=True)
    for field in ('launch-id', 'session-id', 'child-id', 'client-cwd'):
        parser.add_argument('--' + field, required=True)
    args = vars(parser.parse_args(argv))
    operation = args.pop('operation')
    result = (inspect if operation == 'inspect' else record_return)(**args)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
