"""Canonical Codex hook boundary. Repository shims contain no routing policy.

Host registration fixes the exact checkout and adequate profile before a native
launch. Hooks consume the record; prompt text is never an authority record.
This boundary controls child tools, not the model already running as parent.
"""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Mapping

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cuhg.codex_hooks.child_lifecycle import LifecycleStore, _sandbox
from cuhg.codex_hooks.launch_preflight import launch_issues
from cuhg.errors import CuhError
from cuhg.models.execution_policy import load_owner_execution_policy, resolve_execution_policy
from cuhg.models.mixed_worker_routing import PROFILES, select_worker

LAUNCH_MARKER = re.compile(r'CUHG_LAUNCH_ID=([A-Za-z0-9_-]+)')
SPAWN_TOOLS = {'spawn_agent', 'collaboration.spawn_agent', 'multi_agent_v1spawn_agent'}
FOLLOWUP_TOOLS = {'followup_task', 'collaboration.followup_task', 'send_input', 'multi_agent_v1send_input'}
WAIT_TOOLS = {'wait', 'wait_agent', 'collaboration.wait_agent', 'multi_agent_v1wait_agent', 'functions.wait'}
# Native Codex hook events can flatten namespace + tool without a separator.
# Normalize only these exact aliases into the existing policy paths.
CLIENT_TOOL_ALIASES = {
    'collaborationspawn_agent': 'collaboration.spawn_agent',
    'collaborationfollowup_task': 'collaboration.followup_task',
    'collaborationwait_agent': 'collaboration.wait_agent',
}


def state_root() -> Path:
    # CODEX_HOME is the client's own configuration namespace, also used for an
    # isolated actual-client smoke. A hook request cannot choose this location.
    return Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'runtime/global-hooks/v1'


def _key(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _save(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')
    temporary.chmod(0o600)
    temporary.replace(path)


@contextmanager
def session_state(root: Path, session: str):
    root.mkdir(parents=True, exist_ok=True)
    with (root / (_key(session) + '.lock')).open('a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = root / (_key(session) + '.json')
        state = json.loads(path.read_text()) if path.exists() else {'session_id': session, 'events': [], 'tool_progress': {}}
        yield state
        _save(path, state)


def _decision(allow: bool, reason: str) -> dict:
    return {'hookSpecificOutput': {'hookEventName': 'PreToolUse',
        'permissionDecision': 'allow' if allow else 'deny', 'permissionDecisionReason': reason}}


def _context(event: str, text: str) -> dict:
    return {'hookSpecificOutput': {'hookEventName': event, 'additionalContext': text}}


def _tool_name(value: object) -> str:
    name = str(value)
    if name.startswith('mcp__'):
        name = name.rsplit('__', 1)[-1]
    return CLIENT_TOOL_ALIASES.get(name, name)


def _profile(input_: Mapping) -> tuple[object, object]:
    # Native clients expose either a named profile or explicit model/effort.
    named = PROFILES.get(input_.get('agent_type'))
    model = input_.get('model', named.get('model') if named else None)
    effort = input_.get('reasoning_effort', named.get('model_reasoning_effort') if named else None)
    if named and (model != named['model'] or effort != named['model_reasoning_effort']):
        return None, None
    return model, effort


def register(*, root: Path, repo_root: Path, worktree_root: Path, run_id: str,
             task_id: str, session_id: str, request: dict, capabilities: dict,
             validator_argv: list[str] | None = None, task_name: str | None = None) -> dict:
    from cuhg.codex_hooks.registration_commit import recovery_lock
    with recovery_lock(root):
        return _register(root=root,repo_root=repo_root,worktree_root=worktree_root,run_id=run_id,
                         task_id=task_id,session_id=session_id,request=request,capabilities=capabilities,
                         validator_argv=validator_argv,task_name=task_name)


def _corrected_review_sandbox(prior: Mapping, latest: Mapping | None,
                              request: Mapping, worktree_root: Path) -> bool:
    """A concluded sandbox binding failure is not evidence that the reviewer lacks quality."""
    if request.get('purpose') != 'review' or not isinstance(latest, Mapping) or \
            latest.get('status') != 'RUNTIME_MISMATCH' or \
            latest.get('decision') != 'BLOCKED_BY_RUNTIME' or \
            latest.get('claim_admitted') is not False:
        return False
    child = prior.get('child')
    if not isinstance(prior.get('claim'), Mapping) or not isinstance(child, Mapping) or \
            not prior['claim'].get('tool_use_id') or not child.get('child_id') or \
            latest.get('child_id') != child['child_id']:
        return False
    if any(not isinstance(exit, Mapping) or exit.get('status') != 'RUNTIME_MISMATCH' or
           not isinstance(exit.get('runtime_observation'), Mapping) or
           exit['runtime_observation'].get('reason') != 'CHILD_SANDBOX_MISMATCH'
           for exit in prior.get('exits', {}).values()):
        return False
    runtime = latest.get('runtime_observation')
    if not isinstance(runtime, Mapping) or runtime.get('state') != 'MISMATCH' or \
            runtime.get('reason') != 'CHILD_SANDBOX_MISMATCH' or \
            not runtime.get('transcript_sha256'):
        return False
    observed = runtime.get('observed')
    profile = prior.get('profile')
    identity = prior.get('identity')
    if not all(isinstance(value, Mapping) for value in (observed, profile, identity)):
        return False
    if observed.get('model') != profile.get('model') or \
            observed.get('effort') != profile.get('effort') or \
            observed.get('cwd') != identity.get('worktree_root') or \
            identity.get('worktree_root') != str(worktree_root.resolve()):
        return False
    previous = _sandbox(profile.get('sandbox_policy'))
    actual = _sandbox(observed.get('sandbox_policy'))
    corrected = _sandbox(request.get('sandbox_policy'))
    return previous is not None and actual is not None and previous != actual and corrected == actual


def _register(*, root: Path, repo_root: Path, worktree_root: Path, run_id: str,
             task_id: str, session_id: str, request: dict, capabilities: dict,
             validator_argv: list[str] | None = None, task_name: str | None = None) -> dict:
    """Host-only planning entrypoint. Uses the existing adequate-worker selector."""
    if _sandbox(request.get('sandbox_policy')) is None:
        raise CuhError('REGISTRATION_SANDBOX_REQUIRED',
            'Freeze the actual client sandbox_policy before registration; do not infer or backfill it.', {})
    policy = resolve_execution_policy(request.get('execution_policy'), owner_default=load_owner_execution_policy())
    store = LifecycleStore(root / 'lifecycle')
    existing = [r for r in store.list_launches() if r['task_id']==task_id and r['run_id']==run_id
                and r['identity']['repo_root']==str(repo_root.resolve())]
    from cuhg.models.routing_activation import _rows
    routing_root = root / 'routing'
    opportunity = request.get('routing_opportunity_id') or ('native_' + hashlib.sha256(
        json.dumps([str(repo_root.resolve()), run_id, task_id, session_id]).encode()).hexdigest())
    phases = request.get('routing_phases', ['REVIEW' if request.get('purpose') == 'review' else 'IMPLEMENTATION'])
    effective = {**request, 'execution_policy': policy}
    continuation_context = request.get('continuation_context')
    initial = select_worker(effective, capabilities, [])
    registered = next((row for row in _rows(routing_root/'routing-opportunities.jsonl') if row['opportunity_id']==opportunity), None)
    # Author and reviewer are distinct phases of the same task. Keep legacy
    # phase receipts and the shared native launch budget, without colliding
    # with an already frozen author opportunity.
    if (registered is not None and registered['phases']!=sorted(set(phases))
            and not request.get('routing_opportunity_id') and existing
            and all(r.get('exits') or r.get('terminal_resolution') for r in existing)):
        opportunity += '_' + hashlib.sha256(json.dumps(sorted(set(phases))).encode()).hexdigest()[:12]
        registered = next((row for row in _rows(routing_root/'routing-opportunities.jsonl') if row['opportunity_id']==opportunity), None)
    if registered is not None and registered['phases']!=sorted(set(phases)):
        raise CuhError('ROUTING_OPPORTUNITY_CHANGED','Opportunity phases are frozen.',{})
    for prior in existing:
        if (prior['session_id']==session_id and initial.get('profile_id')==prior['profile'].get('profile_id')
                and prior.get('task_name')==task_name and prior.get('validator_argv')==validator_argv):
            launch=store.register_launch(repo_root=repo_root,worktree_root=worktree_root,run_id=run_id,
                task_id=task_id,session_id=session_id,profile={**initial, 'sandbox_policy': request.get('sandbox_policy')},validator_argv=validator_argv,task_name=task_name,continuation_context=continuation_context,
                _routing_registration={'routing_root':str(routing_root),'opportunity_id':opportunity,'phases':phases})
            return {'registered':True,'idempotent':True,'route':initial,'launch':launch,
                    'message_prefix':'CUHG_LAUNCH_ID='+launch['launch_id'], 'task_name':task_name}
    local_exclusion=None
    if request.get('author_routing_policy')=='SCOPED_LOCAL_FIRST_V1' and request.get('purpose') in {'implement','write'} and request.get('local_eligible') is False and 'LOCAL_MODEL' in policy.get('provider_allowlist',[]):
        from cuhg.models.author_routing import exclusion
        try:
            local_exclusion=exclusion(effective,task_id=task_id,repo_root=repo_root)
        except CuhError as error:
            if error.code not in {'LOCAL_EXCLUSION_EVIDENCE_REQUIRED','LOCAL_EXCLUSION_REASON_REQUIRED'}:
                raise
            return {'registered':False,'route':error.details}
    history=[]
    for item in existing:
        exits=item.get('exits',{})
        latest=exits.get(item.get('last_exit_digest'))
        # Canonical JSON sorts digest keys; that order is not execution order.
        # Old records without an observed latest pointer cannot imply success.
        if not exits:
            status='DISPATCH_RESERVED'
        elif latest and latest['status']=='VALIDATOR_PASSED':
            status='VALIDATED'
        elif _corrected_review_sandbox(item, latest, effective, worktree_root):
            status='RUNTIME_BINDING_CORRECTED'
        else:
            status='FAILED'
        history.append(dict(item['profile'],status=status))
    decision = select_worker(effective, capabilities, history)
    if local_exclusion is not None:
        decision['local_exclusion']=local_exclusion
    if decision['action'] != 'SPAWN_CODEX_SUBAGENT':
        return {'registered': False, 'route': decision}
    # A rejected request or non-native route has no native reservation. Do not
    # freeze its phases before selection succeeds: the same logical task must
    # remain correctable without deleting a ledger or inventing a new task ID.
    launch = store.register_launch(repo_root=repo_root, worktree_root=worktree_root,
        run_id=run_id, task_id=task_id, session_id=session_id, profile={**decision, 'sandbox_policy': request.get('sandbox_policy')},
        validator_argv=validator_argv, task_name=task_name, continuation_context=continuation_context,
        _routing_registration={'routing_root':str(routing_root),'opportunity_id':opportunity,'phases':phases})
    return {'registered': True, 'route': decision, 'launch': launch,
            'message_prefix': 'CUHG_LAUNCH_ID=' + launch['launch_id'], 'task_name':task_name}


def semantic_progress(path: Path) -> str:
    """Only completed work output, not timestamps/context/usage metadata."""
    completed = []
    for line in path.read_text().splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        payload = row.get('payload', {})
        kind = payload.get('type')
        if row.get('type') == 'response_item' and kind in {'function_call_output', 'custom_tool_call_output'}:
            completed.append((kind, payload.get('call_id'), payload.get('output')))
        elif row.get('type') == 'event_msg' and kind == 'task_complete':
            completed.append((kind, payload.get('last_agent_message')))
    return hashlib.sha256(json.dumps(completed, sort_keys=True).encode()).hexdigest()


def dispatch(event: Mapping, *, root: Path | None = None, local_dispatcher=None) -> dict:
    from cuhg.observability.telemetry import observe_hook
    observe_hook(event)
    root = state_root() if root is None else Path(root)
    name = str(event.get('hook_event_name', ''))
    session = event.get('session_id')
    if not isinstance(session, str) or not session:
        raise ValueError('HOOK_SESSION_ID_REQUIRED')
    store = LifecycleStore(root / 'lifecycle')
    tool = _tool_name(event.get('tool_name', ''))
    input_ = event.get('tool_input', {})
    if not isinstance(input_, Mapping):
        raise ValueError('HOOK_TOOL_INPUT_INVALID')
    # Child validation can run external bounded processes.  Keep the session
    # journal lock for its small state append only, so another hook in the same
    # session can continue while the per-launch lifecycle lock owns validation.
    exit_receipt = None
    if name == 'SubagentStop':
        exit_receipt = store.child_exit(session_id=session, child_id=str(event.get('agent_id', '')), event=dict(event))
    with session_state(root / 'sessions', session) as state:
        # Native child tools can share the parent's session_id while carrying
        # their own agent_id. Classify this event from the existing binding;
        # never turn the shared parent journal into a child session. Task-name
        # aliases are followup targets, not the tool event's actor identity.
        tool_state = state
        agent = event.get('agent_id')
        if name == 'PreToolUse' and isinstance(agent, str) and agent:
            binding = store.get_child(session_id=session, child_id=agent)
            if binding is not None and binding['child']['child_id'] == agent:
                tool_state = {**state, 'is_child': True}
        result: dict = {}
        status = 'NO_POLICY_ACTION'
        if name == 'SessionStart':
            try:
                from cuhg.models.continuous_policy import prompt_guidance
                result = _context(name, prompt_guidance())
            except (OSError, ValueError):
                result = {}
            status = 'CONTINUOUS_SESSION_CONTEXT'
        elif name == 'UserPromptSubmit':
            policy = resolve_execution_policy(None, owner_default=load_owner_execution_policy())
            state.update(cwd=str(event.get('cwd', '')), policy=policy, is_child=bool(event.get('agent_id')))
            command = str(Path(__file__).resolve().parents[3] / 'scripts/codex_harness/global_hook.py')
            state['author_route_turn']=str(event.get('turn_id') or _key(str(event.get('prompt',''))))
            author_command=str(Path(command).with_name('author_route.py'))
            text = ('[GLOBAL_ROUTING_BOUNDARY/v1]\n'
                f"policy: {policy['execution_mode']}/{policy['routing_objective']}\n"
                f'session_id: {session}\nworktree_root: {event.get("cwd")}\n'
                f'For a NEW child only, register its exact worktree/run/task and frozen validator with: python {command} register --help\n'
                'Register --task-name and use that exact task_name in spawn_agent, with the returned '
                'CUHG_LAUNCH_ID marker, exact model/effort and fresh context. The task_name binds '
                'the registration when the client transports message as an opaque value. '
                'Direct collaboration is intercepted; default-inheriting or unregistered children are denied. '
                'Choose an adequate low-usage route after the quality gate; latency is secondary. '
                'Local eligible frozen tasks use delegate_scientific_task.py; placement alone is not role admission. '
                'The current parent model is unchanged. Repeated unchanged waits stop at NO_PROGRESS_EVENT.\n'
                '[/GLOBAL_ROUTING_BOUNDARY/v1]')
            text += '\nBefore parent implementation edits, select useful local work via execute_task.py/delegate_scientific_task.py or record a concrete scoped exclusion (no new approval). Exact author-route command: python '+author_command+' --root '+str(root)+' --session '+session+' --turn '+state['author_route_turn']+' --repo '+str(event.get('cwd',''))+' --task <same-task-id> --reason <HOST_REQUIRED|CROSS_MODULE_INTEGRATION|SMALL_DIRECT_CHANGE|LOCAL_UNAVAILABLE|LOCAL_FAILED|LOCAL_CANDIDATE_INTEGRATION|VALIDATION_AND_RELEASE> --detail <concrete-reason> --path <each-relative-path> [--evidence <existing-local-receipt>]. Registry availability is not execution; do not fabricate local calls or skip feasible useful local subtasks.'
            text += '\nExact CAS/kernel validators do not inherently exclude local candidate generation. Before local_eligible=false, inspect existing availability and task/role qualification evidence for a useful bounded candidate; unknown qualification is not failed qualification. Native registration local_exclusion.evidence_ref must reference an assessment bound to the registration repo/task and inspected role/profile/model, with structured observations and source hashes (docs/LOCAL_EXCLUSION_EVIDENCE.md). Hashes and prose alone do not establish exclusion. INSPECT_LOCAL_EVIDENCE is a read-only lookup, not an inference or approval request. If inspection finds no safe useful qualified or already-authorized exploratory candidate, record QUALIFICATION_UNKNOWN/NO_SAFE_USEFUL_CANDIDATE and continue hosted without claiming local failure. Preserve explicit execution-policy exclusions and candidate-specific unavailable execution or observed failures. Local candidates, deterministic validation and independent hosted review retain separate authority; this lookup grants no scientific admission.'
            text += '\nFor multi-file or new-file payloads use execute_task.py prepare-workspace --repo-root <repo> --task-json <intent>, then run the prepared task with explicit managed profile qualification and observed native capabilities. HOST_REQUIRED, CROSS_MODULE_INTEGRATION, LOCAL_UNAVAILABLE and LOCAL_FAILED require --assessment-json with candidate_paths, route, reason, task-bound native_request, observed native_capabilities and existing native_history. Direct HOST_AUTHORITY also supplies host_decision and observed host_author; see docs/ROUTING_DISCOVERY_REPAIR_20260930.md for the complete schema. The selector derives the smaller author and higher review plan. CODEX_SUBAGENT_PENDING is planning, never permission for a parent edit. CODEX_ONLY permits smaller native authors and higher independent reviewers. Native review sandbox inherits the live parent turn; a profile TOML alone is not read-only runtime proof.'
            registered = [r for r in store.list_launches(session) if not r.get("exits")][-8:]
            if registered:
                text += '\nExisting Host registrations (reuse these; do NOT register again):\n' + json.dumps([
                    {'marker':'CUHG_LAUNCH_ID='+r['launch_id'], 'model':r['profile']['model'],
                     'effort':r['profile']['model_reasoning_effort'], 'worktree':r['identity']['worktree_root'],
                     'task_id':r['task_id'], 'task_name':r.get('task_name'), 'child_id':(r.get('child') or {}).get('child_id')} for r in registered])
            if local_dispatcher is not None:
                try:
                    local = local_dispatcher(event)
                    output = getattr(local, 'output', None)
                    extra = output.get('hookSpecificOutput', {}).get('additionalContext', '') if isinstance(output, dict) else ''
                    if extra:
                        text += '\n' + extra
                except Exception as error:
                    # Boundary diagnosis is private and typed, never exception
                    # messages (which can contain prompts, paths or credentials).
                    state['local_dispatch_failure'] = {'type': type(error).__name__,
                        'code': getattr(error, 'code', 'UNCLASSIFIED'), 'source': str(Path(__file__).resolve())}
                    text += '\nlocal_dispatch: HOOK_BOUNDARY_FAILURE; native routing remains available; private diagnostic recorded.'
            try:
                from cuhg.models.continuous_policy import prompt_guidance
                guidance = prompt_guidance()
                if guidance:
                    text += '\n' + guidance
            except (OSError, ValueError):
                text += '\ncontinuous_policy: OBSERVATION_FAILED; continue with current task authority.'
            result, status = _context(name, text), 'ROUTING_INTERCEPTION_ACTIVE'
        elif name == 'PreToolUse' and tool in SPAWN_TOOLS:
            if tool_state.get('is_child'):
                state['events'].append({'event':name,'tool':tool,'status':'NESTED_DISPATCH_DENIED'})
                return _decision(False,'NESTED_DISPATCH_FORBIDDEN: return to the existing Host coordinator.')
            markers = set(LAUNCH_MARKER.findall(str(input_.get('message', ''))))
            task_name = input_.get('task_name')
            launch = None
            ambiguous = len(markers) > 1
            if len(markers) == 1:
                launch = store.get_launch(next(iter(markers)))
                if launch is None:
                    raise ValueError('UNKNOWN_LAUNCH_ID')
            elif not markers and isinstance(task_name, str) and task_name:
                # Some clients expose message only as an opaque transport value.
                # Resolve the separately visible name against Host registrations;
                # never decode prompt data or select an arbitrary pending launch.
                candidates = [r for r in store.list_launches(session) if r.get('task_name') == task_name]
                ambiguous = len(candidates) > 1
                if len(candidates) == 1:
                    launch = candidates[0]
            if ambiguous:
                result, status = _decision(False, 'ROUTING_LAUNCH_AMBIGUOUS: use one explicit launch marker or a uniquely registered task_name.'), 'AMBIGUOUS_SPAWN_DENIED'
            elif launch is None:
                result, status = _decision(False, 'ROUTING_REGISTRATION_REQUIRED: register exact worktree/run/task before direct collaboration.'), 'UNREGISTERED_SPAWN_DENIED'
            else:
                model, effort = _profile(input_)
                profile = launch['profile']
                if task_name is not None and launch.get('task_name') is not None and task_name != launch['task_name']:
                    result, status = _decision(False, 'ROUTING_TASK_NAME_MISMATCH: use the exact registered task_name.'), 'TASK_NAME_MISMATCH_DENIED'
                elif launch['session_id'] != session or (model, effort) != (profile['model'], profile['model_reasoning_effort']):
                    result, status = _decision(False, 'ROUTING_PROFILE_MISMATCH: use the exact validated model and effort.'), 'PROFILE_MISMATCH_DENIED'
                elif input_.get('fork_context') is True or input_.get('fork_turns') not in (None, 'none', '0', 0):
                    result, status = _decision(False, 'ROUTING_CONTEXT_INHERITANCE_DENIED: use the bounded fresh execution brief.'), 'CONTEXT_INHERITANCE_DENIED'
                elif not isinstance(event.get('tool_use_id'), str) or not event['tool_use_id'].strip():
                    result, status = _decision(False, 'ROUTING_TOOL_ID_REQUIRED: a nonempty native tool-use identity is required before claiming a launch.'), 'TOOL_ID_MISSING_DENIED'
                elif issues := launch_issues(launch, event.get('cwd'), event=event):
                    result, status = _decision(False, issues[0] +
                        ': open the client at the registered worktree and reconcile its frozen sandbox/source; '
                        'native children inherit live parent permissions after role settings. '
                        'Use a read-only client for an enforced read-only review; prompt paths or subprocess cwd '
                        'do not change child runtime identity.'), 'CLIENT_PREFLIGHT_DENIED'
                else:
                    store.claim_launch(launch['launch_id'], session_id=session,
                        tool_use_id=event['tool_use_id'])
                    result, status = _decision(True, 'BUDGET_ROUTE_VALIDATED:' + profile['profile_id']), 'BUDGET_ROUTE_VALIDATED'
        elif name == 'PreToolUse' and tool in FOLLOWUP_TOOLS:
            if tool_state.get('is_child'):
                return _decision(False, 'NESTED_DISPATCH_FORBIDDEN: return to the existing Host coordinator.')
            child = input_.get('target', input_.get('id', input_.get('agent_id')))
            try:
                binding = store.get_child(session_id=session, child_id=str(child))
                if binding is None or binding['session_id'] != session:
                    raise ValueError('CHILD_SESSION_MISMATCH')
                if binding.get('child', {}).get('runtime_observation', {}).get('state') != 'MATCH':
                    raise ValueError('CHILD_RUNTIME_UNVERIFIED')
                context = binding.get('continuation_context')
                from direct_author_continuation import is_direct_author, consume as consume_author
                if is_direct_author(binding):
                    consume_author(root, launch_id=binding['launch_id'], session_id=session,
                        child_id=binding['child']['child_id'], client_cwd=event.get('cwd'),
                        tool_use_id=event.get('tool_use_id'))
                else:
                    if not isinstance(context, dict):
                        raise ValueError('CONTINUATION_RESOURCE_BINDING_REQUIRED')
                    from cuhg.models.native_workspace_job import consume_continuation
                    consume_continuation(Path(context['run_dir']), selection_id=context['selection_id'],
                        thread_id=binding['child']['child_id'], model=binding['profile']['model'],
                        effort=binding['profile']['effort'], tool_use_id=str(event.get('tool_use_id', '')))
                result, status = _decision(True, 'RESERVED_CHILD_CONTINUATION'), 'RESERVED_CHILD_CONTINUATION'
            except (CuhError, ValueError, TypeError, KeyError, FileNotFoundError):
                result, status = _decision(False, 'CHILD_CONTINUATION_NOT_RESERVED: reconcile identity, usage and the formal continuation reservation.'), 'UNBOUND_CHILD_DENIED'
        elif name == 'PreToolUse' and tool in WAIT_TOOLS and not input_.get('chars'):
            targets = input_.get('targets', [input_.get('target', input_.get('cell_id', input_.get('session_id', 'unknown')))])
            if not isinstance(targets, list):
                targets = [targets]
            progress = {}
            for target in targets:
                try:
                    child = store.get_child(session_id=session, child_id=str(target))
                    if child is None:
                        raise ValueError('UNBOUND_CHILD')
                    runtime = child.get('child', {})
                    transcript = runtime.get('transcript_ref')
                    observed = None
                    if transcript and Path(transcript).is_file():
                        observed = semantic_progress(Path(transcript))
                    progress[str(target)] = hashlib.sha256(json.dumps(
                        {'exits': list(child.get('exits', {})), 'runtime_progress': observed},
                        sort_keys=True).encode()).hexdigest()
                except (CuhError, ValueError, TypeError, KeyError, FileNotFoundError):
                    progress[str(target)] = state['tool_progress'].get(str(target), 'UNOBSERVED')
            observation = store.observe_wait(session_id=session, targets=targets,
                progress_tokens=progress)
            status = observation.get('code', observation.get('status', 'WAIT_OBSERVED'))
            result = _decision(status != 'NO_PROGRESS_EVENT',
                'NO_PROGRESS_EVENT: diagnose the unchanged operation; do not poll again blindly.' if status == 'NO_PROGRESS_EVENT' else 'WAIT_WITHIN_PROGRESS_BOUND')
        elif name == 'SubagentStart':
            binding = store.bind_child(session_id=session, child_id=str(event.get('agent_id', '')), event=dict(event))
            result = _context(name, '[GLOBAL_CHILD_IDENTITY/v1]\n' + json.dumps({**binding['identity'], 'run_id':binding['run_id'], 'task_id':binding['task_id'], 'child_id':binding['child']['child_id']}) +
                '\nUse only the exact worktree. Return the bounded task result; never inspect another checkout.\n')
            status = 'CHILD_EXACT_IDENTITY_BOUND'
        elif name == 'SubagentStop':
            receipt = exit_receipt
            assert isinstance(receipt, Mapping)
            status = receipt.get('code', receipt.get('status', 'CHILD_EXIT_RECORDED'))
            if receipt.get('decision') in ('block', 'BLOCKED_BY_VALIDATOR', 'BLOCKED_BY_RUNTIME') or receipt.get('status') in ('FAILED', 'BLOCKED', 'VALIDATOR_FAILED'):
                result = {} if event.get('stop_hook_active') else {'decision': 'block', 'reason': str(receipt.get('reason', status))}
        elif name == 'PostToolUse' and tool in SPAWN_TOOLS:
            response = event.get('tool_response')
            # Only an explicit native terminal receipt enters this path. Generic
            # tool errors and successful/unknown dispatches retain the claim.
            if isinstance(response, Mapping) and response.get('schema') == 'cuhg-native-no-child/v1':
                if response.get('session_id') != session or response.get('tool_use_id') != event.get('tool_use_id'):
                    raise CuhError('NATIVE_OUTCOME_IDENTITY_MISMATCH', 'PostToolUse outcome belongs to another tool call.', {})
                status = store.reconcile_unbound_claim(evidence=response)['status']
        elif name == 'PostToolUse' and tool in WAIT_TOOLS:
            # Only substantive output is progress; elapsed time and a new tool
            # call ID do not reset the bound.
            response = event.get('tool_response', {})
            output = response.get('output', '') if isinstance(response, Mapping) else ''
            if output:
                target = str(input_.get('cell_id', input_.get('session_id', input_.get('target', 'unknown'))))
                state['tool_progress'][target] = hashlib.sha256(str(output).encode()).hexdigest()
        if name=='PreToolUse' and tool not in SPAWN_TOOLS | FOLLOWUP_TOOLS | WAIT_TOOLS:
            from cuhg.models.author_routing import check_edit
            reason=check_edit(event,tool_state,root,tool,input_)
            if reason:
                result=_decision(False,reason);status='AUTHOR_ROUTE_REQUIRED'
        if name=='PostCompact':
            state.pop('context_index_delivered',None)
            state['context_restore_pending']=True
        if name in {'SessionStart','UserPromptSubmit','PostToolUse'} or (name=='PreToolUse' and state.get('context_restore_pending')):
            try:
                from cuhg.observability.telemetry import enabled, spool_root
                from cuhg.models.context_manager import handoff_for_event
                if enabled():
                    handoff = handoff_for_event(event, spool_root().parent/'context-manager',
                        delivered=state.get('context_index_delivered') if name == 'PostToolUse' else None)
                    if handoff['text'] and (handoff['digest'] or name != 'PostToolUse'):
                        existing = result.get('hookSpecificOutput',{}).get('additionalContext','')
                        output=result.setdefault('hookSpecificOutput',{'hookEventName':name})
                        output['additionalContext']=existing+'\n'+handoff['text']
                    if handoff['digest']:
                        state['context_index_delivered'] = handoff['digest']
                        state.pop('context_restore_pending',None)
            except Exception:
                pass  # Context is replaceable; hook lifecycle decisions stay intact.
        state['events'].append({'event': name, 'tool': tool, 'status': status,
            'turn_id': event.get('turn_id'), 'child_id': event.get('agent_id'),
            'source_path':str(Path(__file__).resolve()), 'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
        return result


def main(argv=None) -> int:
    if argv == ['--self-check']:
        print('GLOBAL_ROUTING_HOOK_SELF_CHECK_PASS')
        return 0
    event = {}
    try:
        raw = sys.stdin.read(1024 * 1024 + 1)
        if len(raw.encode()) > 1024 * 1024:
            raise ValueError('HOOK_INPUT_TOO_LARGE')
        event = json.loads(raw)
        if not isinstance(event, dict):
            raise ValueError('HOOK_INPUT_NOT_OBJECT')
        from cuhg.models.auto_dispatch import dispatch_user_prompt
        from cuhg.models.task_entrypoint import routing_root_for_event
        output = dispatch(event, local_dispatcher=lambda value: dispatch_user_prompt(
            value, opportunity_root=routing_root_for_event(value, legacy_roots=(state_root() / 'routing',))))
    except Exception as error:
        name = event.get('hook_event_name') if isinstance(event, dict) else None
        detail = error.code if isinstance(error, CuhError) else type(error).__name__
        reason = 'GLOBAL_HOOK_IDENTITY_OR_STATE_UNVERIFIED:' + detail
        if name == 'PreToolUse':
            output = _decision(False, reason)
        elif name == 'SubagentStop':
            # A repeated block cannot become admission. Native stop retry is
            # bounded: preserve NON_ADMITTED then return control to the Host.
            output = {} if event.get('stop_hook_active') else {'decision': 'block', 'reason': reason}
        elif name == 'SubagentStart':
            # SubagentStart is advisory in Codex; only PreToolUse can deny launch.
            output = {'systemMessage': reason, **_context('SubagentStart', reason + ': execution is unverified; return to the Host for reconciliation.')}
        else:
            output = _context('UserPromptSubmit', reason)
        _save(state_root() / 'errors' / (_key(str(event.get('session_id', 'unknown')) + str(event.get('turn_id', ''))) + '.json'),
            {'event': name, 'type': type(error).__name__, 'code': getattr(error, 'code', 'UNVERIFIED'),
             'source': str(Path(__file__).resolve()), 'result': 'NON_ADMITTED'})
    print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
