"""The ledger writer: header first, one compact line per row, the label enforced.

Every test that expects a refusal also checks what landed on disk, because the point of
a refusal here is that nothing was written: a refused row must not consume a `seq` and
must not leave a partial line.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import fields
from pathlib import Path

from market_swarm.ledger import (
    ACTIONS,
    CHAINS,
    LEDGER_HEADER,
    PROGRAMS,
    STATUSES,
    LedgerWriter,
    TradeRow,
)


def _row(**overrides) -> TradeRow:
    base = {
        "run_id": "sw20261107T185000Z1a2b",
        "seq": 99,  # the writer stamps its own; this value must be ignored
        "ts": "2026-11-07T18:50:00Z",
        "event_id": "evt1",
        "mode": "capped",
        "agent_id": "a1",
        "action": "buy",
        "ticket_id": "tkt1",
        "from_wallet": "house",
        "to_wallet": "wallet-a1",
        "price_lamports": 1_000_000_000,
        "face_lamports": 1_000_000_000,
        "cap_bps": 2500,
        "ceiling_lamports": 1_250_000_000,
        "markup_bps": 0,
        "status": "ok",
        "error_code": None,
        "signature": "sig",
        "slot": 7,
        "block_time": 1_794_077_400,
        "latency_ms": 12,
        "hop_index": 0,
        "budget_before": 1_000,
        "budget_after": 0,
        "chain": "local-validator",
        "program": "v1",
        "rationale": "buyer took the listing at face",
    }
    base.update(overrides)
    return TradeRow(**base)


def _header(**overrides) -> dict:
    header = dict(LEDGER_HEADER)
    header["run_id"] = "sw20261107T185000Z1a2b"
    header.update(overrides)
    return header


class TestTradeRow(unittest.TestCase):
    def test_as_dict_has_every_field_in_declaration_order(self) -> None:
        row = _row()
        expected = [field.name for field in fields(TradeRow)]
        self.assertEqual(list(row.as_dict()), expected)
        self.assertEqual(list(row.as_dict())[-1], "synthetic")

    def test_as_dict_is_json_serialisable_and_round_trips(self) -> None:
        row = _row()
        payload = row.as_dict()
        self.assertEqual(json.loads(json.dumps(payload)), payload)
        self.assertIs(payload["synthetic"], True)

    def test_the_status_and_chain_vocabularies_are_closed_sets(self) -> None:
        self.assertEqual(STATUSES, frozenset({"ok", "refused", "error", "skipped"}))
        self.assertEqual(
            CHAINS, frozenset({"local-validator", "devnet", "simulated"})
        )
        self.assertEqual(
            ACTIONS, frozenset({"buy", "list", "refuse", "resell", "unknown"})
        )
        self.assertEqual(PROGRAMS, frozenset({"v1", "v2"}))
        self.assertIsInstance(STATUSES, frozenset)
        self.assertIsInstance(CHAINS, frozenset)
        self.assertIsInstance(ACTIONS, frozenset)
        self.assertIsInstance(PROGRAMS, frozenset)

    def test_the_program_is_not_defaulted_on_the_row(self) -> None:
        # A row that forgot which program produced it would read as v1 and be a false statement
        # about its own provenance, so the field is required and the writer checks the value.
        field_names = [field.name for field in fields(TradeRow)]
        self.assertIn("program", field_names)
        self.assertEqual(field_names[field_names.index("program") - 1], "chain",
                         "the program sits with the provenance fields")
        with self.assertRaises(TypeError):
            TradeRow(**{key: value for key, value in _row().as_dict().items() if key != "program"})


class TestHeader(unittest.TestCase):
    def _read(self, path: Path) -> list[dict]:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def test_the_header_is_the_first_line_and_carries_the_required_literals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SYNTHETIC-run.jsonl"
            with LedgerWriter(path, header=_header()) as writer:
                writer.write(_row())
            lines = self._read(path)
            header = lines[0]
            self.assertEqual(header["record"], "header")
            self.assertIs(header["synthetic"], True)
            self.assertEqual(header["schema_version"], 1)
            self.assertTrue(header["label"].startswith("SYNTHETIC DATA"))
            self.assertIn("local validator", header["disclaimer"])
            self.assertIn("simulation", header["disclaimer"])
            self.assertIn("NOT evidence of real market pricing", header["disclaimer"])
            self.assertEqual(header["run_id"], "sw20261107T185000Z1a2b")
            self.assertIn("created_at", header)
            self.assertEqual(len(lines), 2)

    def test_a_header_missing_the_label_is_refused(self) -> None:
        bad = _header()
        del bad["label"]
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError) as caught:
                LedgerWriter(Path(tmp) / "x.jsonl", header=bad)
            self.assertIn("label", str(caught.exception))

    def test_a_label_that_does_not_say_synthetic_data_is_refused(self) -> None:
        bad = _header()
        bad["label"] = "agent trades"
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                LedgerWriter(Path(tmp) / "x.jsonl", header=bad)

    def test_a_header_without_the_disclaimer_is_refused(self) -> None:
        bad = _header()
        bad["disclaimer"] = "trades"
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError) as caught:
                LedgerWriter(Path(tmp) / "x.jsonl", header=bad)
            self.assertIn("disclaimer", str(caught.exception))

    def test_a_header_that_is_not_synthetic_is_refused(self) -> None:
        bad = _header()
        bad["synthetic"] = False
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                LedgerWriter(Path(tmp) / "x.jsonl", header=bad)

    def test_a_header_for_another_schema_version_is_refused(self) -> None:
        bad = _header()
        bad["schema_version"] = 2
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                LedgerWriter(Path(tmp) / "x.jsonl", header=bad)


class TestRows(unittest.TestCase):
    def _lines(self, path: Path) -> list[dict]:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def _rows(self, path: Path) -> list[dict]:
        return self._lines(path)[1:]  # line 0 is the header

    def test_seq_is_stamped_from_one_and_ignores_the_row_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SYNTHETIC-run.jsonl"
            with LedgerWriter(path, header=_header()) as writer:
                writer.write(_row())
                writer.write(_row())
                writer.write(_row())
            self.assertEqual([row["seq"] for row in self._rows(path)], [1, 2, 3])

    def test_a_row_without_a_z_suffix_gets_one(self) -> None:
        cases = {
            "": None,                                  # stamped with now, ends in Z
            "2026-11-07T18:50:00": "2026-11-07T18:50:00Z",
            "2026-11-07T20:50:00+02:00": "2026-11-07T18:50:00Z",
            "2026-11-07T18:50:00Z": "2026-11-07T18:50:00Z",
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SYNTHETIC-run.jsonl"
            with LedgerWriter(path, header=_header()) as writer:
                for ts in cases:
                    writer.write(_row(ts=ts))
            stamps = [row["ts"] for row in self._rows(path)]
        for stamp, expected in zip(stamps, cases.values()):
            if expected is None:
                self.assertTrue(stamp.endswith("Z"), stamp)
            else:
                self.assertEqual(stamp, expected)

    def test_a_row_whose_label_is_not_true_is_refused_and_nothing_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SYNTHETIC-run.jsonl"
            with LedgerWriter(path, header=_header()) as writer:
                with self.assertRaises(ValueError) as caught:
                    writer.write(_row(synthetic=False))
                self.assertIn("synthetic", str(caught.exception))
                writer.write(_row())
            lines = self._lines(path)
        self.assertEqual(len(lines), 2)          # the header and one row, no refused row
        self.assertEqual(lines[1]["seq"], 1)     # the refusal did not consume a seq

    def test_an_unknown_status_is_refused(self) -> None:
        for bad in ("done", "OK", "", "success"):
            with self.subTest(status=bad), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "SYNTHETIC-run.jsonl"
                with LedgerWriter(path, header=_header()) as writer:
                    with self.assertRaises(ValueError) as caught:
                        writer.write(_row(status=bad))
                    self.assertIn("status", str(caught.exception))
                self.assertEqual(len(self._lines(path)), 1)

    def test_an_unknown_chain_is_refused(self) -> None:
        for bad in ("mainnet", "local", "", "Local-Validator"):
            with self.subTest(chain=bad), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "SYNTHETIC-run.jsonl"
                with LedgerWriter(path, header=_header()) as writer:
                    with self.assertRaises(ValueError) as caught:
                        writer.write(_row(chain=bad))
                    self.assertIn("chain", str(caught.exception))
                self.assertEqual(len(self._lines(path)), 1)

    def test_an_unknown_program_is_refused(self) -> None:
        for bad in ("v3", "V1", "", "v1.0"):
            with self.subTest(program=bad), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "SYNTHETIC-run.jsonl"
                with LedgerWriter(path, header=_header()) as writer:
                    with self.assertRaises(ValueError) as caught:
                        writer.write(_row(program=bad))
                    self.assertIn("program", str(caught.exception))
                self.assertEqual(len(self._lines(path)), 1)

    def test_the_program_lands_on_every_row(self) -> None:
        for program in sorted(PROGRAMS):
            with self.subTest(program=program), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "SYNTHETIC-run.jsonl"
                with LedgerWriter(path, header=_header(program=program)) as writer:
                    writer.write(_row(program=program))
                header, row = self._lines(path)
                self.assertEqual(row["program"], program)
                self.assertEqual(header["program"], program)

    def test_an_unknown_action_is_refused(self) -> None:
        for bad in ("sell", "Buy", "", "buys"):
            with self.subTest(action=bad), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "SYNTHETIC-run.jsonl"
                with LedgerWriter(path, header=_header()) as writer:
                    with self.assertRaises(ValueError) as caught:
                        writer.write(_row(action=bad))
                    self.assertIn("action", str(caught.exception))
                self.assertEqual(len(self._lines(path)), 1)

    def test_a_refusal_row_is_written_with_its_own_action(self) -> None:
        # A decision nobody took is `refuse`, not `buy`. It carries no price and no move, and
        # it is the whole reason the action column has a fourth value.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SYNTHETIC-run.jsonl"
            with LedgerWriter(path, header=_header()) as writer:
                writer.write(
                    _row(
                        action="refuse",
                        status="skipped",
                        price_lamports=None,
                        markup_bps=None,
                        ticket_id=None,
                        from_wallet=None,
                        to_wallet=None,
                        signature=None,
                        slot=None,
                        block_time=None,
                        latency_ms=None,
                        hop_index=None,
                        rationale="forge-refused: the adapter's token cap is spent",
                    )
                )
            row = self._lines(path)[1]
        self.assertEqual(row["action"], "refuse")
        self.assertEqual(row["status"], "skipped")
        self.assertIsNone(row["price_lamports"])

    def test_every_closed_vocabulary_value_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SYNTHETIC-run.jsonl"
            with LedgerWriter(path, header=_header()) as writer:
                for status in sorted(STATUSES):
                    for chain in sorted(CHAINS):
                        writer.write(_row(status=status, chain=chain))
            lines = self._lines(path)
        self.assertEqual(len(lines), 1 + len(STATUSES) * len(CHAINS))

    def test_a_non_trade_row_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SYNTHETIC-run.jsonl"
            with LedgerWriter(path, header=_header()) as writer:
                with self.assertRaises(TypeError):
                    writer.write({"status": "ok"})  # type: ignore[arg-type]
            self.assertEqual(len(self._lines(path)), 1)

    def test_each_write_is_readable_before_close(self) -> None:
        # A killed run must leave a readable file, so every line is complete and flushed.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SYNTHETIC-run.jsonl"
            writer = LedgerWriter(path, header=_header())
            writer.write(_row())
            on_disk = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(on_disk), 2)
            self.assertEqual(json.loads(on_disk[1])["status"], "ok")
            self.assertTrue(path.read_text(encoding="utf-8").endswith("\n"))
            writer.close()

    def test_the_file_is_compact_json_one_object_per_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SYNTHETIC-run.jsonl"
            with LedgerWriter(path, header=_header()) as writer:
                writer.write(_row())
            # The header carries the human-readable label; the rows are machine records
            # and stay compact.
            for line in path.read_text(encoding="utf-8").splitlines()[1:]:
                self.assertNotIn(": ", line)
                self.assertNotIn(", ", line)


class TestLifecycle(unittest.TestCase):
    def test_close_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            writer = LedgerWriter(Path(tmp) / "SYNTHETIC-run.jsonl", header=_header())
            writer.close()
            writer.close()  # must not raise

    def test_a_write_after_close_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            writer = LedgerWriter(Path(tmp) / "SYNTHETIC-run.jsonl", header=_header())
            writer.close()
            with self.assertRaises(ValueError) as caught:
                writer.write(_row())
            self.assertIn("closed", str(caught.exception))

    def test_the_context_manager_closes_the_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SYNTHETIC-run.jsonl"
            with LedgerWriter(path, header=_header()) as writer:
                writer.write(_row())
            self.assertTrue(writer._handle.closed)
            self.assertTrue(path.read_text(encoding="utf-8").endswith("\n"))

    def test_parent_directories_are_created(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "out" / "SYNTHETIC-run.jsonl"
            with LedgerWriter(path, header=_header()):
                pass
            self.assertTrue(path.is_file())

    def test_an_exception_inside_the_with_still_closes_the_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SYNTHETIC-run.jsonl"
            with self.assertRaises(RuntimeError):
                with LedgerWriter(path, header=_header()) as writer:
                    writer.write(_row())
                    raise RuntimeError("boom")
            self.assertTrue(writer._handle.closed)
            self.assertEqual(len(path.read_text(encoding="utf-8").splitlines()), 2)


if __name__ == "__main__":
    unittest.main()
