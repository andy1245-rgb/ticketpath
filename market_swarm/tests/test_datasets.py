"""The dataset verifier and summariser, on hand-built files with exact numbers.

Every file here is written by hand rather than by a run, because the point is to prove the
checker fails on each breakage independently: a header that is not first, a row that denies
it is synthetic, a `seq` that goes backwards, a markup that disagrees with its own price, a
refusal with no error code, an `ok` row on the validator with nothing to point at.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from market_swarm.config import ceiling_lamports, effective_cap_bps
from market_swarm.datasets import DatasetInvalid, summarise, verify_dataset
from market_swarm.ledger import LEDGER_HEADER, TradeRow

FACE = 1_000_000
CAP_BPS = 2500


def _header(**overrides) -> dict:
    header = dict(LEDGER_HEADER)
    header.update({"run_id": "sw-test", "event_id": "ev", "mode": "capped", "cluster": "local"})
    header.update(overrides)
    return header


def _row(
    *,
    mode: str = "capped",
    action: str = "resell",
    status: str = "ok",
    price: int | None = 1_100_000,
    face: int = FACE,
    markup: int | None | str = "auto",
    chain: str = "local-validator",
    program: str = "v1",
    signature: str | None = "sig-1",
    error_code: int | None = None,
    agent_id: str = "a1",
    seq: int = 1,
    **overrides,
) -> TradeRow:
    cap_bps = effective_cap_bps(mode, CAP_BPS)
    if markup == "auto" and price is not None:
        markup = (price - face) * 10_000 // face
    fields = dict(
        run_id="sw-test",
        seq=seq,
        ts="2026-01-01T00:00:00Z",
        event_id="ev",
        mode=mode,
        agent_id=agent_id,
        action=action,
        ticket_id="ev#0001",
        from_wallet="w-a1",
        to_wallet="w-a2",
        price_lamports=price,
        face_lamports=face,
        cap_bps=cap_bps,
        ceiling_lamports=ceiling_lamports(face, cap_bps),
        markup_bps=markup,
        status=status,
        error_code=error_code,
        signature=signature,
        slot=1,
        block_time=1_700_000_000,
        latency_ms=1,
        hop_index=2,
        budget_before=0,
        budget_after=0,
        chain=chain,
        program=program,
        rationale="hand built for a test",
    )
    fields.update(overrides)
    return TradeRow(**fields)


class DatasetCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def write_rows(self, rows, name: str = "SYNTHETIC-test.jsonl", header=None) -> Path:
        """Header, then rows with `seq` stamped 1..n the way the writer stamps it."""
        path = self.root / name
        lines = [json.dumps(header if header is not None else _header(), separators=(",", ":"))]
        for index, row in enumerate(rows, start=1):
            payload = row.as_dict()
            payload["seq"] = index
            lines.append(json.dumps(payload, separators=(",", ":")))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def write_raw(self, lines, name: str = "SYNTHETIC-raw.jsonl") -> Path:
        path = self.root / name
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def violations(self, path: Path) -> list[str]:
        with self.assertRaises(DatasetInvalid) as caught:
            verify_dataset(path)
        return list(caught.exception.violations)


class TestValidDatasets(DatasetCase):
    def test_a_good_dataset_verifies_and_reports_what_it_is(self) -> None:
        path = self.write_rows([_row(seq=0), _row(seq=0, price=1_200_000)])
        result = verify_dataset(path)
        self.assertEqual(result["rows"], 2)
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["run_id"], "sw-test")
        self.assertEqual(result["event_id"], "ev")
        self.assertEqual(result["mode"], "capped")
        self.assertEqual(result["by_status"], {"ok": 2})
        self.assertIs(result["ok"], True)

    def test_a_listing_may_have_no_signature(self) -> None:
        path = self.write_rows([_row(action="list", signature=None, slot=None)])
        self.assertEqual(verify_dataset(path)["rows"], 1)

    def test_a_simulated_ok_row_needs_no_signature(self) -> None:
        path = self.write_rows([_row(chain="simulated", signature=None)])
        self.assertEqual(verify_dataset(path)["rows"], 1)

    def test_blank_lines_are_ignored_but_do_not_hide_the_rows(self) -> None:
        path = self.write_raw(
            [
                json.dumps(_header(), separators=(",", ":")),
                "",
                json.dumps(_row().as_dict(), separators=(",", ":")),
            ]
        )
        self.assertEqual(verify_dataset(path)["rows"], 1)


class TestEveryInvariantIsChecked(DatasetCase):
    def test_a_row_whose_program_is_outside_the_set_is_refused(self) -> None:
        path = self.write_rows([_row(program="v3")])
        messages = self.violations(path)
        self.assertTrue(any("program" in message for message in messages), messages)

    def test_a_row_whose_program_disagrees_with_the_header_is_refused(self) -> None:
        # One file is one run, one event and one program. Rows from two programs under one header
        # answer two different questions with one name, so this is a violation and not a nuance.
        path = self.write_rows(
            [_row(program="v1"), _row(program="v2")], header=_header(program="v1")
        )
        messages = self.violations(path)
        self.assertTrue(any("mixes two programs" in message for message in messages), messages)

    def test_a_dataset_of_one_program_verifies_under_its_own_header(self) -> None:
        for program in ("v1", "v2"):
            with self.subTest(program=program):
                path = self.write_rows(
                    [_row(program=program)],
                    name=f"SYNTHETIC-{program}.jsonl",
                    header=_header(program=program),
                )
                self.assertEqual(verify_dataset(path)["rows"], 1)

    def test_a_missing_header_is_refused(self) -> None:
        path = self.write_raw(
            [json.dumps(_row().as_dict(), separators=(",", ":"))]
        )
        messages = self.violations(path)
        self.assertTrue(any("header" in message for message in messages), messages)

    def test_an_empty_file_is_refused(self) -> None:
        path = self.write_raw([])
        self.assertTrue(any("empty" in message for message in self.violations(path)))

    def test_a_missing_file_is_refused_rather_than_raising_oserror(self) -> None:
        messages = self.violations(self.root / "nope.jsonl")
        self.assertTrue(any("cannot read" in message for message in messages))

    def test_a_row_that_denies_it_is_synthetic_is_refused(self) -> None:
        payload = _row().as_dict()
        payload["synthetic"] = False
        path = self.write_raw(
            [
                json.dumps(_header(), separators=(",", ":")),
                json.dumps(payload, separators=(",", ":")),
            ]
        )
        messages = self.violations(path)
        self.assertTrue(any("synthetic must be true" in message for message in messages))

    def test_a_seq_that_does_not_start_at_one_is_refused(self) -> None:
        path = self.write_rows([_row(seq=0)])
        payload = json.loads(path.read_text().splitlines()[1])
        payload["seq"] = 2
        lines = path.read_text().splitlines()
        lines[1] = json.dumps(payload, separators=(",", ":"))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.assertTrue(any("start at 1" in message for message in self.violations(path)))

    def test_a_seq_that_goes_backwards_is_refused(self) -> None:
        lines = [json.dumps(_header(), separators=(",", ":"))]
        for seq in (1, 2, 2):
            payload = _row().as_dict()
            payload["seq"] = seq
            lines.append(json.dumps(payload, separators=(",", ":")))
        path = self.write_raw(lines)
        self.assertTrue(
            any("strictly increase" in message for message in self.violations(path))
        )

    def test_a_markup_that_disagrees_with_the_price_is_refused(self) -> None:
        path = self.write_rows([_row(markup=900)])
        messages = self.violations(path)
        self.assertTrue(any("markup_bps 900" in message for message in messages), messages)

    def test_a_status_outside_the_closed_set_is_refused(self) -> None:
        path = self.write_rows([_row(status="maybe")])
        self.assertTrue(any("status 'maybe'" in message for message in self.violations(path)))

    def test_a_chain_outside_the_closed_set_is_refused(self) -> None:
        path = self.write_rows([_row(chain="mainnet")])
        self.assertTrue(any("chain 'mainnet'" in message for message in self.violations(path)))

    def test_a_refused_row_without_an_error_code_is_refused(self) -> None:
        path = self.write_rows([_row(status="refused", error_code=None)])
        self.assertTrue(
            any("refused row must carry an error_code" in m for m in self.violations(path))
        )

    def test_an_ok_row_on_the_validator_without_a_signature_is_refused(self) -> None:
        path = self.write_rows([_row(signature=None)])
        self.assertTrue(
            any("must carry a signature" in message for message in self.violations(path))
        )

    def test_a_wrong_ceiling_is_refused(self) -> None:
        path = self.write_rows([_row(ceiling_lamports=1_000_000)])
        self.assertTrue(
            any("ceiling_lamports" in message for message in self.violations(path))
        )

    def test_a_non_integer_face_is_refused(self) -> None:
        payload = _row().as_dict()
        payload["face_lamports"] = "1000000"
        path = self.write_raw(
            [
                json.dumps(_header(), separators=(",", ":")),
                json.dumps(payload, separators=(",", ":")),
            ]
        )
        self.assertTrue(
            any("face_lamports must be a positive integer" in m for m in self.violations(path))
        )

    def test_every_violation_is_listed_not_just_the_first(self) -> None:
        lines = [json.dumps(_header(synthetic=False), separators=(",", ":"))]
        refused = _row(status="refused", error_code=None).as_dict()
        refused["synthetic"] = False
        refused["seq"] = 5
        lines.append(json.dumps(refused, separators=(",", ":")))
        nonsense = _row(status="nonsense").as_dict()
        nonsense["seq"] = 6
        lines.append(json.dumps(nonsense, separators=(",", ":")))
        unsigned = _row(markup=7, signature=None).as_dict()
        unsigned["seq"] = 7
        lines.append(json.dumps(unsigned, separators=(",", ":")))
        path = self.write_raw(lines)
        messages = self.violations(path)
        # header synthetic, first row synthetic, first row refused without a code, first row
        # seq not starting at 1, status, markup and signature on the last row.
        self.assertGreaterEqual(len(messages), 7)
        joined = "\n".join(messages)
        for needle in ("header synthetic", "synthetic must be true", "error_code",
                       "must carry a signature", "start at 1", "markup_bps 7",
                       "status 'nonsense'"):
            self.assertIn(needle, joined)

    def test_a_line_that_is_not_json_is_refused(self) -> None:
        path = self.write_raw([json.dumps(_header()), "{not json"])
        self.assertTrue(any("not valid JSON" in m for m in self.violations(path)))


class TestSummarise(DatasetCase):
    def _dataset(self) -> Path:
        return self.write_rows(
            [
                _row(action="buy", price=FACE, agent_id="a1"),
                _row(action="resell", price=1_100_000, agent_id="a1"),
                _row(action="resell", price=1_200_000, status="skipped", agent_id="a2",
                     signature=None),
                _row(action="resell", price=1_300_000, status="refused", agent_id="a3",
                     error_code=6010, signature="sig-2"),
                _row(action="resell", mode="monitored", price=1_400_000, agent_id="a1"),
                _row(action="resell", mode="monitored", price=1_500_000, status="skipped",
                     agent_id="a1", signature=None),
            ]
        )

    def test_counts_by_status_action_agent_and_mode(self) -> None:
        result = summarise(self._dataset())
        self.assertEqual(result["rows"], 6)
        self.assertEqual(result["by_status"], {"ok": 3, "refused": 1, "skipped": 2})
        self.assertEqual(result["by_action"], {"buy": 1, "resell": 5})
        self.assertEqual(result["by_agent"], {"a1": 4, "a2": 1, "a3": 1})
        self.assertEqual(result["by_mode"], {"capped": 4, "monitored": 2})

    def test_executed_skipped_and_refused_asks_per_mode(self) -> None:
        result = summarise(self._dataset())
        self.assertEqual(
            result["asks_by_mode"]["capped"],
            {"attempts": 3, "executed": 1, "skipped": 1, "refused": 1},
        )
        self.assertEqual(
            result["asks_by_mode"]["monitored"],
            {"attempts": 2, "executed": 1, "skipped": 1, "refused": 0},
        )

    def test_the_refusal_rate_is_per_mode_and_in_basis_points(self) -> None:
        result = summarise(self._dataset())
        self.assertEqual(result["refusal_rate_by_mode"]["capped"]["rate_bps"], 3333)
        self.assertEqual(result["refusal_rate_by_mode"]["capped"]["refused"], 1)
        self.assertEqual(result["refusal_rate_by_mode"]["monitored"]["rate_bps"], 0)

    def test_price_quantiles_are_exact_integers_per_mode(self) -> None:
        result = summarise(self._dataset())
        self.assertEqual(
            result["price_quantiles_by_mode"]["capped"],
            {"n": 2, "min": 1_000_000, "p50": 1_000_000, "p90": 1_100_000, "max": 1_100_000},
        )
        self.assertEqual(
            result["price_quantiles_by_mode"]["monitored"],
            {"n": 1, "min": 1_400_000, "p50": 1_400_000, "p90": 1_400_000, "max": 1_400_000},
        )
        self.assertEqual(result["total_notional_lamports"], 3_500_000)

    def test_the_result_says_it_is_synthetic_and_is_json_serialisable(self) -> None:
        result = summarise(self._dataset())
        self.assertIn("Synthetic data only", result["note"])
        json.dumps(result)  # raises if any value is not a plain JSON value

    def test_quantiles_use_nearest_rank_on_integers(self) -> None:
        rows = [
            _row(action="buy", price=price, agent_id="a1")
            for price in (10_000_000, 2_000_000, 4_000_000, 6_000_000)
        ]
        result = summarise(self.write_rows(rows))
        capped = result["price_quantiles_by_mode"]["capped"]
        # Nearest rank on four values: p50 is rank 2 (the second smallest), p90 is rank 4.
        self.assertEqual((capped["min"], capped["p50"], capped["p90"], capped["max"]),
                         (2_000_000, 4_000_000, 10_000_000, 10_000_000))
        self.assertIsInstance(capped["p90"], int)

    def test_an_invalid_dataset_raises_instead_of_summarising(self) -> None:
        path = self.write_rows([_row(status="maybe")])
        with self.assertRaises(DatasetInvalid):
            summarise(path)


if __name__ == "__main__":
    unittest.main()
