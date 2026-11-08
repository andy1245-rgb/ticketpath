"""The harness adapter: a draft run config in, a config the loader accepts out.

The last test in this file is the one that matters: the resolved file is fed to
`market_swarm.config.load_run_config` itself, so "the loader accepts it" is not a claim, it is
a call. The loader refuses any unknown field, which is why the law metadata lives in a sidecar
and the resolved config stays exactly the seven fields an event may carry.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tools"))

import region_harness as rh  # noqa: E402
from market_swarm import config as swarm_config  # noqa: E402

ON_DATE = "2026-12-01"

DRAFT = {
    "cluster": "local",
    "seed": 7,
    "dry_run": True,
    "total_budget_lamports": 80_000_000_000,
    "total_budget_actions": 1_200,
    "events": [
        {
            "event_id": "evt_on",
            "face_lamports": 1_000_000_000,
            "fuel": None,
            "tickets": 8,
            "rounds": 2,
            "round_seconds": 3_600,
            "jurisdiction": "CA-ON",
        }
    ],
    "agents": [
        {
            "agent_id": "b1",
            "policy": "buyer",
            "wallet_label": "b1",
            "seed": 11,
            "budget_lamports": 3_000_000_000,
            "budget_actions": 120,
        }
    ],
}


def _draft(**event_over):
    draft = json.loads(json.dumps(DRAFT))
    draft["events"][0].update(event_over)
    return draft


class TestResolution(unittest.TestCase):
    def test_ontario_event_resolves_to_its_law(self):
        resolved, sidecar = rh.build(_draft(), on_date=ON_DATE, accept_unresolved=False)
        event = resolved["events"][0]
        self.assertEqual(event["mode"], "capped")
        self.assertEqual(event["cap_bps"], 0)
        record = sidecar["events"][0]
        self.assertEqual(record["policy"], "capped")
        self.assertEqual(record["capBasis"], "face_plus_fees")
        self.assertEqual(record["enforcedCap"]["bindingRule"], "law")
        self.assertEqual(len(sidecar["lawTableSha256"]), 64)

    def test_a_designated_events_jurisdiction_needs_the_three_state_answer(self):
        _, sidecar = rh.build(
            _draft(jurisdiction="IE", declared_event=True), on_date=ON_DATE, accept_unresolved=False
        )
        self.assertEqual(sidecar["events"][0]["policy"], "capped")
        _, sidecar = rh.build(
            _draft(jurisdiction="IE", declared_event=False), on_date=ON_DATE, accept_unresolved=False
        )
        self.assertEqual(sidecar["events"][0]["policy"], "monitored")
        # silence is refused, not read as permission
        with self.assertRaises(rh.Refused) as caught:
            rh.build(_draft(jurisdiction="IE"), on_date=ON_DATE, accept_unresolved=False)
        self.assertIn("designation_not_stated", str(caught.exception))

    def test_a_monitored_jurisdiction_with_no_platform_cap_has_no_ceiling(self):
        resolved, sidecar = rh.build(_draft(jurisdiction="GB"), on_date=ON_DATE, accept_unresolved=False)
        self.assertEqual(resolved["events"][0]["mode"], "monitored")
        self.assertIsNone(resolved["events"][0]["cap_bps"])
        self.assertIsNone(sidecar["events"][0]["enforcedCap"])

    def test_a_platform_cap_can_bind_and_is_kept(self):
        resolved, sidecar = rh.build(
            _draft(jurisdiction="GB", mode="capped", cap_bps=1500), on_date=ON_DATE, accept_unresolved=False
        )
        self.assertEqual(resolved["events"][0]["cap_bps"], 1500)
        self.assertEqual(sidecar["events"][0]["enforcedCap"]["bindingRule"], "platform")

    def test_a_hand_typed_cap_looser_than_the_law_is_refused(self):
        with self.assertRaises(rh.Refused) as caught:
            rh.build(_draft(mode="capped", cap_bps=2500), on_date=ON_DATE, accept_unresolved=False)
        self.assertIn("looser than the law", str(caught.exception))

    def test_an_unresolved_jurisdiction_is_refused_without_the_operator_s_say_so(self):
        with self.assertRaises(rh.Refused) as caught:
            rh.build(_draft(jurisdiction="US-TX"), on_date=ON_DATE, accept_unresolved=False)
        self.assertIn("unresolved", str(caught.exception))
        resolved, sidecar = rh.build(
            _draft(jurisdiction="US-TX"), on_date=ON_DATE, accept_unresolved=True
        )
        self.assertEqual(resolved["events"][0]["mode"], "monitored")
        self.assertTrue(sidecar["acceptedUnresolved"])
        self.assertEqual(sidecar["events"][0]["policy"], "unresolved")

    def test_no_jurisdiction_and_no_mode_is_refused(self):
        draft = _draft()
        draft["events"][0].pop("jurisdiction")
        with self.assertRaises(rh.Refused) as caught:
            rh.build(draft, on_date=ON_DATE, accept_unresolved=False)
        self.assertIn("no jurisdiction and no mode", str(caught.exception))

    def test_no_jurisdiction_with_an_explicit_mode_still_works(self):
        draft = _draft()
        draft["events"][0].pop("jurisdiction")
        draft["events"][0]["mode"] = "monitored"
        resolved, sidecar = rh.build(draft, on_date=ON_DATE, accept_unresolved=False)
        self.assertEqual(resolved["events"][0]["mode"], "monitored")
        self.assertEqual(sidecar["events"][0]["reason"], "no_jurisdiction_declared")

    def test_the_law_is_checked_against_the_named_date(self):
        resolved, _ = rh.build(_draft(jurisdiction="CA-ON"), on_date="2026-04-23", accept_unresolved=False)
        self.assertEqual(resolved["events"][0]["mode"], "monitored")
        resolved, _ = rh.build(_draft(jurisdiction="CA-ON"), on_date="2026-04-24", accept_unresolved=False)
        self.assertEqual(resolved["events"][0]["mode"], "capped")


class TestTheResolvedConfigIsLoadable(unittest.TestCase):
    def test_the_swarm_loader_accepts_the_resolved_file(self):
        resolved, _sidecar = rh.build(_draft(), on_date=ON_DATE, accept_unresolved=False)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "resolved.json"
            path.write_text(json.dumps(resolved), encoding="utf-8")
            loaded = swarm_config.load_run_config(path)
        self.assertEqual(len(loaded.events), 1)
        self.assertEqual(loaded.events[0].event_id, "evt_on")
        self.assertEqual(loaded.events[0].mode, "capped")
        self.assertEqual(loaded.events[0].cap_bps, 0)

    def test_the_draft_only_fields_never_reach_the_loader(self):
        resolved, _ = rh.build(_draft(fee_lamports=50_000_000), on_date=ON_DATE, accept_unresolved=False)
        self.assertEqual(set(resolved["events"][0]) - set(rh.EVENT_FIELDS), set())
        for field in rh.DRAFT_ONLY:
            self.assertNotIn(field, resolved["events"][0])


class TestCli(unittest.TestCase):
    def run_tool(self, *args):
        return subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools" / "region_harness.py"), *args],
            capture_output=True,
            text=True,
            timeout=120,
        )

    def test_check_prints_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            draft = Path(tmp) / "draft.json"
            draft.write_text(json.dumps(_draft()), encoding="utf-8")
            out = Path(tmp) / "resolved.json"
            result = self.run_tool(str(draft), "--out", str(out), "--on-date", ON_DATE, "--check")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("CA-ON", result.stdout)
            self.assertIn("binding=law", result.stdout)
            self.assertFalse(out.exists())

    def test_a_refusal_exits_1_and_says_why(self):
        with tempfile.TemporaryDirectory() as tmp:
            draft = Path(tmp) / "draft.json"
            draft.write_text(json.dumps(_draft(mode="capped", cap_bps=2500)), encoding="utf-8")
            result = self.run_tool(str(draft), "--on-date", ON_DATE, "--check")
            self.assertEqual(result.returncode, 1)
            self.assertIn("looser than the law", result.stderr)

    def test_a_missing_on_date_is_a_usage_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            draft = Path(tmp) / "draft.json"
            draft.write_text(json.dumps(_draft()), encoding="utf-8")
            result = self.run_tool(str(draft), "--check")
            self.assertEqual(result.returncode, 1)
            self.assertIn("on-date", result.stderr)


if __name__ == "__main__":
    unittest.main()
