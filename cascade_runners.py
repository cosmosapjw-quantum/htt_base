"""Execution engines for the cost router, plus the CLI.

  batch  (default): Message Batches API, 50% off, stacks with prompt caching.
                    Rounds: every pending task goes into one batch; verified
                    failures move up one rung and form the next round.
                    Latency is minutes to hours, so it suits "no rush" work.
  async           : streaming Messages API with per-model adaptive concurrency,
                    for work that needs an answer sooner (full price).

Both share one settle step, so the cheap-spend cap and escalation rules are
identical. Every attempt is written to the ledger; state is rebuilt from the
ledger, so a crashed run resumes with --resume and never pays twice.

API key: the key must belong to the Console organization that holds the credits
(plan login and Claude Code usage are billed elsewhere). Read from ANTHROPIC_API_KEY.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import time
from typing import Optional

from cost_router import Budget, Ledger, Policy, TaskState, load_config, usd_cost

DEFAULT_CONC = {"claude-haiku-5-5": 16, "claude-sonnet-5-5": 12,
                "claude-opus-5-5": 8, "claude-fable-5-1": 4}  # Fable has the smallest rate-limit bucket
RESERVE_FACTOR = 1.5   # reserve 1.5x the estimate per call; settle to the real cost afterwards
INFRA_RETRIES = 2


# ---------------------------------------------------------------- verifiers
class CommandVerifier:
    """Run a command with the model output on stdin. Exit 0 = pass.
    signature = last stdout line (identifies a repeated failure); detail feeds the retry prompt."""

    def __init__(self, cmd: list, timeout: int = 600):
        self.cmd, self.timeout = cmd, timeout

    def __call__(self, task: dict, text: str):
        try:
            p = subprocess.run(self.cmd, input=text, capture_output=True, text=True, timeout=self.timeout)
        except subprocess.TimeoutExpired:
            return False, "timeout", "verifier timed out"
        out = (p.stdout or "").strip().splitlines()
        sig = (out[-1][:80] if out else f"rc{p.returncode}")
        return p.returncode == 0, ("" if p.returncode == 0 else sig), ((p.stdout or "") + (p.stderr or ""))[-2000:]


def attach_verifiers(tasks: list[dict]) -> None:
    for t in tasks:
        v = t.get("verifier")
        if v and "_verify" not in t:
            t["_verify"] = CommandVerifier(v["cmd"], v.get("timeout", 600))


# ---------------------------------------------------------------- request helpers
def build_params(policy: Policy, rung, task: dict, user_text_: str, ttl: str) -> dict:
    p = {"model": rung.model, "max_tokens": policy.max_tokens(rung),
         "messages": [{"role": "user", "content": user_text_}],
         "output_config": {"effort": rung.effort}}
    if task.get("system"):
        p["system"] = [{"type": "text", "text": task["system"],
                        "cache_control": {"type": "ephemeral", "ttl": ttl}}]
    if rung.thinking_disabled:
        p["thinking"] = {"type": "disabled"}
    return p


def text_of(msg) -> str:
    return "".join(getattr(b, "text", "") or "" for b in msg.content if getattr(b, "type", None) == "text")


def user_text(task: dict, repair: str) -> str:
    if not repair:
        return task["prompt"]
    return task["prompt"] + "\n\n[A previous attempt failed verification. Verifier output:]\n" + repair


def new_states(policy: Policy, tasks: list[dict]) -> dict:
    states = {}
    for t in tasks:
        text = (t.get("system") or "") + t["prompt"]
        states[t["id"]] = policy.plan(t["id"], t.get("klass", "routine"), text, t.get("_verify") is not None)
    return states


def rebuild_from_ledger(policy: Policy, states: dict, ledger: Ledger):
    """Resume: replay recorded attempts to restore status, spend and the next rung."""
    nxt = {tid: st.start for tid, st in states.items()}
    done_cids = set()
    for e in ledger.entries():
        st = states.get(e.get("task_id"))
        if not st or e.get("rung") not in policy.by_name:
            continue
        if e.get("cid"):
            done_cids.add(e["cid"])
        r = policy.by_name[e["rung"]]
        ok = e.get("success")
        st.attempts.append((r.idx, ok, e.get("sig", "")))
        st.spent_total += e.get("usd", 0.0)
        if r.idx < st.terminal:
            st.spent_nonterminal += e.get("usd", 0.0)
        else:
            st.terminal_attempts += 1
        if ok is True:
            st.status = "SOLVED"
        elif ok is None:
            st.status = "DONE_UNVERIFIED"
        else:
            n = policy.next_rung(st, r.idx, e.get("sig", ""))
            st.last_sig = e.get("sig", "")
            if n is None:
                st.status = "FAILED"
            else:
                nxt[st.task_id] = n
    return nxt, done_cids


def settle(policy, ledger, st: TaskState, task: dict, rung, text: str, usage, mode: str, cid: str):
    """Record one finished attempt, verify it, and update the task. Returns (ok, detail, next_rung)."""
    usd = usd_cost(usage, rung.model, batch=(mode == "batch"), ttl=policy.cfg["cache_ttl"])
    verify = task.get("_verify")
    ok, sig, detail = (None, "", "") if verify is None else verify(task, text)
    in_tok = (getattr(usage, "input_tokens", 0) or 0) + (getattr(usage, "cache_read_input_tokens", 0) or 0) \
        + (getattr(usage, "cache_creation_input_tokens", 0) or 0)
    ledger.record({"task_id": st.task_id, "klass": st.klass, "rung": rung.name, "model": rung.model,
                   "effort": rung.effort, "mode": mode, "cid": cid, "in_tokens": in_tok,
                   "est_in": st.in_tokens, "out_tokens": getattr(usage, "output_tokens", 0),
                   "usd": usd, "success": ok, "sig": sig})
    st.attempts.append((rung.idx, ok, sig))
    st.spent_total += usd
    if rung.idx < st.terminal:
        st.spent_nonterminal += usd
    else:
        st.terminal_attempts += 1
    if ok is True:
        st.status = "SOLVED"
        return ok, detail, None
    if ok is None:
        st.status = "DONE_UNVERIFIED"
        return ok, detail, None
    nxt = policy.next_rung(st, rung.idx, sig)
    st.last_sig = sig
    if nxt is None:
        st.status = "FAILED"
    return ok, detail, nxt


def write_results(path: Optional[str], states: dict, outputs: dict):
    if not path:
        return
    with open(path, "w") as f:
        for tid, st in states.items():
            o = outputs.get(tid, {})
            f.write(json.dumps({"id": tid, "status": st.status, "klass": st.klass,
                                "rung": o.get("rung"), "spent_usd": round(st.spent_total, 6),
                                "nonterminal_usd": round(st.spent_nonterminal, 6),
                                "text": o.get("text")}, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- batch cascade
def run_batch_cascade(client, tasks, cfg, ledger, budget, *, poll_s=30, out_path=None,
                      resume=False, sleep=time.sleep, log=print, chunk=5000):
    policy = Policy(cfg, ledger, batch=True)
    by_id = {t["id"]: t for t in tasks}
    order = {t["id"]: i for i, t in enumerate(tasks)}
    states = new_states(policy, tasks)
    if resume:
        nxt, done_cids = rebuild_from_ledger(policy, states, ledger)
    else:
        nxt, done_cids = {tid: st.start for tid, st in states.items()}, set()
    repair, infra, outputs = {}, {}, {}
    ttl = cfg["cache_ttl"]

    while True:
        pending = [tid for tid, st in states.items() if st.status == "PENDING"]
        if not pending:
            break
        reqs, meta = [], {}
        for tid in pending:
            st, r = states[tid], policy.rungs[nxt[tid]]
            res_usd = policy.est_cost(r, st.klass, st.in_tokens) * RESERVE_FACTOR
            if not budget.reserve(res_usd):
                st.status = "BUDGET_STOP"
                continue
            cid = f"t{order[tid]}_r{r.idx}_a{len(st.attempts)}_i{infra.get(tid, 0)}"
            meta[cid] = (tid, r, res_usd)
            reqs.append({"custom_id": cid, "params": build_params(policy, r, by_id[tid],
                                                                  user_text(by_id[tid], repair.get(tid, "")), ttl)})
        if not reqs:
            break
        log(f"round: submitting {len(reqs)} requests; budget available ${budget.available():.2f}")
        seen = set()
        for k in range(0, len(reqs), chunk):
            batch = client.messages.batches.create(requests=reqs[k:k + chunk])
            while True:
                b = client.messages.batches.retrieve(batch.id)
                if b.processing_status == "ended":
                    break
                sleep(poll_s)
            for res in client.messages.batches.results(batch.id):
                cid = res.custom_id
                if cid not in meta or cid in done_cids:
                    continue
                seen.add(cid)
                tid, r, res_usd = meta[cid]
                st = states[tid]
                budget.release(res_usd)
                if res.result.type == "succeeded":
                    msg = res.result.message
                    text = text_of(msg)
                    ok, detail, n = settle(policy, ledger, st, by_id[tid], r, text, msg.usage, "batch", cid)
                    if ok is not False:
                        outputs[tid] = {"rung": r.name, "text": text}
                    elif n is not None:
                        nxt[tid] = n
                        repair[tid] = detail
                else:  # errored / expired / canceled are not billed; retry same rung a bounded number of times
                    etype = getattr(getattr(getattr(res.result, "error", None), "error", None), "type", "")
                    infra[tid] = infra.get(tid, 0) + 1
                    if etype == "invalid_request_error" or infra[tid] > INFRA_RETRIES:
                        st.status = "ERROR"
        for cid, (tid, r, res_usd) in meta.items():  # reservations whose result never arrived
            if cid not in seen:
                budget.release(res_usd)
        write_results(out_path, states, outputs)
    write_results(out_path, states, outputs)
    return states, outputs


# ---------------------------------------------------------------- async runner
class AdaptiveLimiter:
    """Start low and ramp up (rate limits punish sudden spikes); halve on 429."""

    def __init__(self, max_conc: int, start: int = 2):
        self.max, self.limit, self.inflight, self.streak = max_conc, min(start, max_conc), 0, 0
        self.cond = asyncio.Condition()

    async def acquire(self):
        async with self.cond:
            await self.cond.wait_for(lambda: self.inflight < self.limit)
            self.inflight += 1

    async def release(self):
        async with self.cond:
            self.inflight -= 1
            self.cond.notify_all()

    def on_success(self):
        self.streak += 1
        if self.streak >= self.limit and self.limit < self.max:
            self.limit, self.streak = self.limit + 1, 0

    def on_throttle(self):
        self.limit, self.streak = max(1, self.limit // 2), 0


async def _stream_call(aclient, params, limiter, errors):
    RateLimitError, BadRequestError = errors
    while True:
        await limiter.acquire()
        retry_wait = None
        try:
            async with aclient.messages.stream(**params) as s:  # streaming avoids the SDK's non-streaming size guard
                msg = await s.get_final_message()
            limiter.on_success()
            return msg
        except RateLimitError as e:
            body = getattr(e, "body", None) or {}
            err = body.get("error", {}) if isinstance(body, dict) else {}
            if (err.get("details") or {}).get("error_code") == "enforced_spend_limit_reached":
                raise
            limiter.on_throttle()
            hdrs = getattr(getattr(e, "response", None), "headers", {}) or {}
            retry_wait = float(hdrs.get("retry-after", 1))
        except BadRequestError as e:
            if "thinking" in params and "thinking" in str(e).lower():
                params = {k: v for k, v in params.items() if k != "thinking"}  # rung rejects disabled thinking
                continue
            raise
        finally:
            await limiter.release()
        if retry_wait is not None:
            await asyncio.sleep(retry_wait)


async def run_async_cascade(aclient, tasks, cfg, ledger, budget, *, out_path=None, errors=None, log=print):
    if errors is None:
        import anthropic
        errors = (anthropic.RateLimitError, anthropic.BadRequestError)
    policy = Policy(cfg, ledger, batch=False)
    states = new_states(policy, tasks)
    conc = {**DEFAULT_CONC, **cfg.get("concurrency", {})}
    limiters = {m: AdaptiveLimiter(c) for m, c in conc.items()}
    ttl, outputs = cfg["cache_ttl"], {}

    async def one(t):
        st = states[t["id"]]
        rung_idx, repair, n_call = st.start, "", 0
        while True:
            r = policy.rungs[rung_idx]
            res_usd = policy.est_cost(r, st.klass, st.in_tokens) * RESERVE_FACTOR
            if not budget.reserve(res_usd):
                st.status = "BUDGET_STOP"
                return
            try:
                params = build_params(policy, r, t, user_text(t, repair), ttl)
                msg = await _stream_call(aclient, params, limiters[r.model], errors)
            except Exception:
                st.status = "ERROR"
                return
            finally:
                budget.release(res_usd)
            text = text_of(msg)
            cid = f"{t['id']}_r{r.idx}_a{n_call}"
            n_call += 1
            ok, detail, nxt = await asyncio.to_thread(settle, policy, ledger, st, t, r, text, msg.usage, "async", cid)
            if ok is not False:
                outputs[t["id"]] = {"rung": r.name, "text": text}
                return
            if nxt is None:
                return
            rung_idx, repair = nxt, detail

    await asyncio.gather(*(one(t) for t in tasks))
    write_results(out_path, states, outputs)
    return states, outputs


# ---------------------------------------------------------------- CLI
def load_tasks(path: str) -> list[dict]:
    tasks = [json.loads(ln) for ln in open(path) if ln.strip()]
    for t in tasks:
        t.setdefault("klass", "routine")
    attach_verifiers(tasks)
    return tasks


def cmd_plan(args):
    cfg = load_config(args.config)
    ledger = Ledger(args.ledger)
    policy = Policy(cfg, ledger, batch=(args.mode == "batch"))
    tasks = load_tasks(args.tasks)
    tot_expected = tot_worst = tot_direct = 0.0
    print(f"{'task':<14}{'class':<11}{'in_tok':>8}  {'start':<14}{'path':<44}{'E[$]':>8}{'worst$':>8}{'direct$':>9}")
    for t in tasks:
        st = policy.plan(t["id"], t["klass"], (t.get("system") or "") + t["prompt"], t.get("_verify") is not None)
        path = policy.path_from(st.start, t["klass"], st.in_tokens) if st.has_verifier else [st.start]
        costs = [policy.est_cost(policy.rungs[i], t["klass"], st.in_tokens) for i in path]
        e = policy.expected_cost(path, t["klass"], st.in_tokens) if st.has_verifier else costs[0]
        direct = policy.est_cost(policy.rungs[st.terminal], t["klass"], st.in_tokens)
        tot_expected, tot_worst, tot_direct = tot_expected + e, tot_worst + sum(costs), tot_direct + direct
        print(f"{t['id']:<14}{t['klass']:<11}{st.in_tokens:>8}  {policy.rungs[st.start].name:<14}"
              f"{'>'.join(policy.rungs[i].name for i in path):<44}{e:>8.3f}{sum(costs):>8.3f}{direct:>9.3f}")
    usable = args.budget * (1 - cfg["reserve_frac"])
    print(f"\nexpected ${tot_expected:.2f} | worst-case ${tot_worst:.2f} | all-at-terminal-rung ${tot_direct:.2f} "
          f"| usable budget ${usable:.2f} (after {cfg['reserve_frac']:.0%} reserve)")
    if tot_worst > usable:
        print("WARNING: worst case exceeds the usable budget; the budget guard will stop tasks (BUDGET_STOP).")


def cmd_run(args):
    cfg = load_config(args.config)
    ledger = Ledger(args.ledger)
    budget = Budget(args.budget, ledger, cfg["reserve_frac"])
    tasks = load_tasks(args.tasks)
    import anthropic
    if args.mode == "batch":
        states, _ = run_batch_cascade(anthropic.Anthropic(), tasks, cfg, ledger, budget,
                                      poll_s=args.poll, out_path=args.out, resume=args.resume)
    else:
        states, _ = asyncio.run(run_async_cascade(anthropic.AsyncAnthropic(), tasks, cfg, ledger, budget,
                                                  out_path=args.out))
    from collections import Counter
    print(dict(Counter(s.status for s in states.values())), f"| spent ${ledger.spent():.2f} of ${args.budget:.2f}")


def cmd_report(args):
    es = Ledger(args.ledger).entries()
    if not es:
        print("ledger is empty")
        return
    by_rung, by_class = {}, {}
    for e in es:
        r = by_rung.setdefault(e["rung"], [0, 0.0, 0])
        r[0] += 1
        r[1] += e["usd"]
        r[2] += 1 if e.get("success") else 0
        c = by_class.setdefault(e["klass"], {"usd": 0.0, "solved": set(), "tasks": set()})
        c["usd"] += e["usd"]
        c["tasks"].add(e["task_id"])
        if e.get("success") is True:
            c["solved"].add(e["task_id"])
    print("rung            attempts  pass   spend$")
    for k, (n, usd, ok) in by_rung.items():
        print(f"{k:<15}{n:>8}{ok:>6}{usd:>9.3f}")
    print("\nclass       tasks solved  spend$  $/solved")
    for k, c in by_class.items():
        s = len(c["solved"])
        print(f"{k:<11}{len(c['tasks']):>6}{s:>7}{c['usd']:>8.3f}{(c['usd'] / s if s else float('nan')):>10.3f}")
    print(f"\ntotal spend ${sum(e['usd'] for e in es):.2f}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("plan", cmd_plan), ("run", cmd_run), ("report", cmd_report)):
        p = sub.add_parser(name)
        if name != "report":
            p.add_argument("tasks")
        p.add_argument("--config")
        p.add_argument("--ledger", default="ledger.jsonl")
        p.add_argument("--budget", type=float, default=100.0)
        p.add_argument("--mode", choices=["batch", "async"], default="batch")
        if name == "run":
            p.add_argument("--out", default="results.jsonl")
            p.add_argument("--poll", type=int, default=30)
            p.add_argument("--resume", action="store_true")
        p.set_defaults(fn=fn)
    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
