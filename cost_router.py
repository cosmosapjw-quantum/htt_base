"""Cost-aware model router core: pricing, budget ledger, cascade policy.

No network calls live here. Prices and effort values come from Anthropic's
platform docs (pricing, effort, batch processing, "Optimizing for cost and
intelligence"). Every number marked PRIOR below is an initial guess that the
ledger overwrites with measured success rates; Anthropic's own guidance is to
build evals on your workload and compare cost per solved task.

Design rules taken from the official multi-model guidance:
  * tune effort before switching models, and escalate only failures;
  * a retry at the same capability rarely helps, so a failure moves UP a rung;
  * cheap-first needs a failure signal (a verifier), otherwise run once;
  * judge a policy by cost per solved task, not cost per token or attempt.

Cost guard (the user's requirement): total spend on non-terminal rungs for one
task is capped at ALPHA x the estimated cost of one terminal (strongest) attempt.
Worst case for a task is therefore (1 + ALPHA) x one strong attempt, and the
expected case is far below one strong attempt when cheap rungs often succeed.
"""
from __future__ import annotations

import fcntl
import json
import math
import os
import statistics
import threading
import time
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------- pricing
# USD per million tokens (platform.claude.com/docs/en/about-claude/pricing).
PRICES = {
    "claude-fable-5-1":  {"in": 10.0, "out": 50.0, "read_mult": 0.025},
    "claude-opus-5-5":   {"in": 4.0,  "out": 20.0, "read_mult": 0.05},
    "claude-sonnet-5-5": {"in": 2.0,  "out": 10.0, "read_mult": 0.05},
    "claude-haiku-5-5":  {"in": 0.10, "out": 0.50, "read_mult": 0.10,
                          # prompts over 100k tokens (all input incl. cache) use these
                          "long_in": 0.50, "long_out": 2.50, "long_threshold": 100_000},
}
WRITE_MULT = {"5m": 1.25, "1h": 2.0}
BATCH_MULT = 0.5  # Batch API: 50% off input and output; stacks with caching


def _g(obj, key, default=0):
    if obj is None:
        return default
    v = obj.get(key) if isinstance(obj, dict) else getattr(obj, key, None)
    return default if v is None else v


def usd_cost(usage, model: str, batch: bool = False, ttl: str = "5m") -> float:
    """Dollar cost of one response from its `usage` object."""
    p = PRICES[model]
    inp = _g(usage, "input_tokens")
    out = _g(usage, "output_tokens")  # includes thinking tokens
    read = _g(usage, "cache_read_input_tokens")
    write_total = _g(usage, "cache_creation_input_tokens")
    cc = _g(usage, "cache_creation", None)
    if cc is not None and (_g(cc, "ephemeral_5m_input_tokens") or _g(cc, "ephemeral_1h_input_tokens")):
        w5, w1 = _g(cc, "ephemeral_5m_input_tokens"), _g(cc, "ephemeral_1h_input_tokens")
    else:
        w5, w1 = (write_total, 0) if ttl == "5m" else (0, write_total)
    pin, pout = p["in"], p["out"]
    if "long_threshold" in p and (inp + read + w5 + w1) > p["long_threshold"]:
        pin, pout = p["long_in"], p["long_out"]
    usd = (inp * pin + w5 * pin * WRITE_MULT["5m"] + w1 * pin * WRITE_MULT["1h"]
           + read * pin * p["read_mult"] + out * pout) / 1e6
    return usd * (BATCH_MULT if batch else 1.0)


# ---------------------------------------------------------------- config
DEFAULT_CONFIG = {
    "alpha": 0.5,             # non-terminal spend cap, as a fraction of ONE terminal attempt
    "prior_strength": 4,      # pseudo-observations behind each PRIOR success rate
    "terminal_attempts": 1,   # same-cap retries rarely help; a failed terminal needs a human
    "reserve_frac": 0.10,     # budget held back for rework and the final pass
    "cache_ttl": "1h",        # batches can outlive the 5-minute cache
    "chars_per_token": 2.5,   # conservative (Korean, LaTeX and the newer tokenizer run high)
    "out_tokens_by_effort": {"low": 1500, "medium": 4000, "high": 9000, "xhigh": 20000},   # PRIOR
    "max_tokens_by_effort": {"low": 8000, "medium": 16000, "high": 32000, "xhigh": 64000},
    # ordered cheap -> capable. Haiku 5.5 allows thinking disabled only at effort <= high.
    "rungs": [
        {"name": "haiku_low",    "model": "claude-haiku-5-5",  "effort": "low",    "thinking_disabled": True},
        {"name": "haiku_high",   "model": "claude-haiku-5-5",  "effort": "high",   "thinking_disabled": False},
        {"name": "sonnet_medium", "model": "claude-sonnet-5-5", "effort": "medium", "thinking_disabled": False},
        {"name": "sonnet_high",  "model": "claude-sonnet-5-5", "effort": "high",   "thinking_disabled": False},
        {"name": "opus_medium",  "model": "claude-opus-5-5",   "effort": "medium", "thinking_disabled": False},
        {"name": "opus_high",    "model": "claude-opus-5-5",   "effort": "high",   "thinking_disabled": False},
        {"name": "opus_xhigh",   "model": "claude-opus-5-5",   "effort": "xhigh",  "thinking_disabled": False},
        {"name": "fable_high",   "model": "claude-fable-5-1",  "effort": "high",   "thinking_disabled": False},
        {"name": "fable_xhigh",  "model": "claude-fable-5-1",  "effort": "xhigh",  "thinking_disabled": False},
    ],
    # PRIOR success rates per (class, rung). Replaced by the ledger as data arrives.
    "classes": {
        "mechanical": {"floor": "haiku_low", "terminal": "sonnet_high", "no_verifier": "haiku_high",
                       "prior": {"haiku_low": .85, "haiku_high": .93, "sonnet_medium": .96, "sonnet_high": .98}},
        "routine":    {"floor": "haiku_high", "terminal": "opus_medium", "no_verifier": "sonnet_high",
                       "prior": {"haiku_high": .55, "sonnet_medium": .75, "sonnet_high": .85, "opus_medium": .93}},
        "analysis":   {"floor": "sonnet_medium", "terminal": "opus_xhigh", "no_verifier": "opus_high",
                       "prior": {"sonnet_medium": .45, "sonnet_high": .60, "opus_medium": .65,
                                 "opus_high": .78, "opus_xhigh": .88}},
        "hard":       {"floor": "sonnet_high", "terminal": "fable_xhigh", "no_verifier": "fable_high",
                       "prior": {"sonnet_high": .12, "opus_medium": .20, "opus_high": .35,
                                 "opus_xhigh": .50, "fable_high": .65, "fable_xhigh": .80}},
    },
}


@dataclass(frozen=True)
class Rung:
    idx: int
    name: str
    model: str
    effort: str
    thinking_disabled: bool


def load_config(path: Optional[str] = None) -> dict:
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    if path:
        over = json.load(open(path))
        for k, v in over.items():
            cfg[k] = v
    names = [r["name"] for r in cfg["rungs"]]
    for cname, c in cfg["classes"].items():
        lo, hi = names.index(c["floor"]), names.index(c["terminal"])
        missing = [n for n in names[lo:hi + 1] if n not in c["prior"]]
        if lo > hi or missing:
            raise ValueError(f"class {cname}: bad floor/terminal or missing priors {missing}")
        if c["no_verifier"] not in names:
            raise ValueError(f"class {cname}: unknown no_verifier rung")
    for r in cfg["rungs"]:
        if r["model"] not in PRICES:
            raise ValueError(f"no price for {r['model']}")
    return cfg


# ---------------------------------------------------------------- ledger
class Ledger:
    """Append-only JSONL spend log, safe across threads and processes (flock)."""

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self._lock = threading.Lock()

    def record(self, entry: dict) -> None:
        entry = dict(entry)
        entry.setdefault("ts", time.time())
        line = json.dumps(entry, ensure_ascii=False) + "\n"
        with self._lock, open(self.path, "a") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                f.write(line)
                f.flush()
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def entries(self) -> list[dict]:
        if not os.path.exists(self.path):
            return []
        out = []
        with open(self.path) as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    try:
                        out.append(json.loads(ln))
                    except json.JSONDecodeError:
                        pass
        return out

    def spent(self) -> float:
        return sum(e.get("usd", 0.0) for e in self.entries())


class Budget:
    """Hard spend guard. Reserve before each call, settle after."""

    def __init__(self, total_usd: float, ledger: Ledger, reserve_frac: float):
        self.total = total_usd
        self.ledger = ledger
        self.reserve_floor = total_usd * reserve_frac
        self._reserved = 0.0
        self._lock = threading.Lock()

    def available(self) -> float:
        return self.total - self.reserve_floor - self.ledger.spent() - self._reserved

    def reserve(self, usd: float) -> bool:
        with self._lock:
            if self.available() < usd:
                return False
            self._reserved += usd
            return True

    def release(self, usd: float) -> None:
        with self._lock:
            self._reserved = max(0.0, self._reserved - usd)


# ---------------------------------------------------------------- policy
@dataclass
class TaskState:
    task_id: str
    klass: str
    in_tokens: int
    has_verifier: bool
    start: int
    terminal: int
    spent_nonterminal: float = 0.0
    spent_total: float = 0.0
    terminal_attempts: int = 0
    last_sig: str = ""
    attempts: list = field(default_factory=list)  # (rung_idx, ok, sig)
    status: str = "PENDING"  # PENDING | SOLVED | FAILED | BUDGET_STOP | ERROR


class Policy:
    def __init__(self, cfg: dict, ledger: Ledger, batch: bool = True):
        self.cfg = cfg
        self.ledger = ledger
        self.batch = batch
        self.rungs = [Rung(i, **r) for i, r in enumerate(cfg["rungs"])]
        self.by_name = {r.name: r for r in self.rungs}

    # -- estimation ------------------------------------------------------
    def _entries(self):
        return self.ledger.entries()

    def estimate_input_tokens(self, text: str) -> int:
        est = math.ceil(len(text) / self.cfg["chars_per_token"])
        ratios = [e["in_tokens"] / e["est_in"] for e in self._entries()[-50:]
                  if e.get("est_in") and e.get("in_tokens")]
        factor = statistics.median(ratios) if len(ratios) >= 5 else 1.0
        return max(1, math.ceil(est * factor))

    def est_out_tokens(self, klass: str, rung: Rung) -> int:
        obs = [e["out_tokens"] for e in self._entries()
               if e.get("klass") == klass and e.get("rung") == rung.name and e.get("out_tokens")]
        if len(obs) >= 3:
            return int(statistics.median(obs))
        return self.cfg["out_tokens_by_effort"][rung.effort]

    def est_cost(self, rung: Rung, klass: str, in_tokens: int) -> float:
        p = PRICES[rung.model]
        pin, pout = p["in"], p["out"]
        if "long_threshold" in p and in_tokens > p["long_threshold"]:
            pin, pout = p["long_in"], p["long_out"]
        usd = (in_tokens * pin + self.est_out_tokens(klass, rung) * pout) / 1e6
        return usd * (BATCH_MULT if self.batch else 1.0)  # caching ignored: conservative

    def max_tokens(self, rung: Rung) -> int:
        return self.cfg["max_tokens_by_effort"][rung.effort]

    def p_success(self, klass: str, rung: Rung) -> float:
        prior = self.cfg["classes"][klass]["prior"].get(rung.name, 0.05)
        S = self.cfg["prior_strength"]
        obs = [e for e in self._entries()
               if e.get("klass") == klass and e.get("rung") == rung.name and e.get("success") is not None]
        n, s = len(obs), sum(1 for e in obs if e["success"])
        return (prior * S + s) / (S + n)

    # -- ladder ----------------------------------------------------------
    def cap(self, klass: str, in_tokens: int) -> float:
        term = self.by_name[self.cfg["classes"][klass]["terminal"]]
        return self.cfg["alpha"] * self.est_cost(term, klass, in_tokens)

    def path_from(self, start: int, klass: str, in_tokens: int) -> list[int]:
        """Deterministic rung sequence from `start`, honoring the cheap-spend cap."""
        term = self.by_name[self.cfg["classes"][klass]["terminal"]].idx
        cap, spent, path, i = self.cap(klass, in_tokens), 0.0, [], start
        while i < term:
            c = self.est_cost(self.rungs[i], klass, in_tokens)
            if spent + c > cap:
                break
            path.append(i)
            spent += c
            i += 1
        path.append(term)
        return path

    def expected_cost(self, path: list[int], klass: str, in_tokens: int) -> float:
        total, p_reach = 0.0, 1.0
        for k, i in enumerate(path):
            r = self.rungs[i]
            c = self.est_cost(r, klass, in_tokens)
            p = max(self.p_success(klass, r), 1e-3)
            if k == len(path) - 1:  # terminal: allow geometric retries for the estimate
                total += p_reach * c / p
            else:
                total += p_reach * c
                p_reach *= (1 - p)
        return total

    def plan(self, task_id: str, klass: str, text: str, has_verifier: bool) -> TaskState:
        c = self.cfg["classes"][klass]
        in_tokens = self.estimate_input_tokens(text)
        term = self.by_name[c["terminal"]].idx
        if not has_verifier:  # no failure signal: run once at a fixed rung, never cascade
            start = self.by_name[c["no_verifier"]].idx
            return TaskState(task_id, klass, in_tokens, False, start, start)
        lo = self.by_name[c["floor"]].idx
        best = min(range(lo, term + 1),
                   key=lambda s: (self.expected_cost(self.path_from(s, klass, in_tokens), klass, in_tokens), s))
        return TaskState(task_id, klass, in_tokens, True, best, term)

    def next_rung(self, st: TaskState, last_rung: int, sig: str) -> Optional[int]:
        """Rung for the next attempt after a verified failure, or None to stop."""
        if not st.has_verifier:
            return None
        if last_rung >= st.terminal:
            return None if st.terminal_attempts >= self.cfg["terminal_attempts"] else st.terminal
        nxt = last_rung + 1
        if sig and sig == st.last_sig:  # same failure again: more of the same will not fix it
            nxt = st.terminal
        if nxt < st.terminal:
            c = self.est_cost(self.rungs[nxt], st.klass, st.in_tokens)
            if st.spent_nonterminal + c > self.cap(st.klass, st.in_tokens):
                nxt = st.terminal
        return nxt
