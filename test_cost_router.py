"""Offline tests for cost_router + cascade_runners. No network; run: python3 test_cost_router.py"""
import asyncio
import json
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace as NS

import cascade_runners as cr
from cost_router import Budget, Ledger, Policy, load_config, usd_cost


def usage(inp=1000, out=1500):
    return NS(input_tokens=inp, output_tokens=out, cache_read_input_tokens=0,
              cache_creation_input_tokens=0, cache_creation=None)


def respond(params):
    """Fake model: only Opus/Fable solve it. Failure text differs per rung so signatures differ."""
    m = params["model"]
    if "opus" in m or "fable" in m:
        return "GOOD"
    return f"BAD-{m}-{params['output_config']['effort']}"


def verifier(task, text):
    return (True, "", "") if text == "GOOD" else (False, text, "wrong: " + text)


def make_tasks(n, klass="analysis", with_verifier=True, prompt="prove X"):
    ts = [{"id": f"T{i}", "klass": klass, "prompt": f"{prompt} {i}"} for i in range(n)]
    if with_verifier:
        for t in ts:
            t["_verify"] = verifier
    return ts


def msg(text, u):
    return NS(content=[NS(type="text", text=text)], usage=u)


class FakeBatches:
    def __init__(self, errored_prompts=()):
        self.store, self.n, self.errored = {}, 0, set(errored_prompts)
        self.submitted = []

    def create(self, requests):
        self.n += 1
        bid = f"b{self.n}"
        self.store[bid] = requests
        self.submitted.append(requests)
        return NS(id=bid)

    def retrieve(self, bid):
        return NS(processing_status="ended")

    def results(self, bid):
        for r in self.store[bid]:
            prompt = r["params"]["messages"][0]["content"]
            base = prompt.split("\n\n[A previous")[0]
            if base in self.errored:
                self.errored.discard(base)
                yield NS(custom_id=r["custom_id"], result=NS(type="errored", error=NS(error=NS(type="api_error"))))
                continue
            yield NS(custom_id=r["custom_id"],
                     result=NS(type="succeeded", message=msg(respond(r["params"]), usage())))


class FakeBatchClient:
    def __init__(self, **kw):
        self.messages = NS(batches=FakeBatches(**kw))


class Env:
    def __enter__(self):
        self.d = tempfile.TemporaryDirectory()
        self.ledger = Ledger(os.path.join(self.d.name, "ledger.jsonl"))
        self.cfg = load_config()
        return self

    def __exit__(self, *a):
        self.d.cleanup()


class TestCost(unittest.TestCase):
    def test_known_values(self):
        u = lambda **k: NS(**{"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0,
                              "cache_creation_input_tokens": 0, "cache_creation": None, **k})
        self.assertAlmostEqual(usd_cost(u(input_tokens=10**6, output_tokens=10**6), "claude-opus-5-5"), 24.0)
        self.assertAlmostEqual(usd_cost(u(input_tokens=10**6, output_tokens=10**6), "claude-opus-5-5", batch=True), 12.0)
        self.assertAlmostEqual(usd_cost(u(cache_read_input_tokens=10**6), "claude-opus-5-5"), 0.2)
        self.assertAlmostEqual(usd_cost(u(cache_creation_input_tokens=10**6), "claude-opus-5-5", ttl="1h"), 8.0)
        self.assertAlmostEqual(usd_cost(u(input_tokens=50_000), "claude-haiku-5-5"), 0.005)
        self.assertAlmostEqual(usd_cost(u(input_tokens=200_000), "claude-haiku-5-5"), 0.10)  # >100k tier
        self.assertAlmostEqual(usd_cost({"input_tokens": 10**6, "output_tokens": 0}, "claude-sonnet-5-5"), 2.0)


class TestPolicy(unittest.TestCase):
    def test_cap_invariant_and_terminal_end(self):
        with Env() as e:
            p = Policy(e.cfg, e.ledger)
            for klass, c in e.cfg["classes"].items():
                lo, term = p.by_name[c["floor"]].idx, p.by_name[c["terminal"]].idx
                for tok in (500, 20_000, 300_000):
                    cap = p.cap(klass, tok)
                    for s in range(lo, term + 1):
                        path = p.path_from(s, klass, tok)
                        self.assertEqual(path[-1], term)
                        cheap = sum(p.est_cost(p.rungs[i], klass, tok) for i in path[:-1])
                        self.assertLessEqual(cheap, cap + 1e-12)

    def test_start_rung(self):
        with Env() as e:
            p = Policy(e.cfg, e.ledger)
            self.assertEqual(p.plan("a", "mechanical", "x" * 400, True).start, p.by_name["haiku_low"].idx)
            self.assertGreaterEqual(p.plan("b", "hard", "x" * 400, True).start, p.by_name["sonnet_high"].idx)
            self.assertEqual(p.plan("c", "analysis", "x", False).start, p.by_name["opus_high"].idx)
            e.cfg["classes"]["mechanical"]["prior"].update(
                {"haiku_low": .001, "haiku_high": .001, "sonnet_medium": .001, "sonnet_high": .98})
            p2 = Policy(e.cfg, e.ledger)
            self.assertEqual(p2.plan("d", "mechanical", "x" * 400, True).start, p2.by_name["sonnet_high"].idx)

    def test_next_rung(self):
        with Env() as e:
            p = Policy(e.cfg, e.ledger)
            st = p.plan("t", "analysis", "x" * 400, True)
            self.assertIn(p.next_rung(st, st.start, "s1"), (st.start + 1, st.terminal))
            st.last_sig = "same"
            self.assertEqual(p.next_rung(st, st.start, "same"), st.terminal)  # repeated failure
            st.last_sig = ""
            st.spent_nonterminal = 1e9
            self.assertEqual(p.next_rung(st, st.start, "z"), st.terminal)  # cap exhausted
            st.terminal_attempts = 1
            self.assertIsNone(p.next_rung(st, st.terminal, "z"))  # terminal failure stops
            nv = p.plan("n", "analysis", "x", False)
            self.assertIsNone(p.next_rung(nv, nv.start, "z"))  # no verifier: never cascade

    def test_ledger_calibration(self):
        with Env() as e:
            for _ in range(6):
                e.ledger.record({"klass": "mechanical", "rung": "haiku_low", "success": False})
            p = Policy(e.cfg, e.ledger)
            self.assertLess(p.p_success("mechanical", p.by_name["haiku_low"]), 0.85)


class TestLedger(unittest.TestCase):
    def test_concurrent_appends(self):
        with Env() as e:
            with ThreadPoolExecutor(16) as ex:
                list(ex.map(lambda i: e.ledger.record({"i": i, "usd": 0.01}), range(200)))
            self.assertEqual(len(e.ledger.entries()), 200)
            with open(e.ledger.path) as f:
                for ln in f:
                    json.loads(ln)
            self.assertAlmostEqual(e.ledger.spent(), 2.0)


class TestBatchCascade(unittest.TestCase):
    def run_batch(self, e, tasks, budget=100.0, client=None):
        client = client or FakeBatchClient()
        b = Budget(budget, e.ledger, e.cfg["reserve_frac"])
        out = os.path.join(e.d.name, "results.jsonl")
        states, outs = cr.run_batch_cascade(client, tasks, e.cfg, e.ledger, b, sleep=lambda s: None,
                                            out_path=out, log=lambda *a: None)
        return states, outs, client, out

    def test_escalates_and_respects_cap(self):
        with Env() as e:
            tasks = make_tasks(6)
            states, outs, client, out = self.run_batch(e, tasks)
            p = Policy(e.cfg, e.ledger, batch=True)
            for t in tasks:
                st = states[t["id"]]
                self.assertEqual(st.status, "SOLVED")
                self.assertTrue(outs[t["id"]]["rung"].startswith(("opus", "fable")))
                self.assertLessEqual(st.spent_nonterminal, p.cap("analysis", st.in_tokens) * 1.001 + 0.05)
                self.assertLessEqual(st.terminal_attempts, 1)  # Opus below the terminal rung may already solve it
            rows = [json.loads(l) for l in open(out)]
            self.assertEqual(len(rows), 6)
            self.assertTrue(all(r["status"] == "SOLVED" for r in rows))
            self.assertGreaterEqual(len(client.messages.batches.submitted), 2)  # at least one escalation round

    def test_unsolvable_total_bounded_by_cap_plus_one_terminal(self):
        with Env() as e:
            tasks = make_tasks(3)
            for t in tasks:
                t["_verify"] = lambda task, text: (False, "same" if "GOOD" in text else text, "no")
            states, _, _, _ = self.run_batch(e, tasks)
            p = Policy(e.cfg, e.ledger, batch=True)
            for t in tasks:
                st = states[t["id"]]
                self.assertEqual(st.status, "FAILED")
                self.assertEqual(st.terminal_attempts, 1)  # exactly one terminal try, then stop
                term = p.rungs[st.terminal]
                one_strong = p.est_cost(term, "analysis", st.in_tokens)
                self.assertLessEqual(st.spent_total, (1 + e.cfg["alpha"]) * one_strong * 1.5 + 0.05)

    def test_cheap_passes_stay_cheap(self):
        with Env() as e:
            tasks = make_tasks(3, klass="mechanical")
            for t in tasks:
                t["_verify"] = lambda task, text: (True, "", "")
            states, outs, client, _ = self.run_batch(e, tasks)
            self.assertEqual(len(client.messages.batches.submitted), 1)
            self.assertTrue(all(s.status == "SOLVED" for s in states.values()))
            self.assertTrue(all(o["rung"] == "haiku_low" for o in outs.values()))

    def test_no_verifier_runs_once(self):
        with Env() as e:
            tasks = make_tasks(2, with_verifier=False)
            states, _, client, _ = self.run_batch(e, tasks)
            self.assertEqual(len(client.messages.batches.submitted), 1)
            self.assertTrue(all(s.status == "DONE_UNVERIFIED" for s in states.values()))

    def test_infra_error_retries_same_rung_without_charge(self):
        with Env() as e:
            tasks = make_tasks(2, klass="mechanical")
            for t in tasks:
                t["_verify"] = lambda task, text: (True, "", "")
            client = FakeBatchClient(errored_prompts={"prove X 0"})
            states, _, _, _ = self.run_batch(e, tasks, client=client)
            self.assertTrue(all(s.status == "SOLVED" for s in states.values()))
            self.assertEqual(len(e.ledger.entries()), 2)  # the errored request was not billed

    def test_budget_stop(self):
        with Env() as e:
            tasks = make_tasks(12)
            states, _, _, _ = self.run_batch(e, tasks, budget=0.15)
            statuses = [s.status for s in states.values()]
            self.assertIn("BUDGET_STOP", statuses)
            self.assertLessEqual(e.ledger.spent(), 0.15)

    def test_resume_does_not_repay(self):
        with Env() as e:
            tasks = make_tasks(2, klass="mechanical")
            for t in tasks:
                t["_verify"] = lambda task, text: (True, "", "")
            self.run_batch(e, tasks)
            n_before = len(e.ledger.entries())
            b = Budget(100.0, e.ledger, e.cfg["reserve_frac"])
            client = FakeBatchClient()
            states, _ = cr.run_batch_cascade(client, tasks, e.cfg, e.ledger, b, sleep=lambda s: None,
                                             resume=True, log=lambda *a: None)
            self.assertEqual(len(e.ledger.entries()), n_before)
            self.assertEqual(client.messages.batches.submitted, [])
            self.assertTrue(all(s.status == "SOLVED" for s in states.values()))


class FakeRateLimit(Exception):
    def __init__(self):
        self.body, self.response = {}, NS(headers={"retry-after": "0"})


class FakeBadRequest(Exception):
    pass


class FakeStream:
    def __init__(self, owner, params):
        self.owner, self.params = owner, params

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def get_final_message(self):
        if self.owner.throttle:
            self.owner.throttle -= 1
            raise FakeRateLimit()
        return msg(respond(self.params), usage())


class FakeAsyncClient:
    def __init__(self, throttle=0):
        self.throttle = throttle
        self.messages = NS(stream=lambda **p: FakeStream(self, p))


class TestAsyncCascade(unittest.TestCase):
    def test_cascade_and_429(self):
        with Env() as e:
            tasks = make_tasks(4)
            b = Budget(100.0, e.ledger, e.cfg["reserve_frac"])
            client = FakeAsyncClient(throttle=3)
            states, outs = asyncio.run(cr.run_async_cascade(
                client, tasks, e.cfg, e.ledger, b, errors=(FakeRateLimit, FakeBadRequest), log=lambda *a: None))
            p = Policy(e.cfg, e.ledger, batch=False)
            for t in tasks:
                st = states[t["id"]]
                self.assertEqual(st.status, "SOLVED")
                self.assertLessEqual(st.spent_nonterminal, p.cap("analysis", st.in_tokens) * 1.001 + 0.1)


class TestLimiter(unittest.TestCase):
    def test_ramp_and_halve(self):
        lim = cr.AdaptiveLimiter(8, start=2)
        for _ in range(10):
            lim.on_success()
        self.assertGreater(lim.limit, 2)
        before = lim.limit
        lim.on_throttle()
        self.assertEqual(lim.limit, max(1, before // 2))
        self.assertLessEqual(lim.limit, 8)


if __name__ == "__main__":
    unittest.main(verbosity=2)
