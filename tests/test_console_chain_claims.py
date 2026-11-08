"""Feature 2, second pass: what the non-builder review found in the chain slot.

`tests/test_console_recorded_artefact.py` pins the recorded/current split. This file pins the
sentences and the file grammar around it, because the review's finding was that the split was
right and what the page said about it was not. Every class here is one finding from
tmp/review/feature-2.md, and the comment above each test names the probe that showed the old
behaviour.

The fixture artefact is built by `seal()` from the other module rather than pasted twice: the
hash has to be the grammar's own or a test would pin a file the verifier refuses.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

from ticketpath.adapters import chain_client
from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.console import page
from ticketpath.console.units import STATED
from ticketpath.core import labels
from ticketpath.orchestrator import Orchestrator
from tests.test_console_recorded_artefact import (
    ACCEPTED_SIGNATURE,
    RECORDED_QUOTE_ID,
    RECORDED_SIGNATURE,
    RECORDED_SLOT,
    REFUSED_SIGNATURE,
    artefact_file,
    base_record,
    gen_engine,
    reading,
    seal,
    visible,
)

UTC = dt.timezone.utc
CLOCK = dt.datetime(2026, 11, 8, 12, 0, 0, tzinfo=UTC)
REAL_ARTEFACT = Path(__file__).resolve().parents[1] / "records" / "devnet-artefacts.json"
RECORDED_AS_OF = "2026-11-07T18:34:29.183Z"
RECORDED_MINT = "6RPS73X519CRCdyR7diqvcjBACEVdB2cADKewCXYnimV"
RECORDED_PROGRAM = "5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva"


def real_reading(**query) -> dict:
    """The payload from the operator's proven record, for the tests that need the real one."""
    payload = gen_engine().price_guidance(**query)
    payload["canonicalUrl"] = ""
    return payload


def engine_at(path, cluster: str = "devnet") -> Orchestrator:
    return Orchestrator(
        ledger=LedgerAdapter.from_fixture(),
        rpc=RpcAdapter.from_env(cluster),
        pricing_model=PricingModelAdapter(),
        cluster=cluster,
        now=lambda: CLOCK,
        artefact_path=path,
    )


def slot_state(record: dict, test: unittest.TestCase) -> dict:
    path = artefact_file(test, seal(record))
    return reading(path)["chain"]


class TestThePagePromisesNoMechanismItDoesNotHave(unittest.TestCase):
    """CRITICAL. `page.py` promised a re-read behind TICKETPATH_RPC_ENABLED=1.

    Probe (review, 07:04Z): with all three variables set, `transfer_enforcement` still answered
    `not_queried`, "this build opens no socket", and the page still told a reader to set a flag.
    """

    def test_the_page_does_not_name_a_flag_that_performs_no_re_read(self) -> None:
        text = visible(page.chain_slot(real_reading()))
        self.assertNotIn("TICKETPATH_RPC_ENABLED", text)
        self.assertIn("A live re-read is not implemented in this build", text)

    def test_setting_the_three_variables_changes_neither_the_adapter_nor_the_page(self) -> None:
        variables = {
            "TICKETPATH_RPC_ENABLED": "1",
            "TICKETPATH_RPC_URL": "https://api.devnet.solana.com",
            "TICKETPATH_PROGRAM_ID": RECORDED_PROGRAM,
        }
        with mock.patch.dict(os.environ, variables, clear=False):
            adapter = RpcAdapter.from_env("devnet")
            # The adapter is honest about it: configured, and still no socket.
            self.assertEqual(adapter.transfer_enforcement(RECORDED_MINT)["reason"], "not_queried")
            self.assertIs(adapter.program_status()["askedCluster"], False)
            text = visible(page.chain_slot(real_reading()))
        self.assertIn("A live re-read is not implemented in this build", text)
        self.assertNotIn("TICKETPATH_RPC_ENABLED=1", text)


class TestTheHashCoversSixFieldsAndThePageSaysSo(unittest.TestCase):
    """MAJOR. A file whose `signature` was 88 "F"s verified and rendered as chain evidence.

    Probe: a re-sealed copy with the signature replaced verified (`state: verified`) and the
    page printed the forgery beside the file's real slot and explorer link.
    """

    def test_the_forged_signature_file_is_refused_and_nothing_of_it_is_rendered(self) -> None:
        chain = slot_state(base_record() | {"signature": "F" * 88}, self)
        self.assertEqual(chain["state"], "unverified")
        self.assertEqual(chain["reason"], "signature_malformed")
        html = page.chain_slot({"chain": chain})
        self.assertNotIn("F" * 16, html)
        self.assertNotIn(str(RECORDED_SLOT), visible(page.chain_slot({"chain": chain})))
        self.assertNotIn("explorer.solana.com", html)
        self.assertIn("signature_malformed", visible(page.chain_slot({"chain": chain})))

    def test_the_page_names_the_six_fields_the_hash_covers(self) -> None:
        text = visible(page.chain_slot(real_reading()))
        self.assertIn(labels.render("P_CHAIN_FILE_COVERAGE"), text)
        for phrase in ("quote id", "event", "tier", "recommended price", "instant", "model version"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, labels.render("P_CHAIN_FILE_COVERAGE"))
        self.assertIn("writer's assertion", text)

    def test_a_value_the_hash_does_not_cover_is_not_badged_as_devnet(self) -> None:
        html = page.chain_slot(real_reading())
        spans = re.findall(r'<span class="n">(.*?)</span>', html, flags=re.S)
        # The slot, the block time, the face and the cap, and both transfer prices and slots,
        # are the file's assertion: they carry the words, not the badge.
        stated = [span for span in spans if span.startswith(STATED)]
        self.assertGreaterEqual(len(stated), 8)
        self.assertNotIn(str(RECORDED_SLOT), " ".join(
            span for span in spans if not span.startswith(STATED)
        ))
        self.assertIn(f"slot <span class=\"n\">{STATED} {RECORDED_SLOT}</span>", html)
        # The recommendation is one of the six, so its badge is a claim the hash backs.
        self.assertIn('[DEVNET] 1,380,000,000 lamports', html)

    def test_the_payload_says_itself_which_recorded_numbers_the_hash_covers(self) -> None:
        recorded = real_reading()["chain"]["recorded"]
        self.assertIs(recorded["recommendedLamports"]["coveredByQuoteHash"], True)
        for name in ("slot", "blockTime", "capBps", "faceLamports"):
            with self.subTest(field=name):
                self.assertIs(recorded[name]["coveredByQuoteHash"], False)
        self.assertIs(
            recorded["transfers"]["acceptedAtCap"]["priceLamports"]["coveredByQuoteHash"], False
        )


class TestTheFileGrammarIsCheckedBeforeThePagePrintsIt(unittest.TestCase):
    """MAJOR. The hash covers six fields; the rest was never checked and printed as identity."""

    def test_a_signature_that_is_not_base58_is_refused(self) -> None:
        chain = slot_state(base_record() | {"signature": "0" * 88}, self)
        self.assertEqual(chain["reason"], "signature_malformed")

    def test_a_slot_that_is_not_a_whole_number_is_refused(self) -> None:
        chain = slot_state(base_record() | {"slot": str(RECORDED_SLOT)}, self)
        self.assertEqual(chain["reason"], "slot_malformed")

    def test_a_block_time_that_is_not_a_whole_number_is_refused(self) -> None:
        chain = slot_state(base_record() | {"blockTime": "1794099003"}, self)
        self.assertEqual(chain["reason"], "block_time_malformed")

    def test_a_mint_that_is_not_a_thirty_two_byte_address_is_refused(self) -> None:
        chain = slot_state(base_record() | {"mint": "not-an-address"}, self)
        self.assertEqual(chain["reason"], "mint_malformed")

    def test_a_program_id_that_is_not_a_thirty_two_byte_address_is_refused(self) -> None:
        chain = slot_state(base_record() | {"programId": "abc"}, self)
        self.assertEqual(chain["reason"], "program_id_malformed")

    def test_a_mint_that_is_also_the_program_id_is_refused(self) -> None:
        record = base_record()
        record["programId"] = record["mint"]
        chain = slot_state(record, self)
        self.assertEqual(chain["reason"], "mint_is_program")

    def test_a_memo_program_that_is_not_the_measured_one_is_refused(self) -> None:
        chain = slot_state(
            base_record() | {"memoProgram": "BogusMemo1111111111111111111111111111111111"}, self
        )
        self.assertEqual(chain["reason"], "memo_program_mismatch")
        self.assertNotIn("BogusMemo", page.chain_slot({"chain": chain}))

    def test_the_measured_memo_program_for_the_cluster_still_verifies(self) -> None:
        chain = slot_state(
            base_record() | {"memoProgram": chain_client.memo_program_id("devnet")}, self
        )
        self.assertEqual(chain["state"], "verified")

    def test_a_file_with_no_memo_is_refused(self) -> None:
        """The memo is what ties the signature to the quote; it used to be optional."""
        record = base_record()
        chain = slot_state(record, self)
        self.assertEqual(chain["state"], "verified")  # sealed, so it has a memo
        del record["memoText"]
        record["quoteHash"] = chain_client.quote_hash(record)
        path = artefact_file(self, record)
        chain = reading(path)["chain"]
        self.assertEqual(chain["reason"], "memo_missing")
        self.assertNotIn("one quote memo", visible(page.chain_slot({"chain": chain})))

    def test_every_refusal_reason_has_its_own_sentence(self) -> None:
        for reason in (
            "signature_malformed",
            "slot_malformed",
            "block_time_malformed",
            "mint_malformed",
            "program_id_malformed",
            "mint_is_program",
            "memo_program_mismatch",
            "memo_missing",
        ):
            with self.subTest(reason=reason):
                self.assertTrue(labels.render(reason))
                self.assertIsNone(labels.contains_banned(labels.render(reason)))

    @unittest.skipUnless(REAL_ARTEFACT.exists(), "the operator's record is not on disk")
    def test_the_shipped_file_still_passes_every_check(self) -> None:
        chain = real_reading()["chain"]
        self.assertEqual(chain["state"], "verified")
        self.assertEqual(chain["recorded"]["signature"], RECORDED_SIGNATURE)


class TestAVerifiedFileAlwaysRenders(unittest.TestCase):
    """MAJOR. A verified file whose transfers were malformed 500'd the whole page.

    Probe: a string price, a float price, a text slot and an int signature each answered
    `GET / -> 500` with the failure page; `/health` stayed 200. An int `error` rendered as a
    Python dict under a [DEVNET] badge.
    """

    def test_a_string_price_renders_and_prints_nothing_for_the_price(self) -> None:
        record = base_record()
        record["transfers"]["acceptedAtCap"]["priceLamports"] = "987654321"
        payload = reading(artefact_file(self, seal(record)))
        text = visible(page.render(payload))
        self.assertEqual(payload["chain"]["state"], "verified")
        self.assertNotIn("987654321", text)
        # The row still renders, and the price cell is empty rather than a string.
        self.assertIn("acceptedAtCap", text)

    def test_a_float_price_prints_nothing_for_the_price(self) -> None:
        record = base_record()
        record["transfers"]["acceptedAtCap"]["priceLamports"] = 987654321.5
        payload = reading(artefact_file(self, seal(record)))
        self.assertNotIn("987,654,321", visible(page.render(payload)))

    def test_a_text_slot_prints_nothing_for_the_slot(self) -> None:
        record = base_record()
        record["transfers"]["acceptedAtCap"]["slot"] = "987654321"
        payload = reading(artefact_file(self, seal(record)))
        self.assertNotIn("987654321", visible(page.render(payload)))

    def test_an_int_signature_prints_no_link_and_no_slice(self) -> None:
        record = base_record()
        record["signature"] = 12345
        chain = reading(artefact_file(self, seal(record)))["chain"]
        # The loader refuses it by name, so the page renders the refusal and not a slice.
        self.assertEqual(chain["state"], "unverified")
        self.assertEqual(chain["reason"], "signature_malformed")

    def test_an_int_error_prints_a_sentence_not_a_dict(self) -> None:
        record = base_record()
        record["transfers"]["refusedOverCap"]["error"] = 42
        payload = reading(artefact_file(self, seal(record)))
        text = visible(page.render(payload))
        self.assertNotIn("{'value'", text)
        self.assertNotIn("'badge'", text)
        self.assertIn("the file's error is not a string, so it is not shown", text)

    def test_the_page_survives_a_payload_built_elsewhere(self) -> None:
        """The page is the surface, so it type-checks too: a payload is not a contract."""
        chain = {
            "state": "verified",
            "recorded": {
                "signature": 1234,
                "slot": "519845921",
                "blockTime": 1.5,
                "transfers": {
                    "acceptedAtCap": {
                        "priceLamports": "1250000000",
                        "slot": "519845933",
                        "signature": 99,
                        "error": 7,
                    }
                },
            },
            "matchesCurrentQuote": None,
            "quoteId": "q-test",
            "memoText": "ticketpath:quote:q-test:" + "0" * 64,
            "programStatus": {"askedCluster": False, "cluster": "devnet"},
        }
        html = page.chain_slot({"chain": chain})
        text = visible(html)
        self.assertNotIn("519845921", text)
        self.assertNotIn("1250000000", text)
        self.assertNotIn("{'value'", text)

    def test_a_string_price_answers_two_hundred_over_the_wire(self) -> None:
        record = base_record()
        record["transfers"]["acceptedAtCap"]["priceLamports"] = "987654321"
        path = artefact_file(self, seal(record))
        server, thread, base = _serve(engine_at(path))
        try:
            self.assertEqual(_get(base + "/")[0], 200)
            self.assertEqual(_get(base + "/health")[0], 200)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


def _serve(engine):
    from ticketpath.server import make_server

    server = make_server(0, "127.0.0.1", engine)
    server.RequestHandlerClass.log_message = lambda *args, **kwargs: None
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, f"http://127.0.0.1:{server.server_address[1]}"


def _get(url):
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8", "replace")


class TestTheExplorerLinkIsChecked(unittest.TestCase):
    """MAJOR. The href was escaped but its scheme was not: `javascript:` rendered as a link."""

    def _html_for(self, url) -> str:
        record = base_record()
        record["explorer"] = {"transaction": url}
        return page.chain_slot(reading(artefact_file(self, seal(record))))

    def test_a_javascript_url_is_not_an_anchor(self) -> None:
        html = self._html_for("javascript:alert(1)")
        self.assertNotIn("<a href", html)
        self.assertNotIn("javascript:", html)
        # The signature is still printed, as text: the reader loses the link, not the fact.
        self.assertIn("transaction <code>", html)
        self.assertIn("5" * 87, html)

    def test_a_data_url_is_not_an_anchor(self) -> None:
        html = self._html_for("data:text/html,<script>alert(1)</script>")
        self.assertNotIn("<a href", html)

    def test_an_https_url_on_another_host_is_not_an_anchor(self) -> None:
        html = self._html_for(f"https://elsewhere.example/tx/{RECORDED_SIGNATURE}")
        self.assertNotIn("<a href", html)
        self.assertIn("transaction <code>", html)

    def test_userinfo_cannot_smuggle_another_host_past_the_check(self) -> None:
        html = self._html_for(f"https://explorer.solana.com@elsewhere.example/tx/{RECORDED_SIGNATURE}")
        self.assertNotIn("<a href", html)

    def test_the_files_own_explorer_url_still_renders_as_a_link(self) -> None:
        html = page.chain_slot(real_reading())
        self.assertIn('href="https://explorer.solana.com/tx/', html)


class TestTheAgreementSentenceIsAboutTheQuote(unittest.TestCase):
    """MAJOR. The page said the number was not the recorded one while printing 1.38 SOL twice.

    Probe: on the default page the headline recommendation and the recorded recommendation were
    both 1,380,000,000 lamports, and the sentence said "the number on this page is ... not the
    number the chain recorded".
    """

    def test_the_equal_numbers_are_printed_once_and_the_sentence_says_so(self) -> None:
        payload = real_reading()
        headline = payload["decision"]["recommendedLamports"]["value"]
        recorded = payload["chain"]["recorded"]["recommendedLamports"]["value"]
        self.assertEqual(headline, recorded)
        html = page.chain_slot(payload)
        text = visible(html)
        self.assertIn("and this page recommends the same number.", text)
        self.assertNotIn("and this page recommends [", text)
        self.assertNotIn("is not the number the chain recorded", text)
        self.assertEqual(html.count("1,380,000,000"), 2)  # the decision block and the recorded one

    def test_the_sentence_names_both_quotes_and_both_instants(self) -> None:
        payload = real_reading()
        text = visible(page.chain_slot(payload))
        for fragment in (
            payload["chain"]["quoteId"],
            payload["asOf"],
            RECORDED_QUOTE_ID,
            RECORDED_AS_OF,
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)
        self.assertIn(labels.render("P_CHAIN_QUOTE_DISAGREE", liveQuoteId="a", liveAsOf="b",
                                    recordedQuoteId="c", recordedAsOf="d").split(".")[0], text)

    def test_both_numbers_are_printed_when_they_differ(self) -> None:
        record = base_record()  # recommends 1,200,000,000 where the page recommends 1,380,000,000
        payload = reading(artefact_file(self, seal(record)))
        text = visible(page.chain_slot(payload))
        self.assertIn("1,200,000,000 lamports", text)
        self.assertIn("1,380,000,000 lamports", text)

    def test_the_agreeing_sentence_is_about_the_quote_and_names_it(self) -> None:
        payload = real_reading(event_id="evt_syn_02", tier_id="tier_stg_general", as_of=RECORDED_AS_OF)
        self.assertIs(payload["chain"]["matchesCurrentQuote"], True)
        text = visible(page.chain_slot(payload))
        self.assertIn(
            labels.render("P_CHAIN_QUOTE_AGREE", quoteId=RECORDED_QUOTE_ID, asOf=RECORDED_AS_OF),
            text,
        )
        self.assertNotIn("The number on this page", text)

    def test_the_recorded_tier_and_event_are_rendered(self) -> None:
        html = page.chain_slot(real_reading())
        self.assertIn("evt_syn_02", html)
        self.assertIn("tier_stg_general", html)

    def test_the_recorded_cap_face_and_ceiling_are_printed(self) -> None:
        payload = real_reading()
        recorded = payload["chain"]["recorded"]
        self.assertEqual(recorded["capBps"]["value"], 2500)
        self.assertEqual(recorded["faceLamports"]["value"], 1000000000)
        text = visible(page.chain_slot(payload))
        self.assertIn(f"cap {STATED} 2,500 bps", text)
        self.assertIn(f"face {STATED} 1,000,000,000 lamports", text)
        self.assertIn("resale ceiling at [EXACT] 1,250,000,000 lamports", text)

    def test_the_page_says_the_recorded_recommendation_is_above_the_files_own_ceiling(self) -> None:
        """1,380,000,000 against the 1,250,000,000 its own cap and face imply."""
        text = visible(page.chain_slot(real_reading()))
        self.assertIn("The recorded recommendation of [DEVNET] 1,380,000,000 lamports is above that ceiling.", text)

    def test_the_page_says_which_parameters_its_own_number_was_computed_under(self) -> None:
        text = visible(page.chain_slot(real_reading()))
        self.assertIn("[DECLARED] 1,500 bps", text)
        self.assertIn("[FIXTURE] 1,200,000,000 lamports", text)
        self.assertIn("which are the store's, not the file's", text)

    def test_that_sentence_is_not_printed_when_the_parameters_are_the_same(self) -> None:
        """A file stating the fixture's own cap and face: nothing differs, so nothing is said."""
        record = seal(base_record() | {"capBps": 1500, "faceLamports": 1200000000})
        text = visible(page.chain_slot(reading(artefact_file(self, record))))
        self.assertNotIn("which are the store's, not the file's", text)


class TestTheTransferRowIsTheFilesOwn(unittest.TestCase):
    """MAJOR. The row label was a page constant saying "at the cap"."""

    def test_the_leg_keys_are_printed_as_the_file_spells_them(self) -> None:
        text = visible(page.chain_slot(real_reading()))
        self.assertIn("acceptedAtCap", text)
        self.assertIn("refusedOverCap", text)
        self.assertNotIn("at the cap", text)
        self.assertNotIn("one lamport over the cap", text)

    def test_the_file_s_face_and_cap_are_printed_beside_the_table(self) -> None:
        html = page.chain_slot(real_reading())
        text = visible(html)
        table = html[html.index("<table>"):]
        # Both are on the page, and the leg the file calls acceptedAtCap is exactly the
        # ceiling its own face and cap imply: 1,000,000,000 x (10,000 + 2,500) / 10,000.
        self.assertIn(f"face {STATED} 1,000,000,000 lamports", text)
        self.assertIn(f"cap {STATED} 2,500 bps", text)
        self.assertIn("1,250,000,000 lamports", table)


class TestTheAbsentAndOtherClusterSentences(unittest.TestCase):
    """MAJOR. The absent sentence claimed the project had no devnet transaction."""

    def test_the_absent_sentence_is_about_the_file(self) -> None:
        payload = reading(artefact_file(self, None))
        text = visible(page.chain_slot(payload))
        self.assertIn("No devnet transaction is recorded in the console's artefact file.", text)
        self.assertNotIn("has been recorded for this project", text)
        self.assertNotIn("No devnet transaction has been recorded.", text)

    def test_a_testnet_file_names_testnet_and_is_not_called_a_rehearsal(self) -> None:
        record = seal(base_record() | {"cluster": "testnet"})
        payload = reading(artefact_file(self, record))
        self.assertEqual(payload["chain"]["reason"], "cluster_not_devnet")
        self.assertEqual(payload["chain"]["reasonCluster"], "testnet")
        text = visible(page.chain_slot(payload))
        self.assertIn("recorded on cluster testnet", text)
        self.assertNotIn("A local rehearsal was recorded", text)

    def test_a_localnet_file_names_localnet_and_says_it_is_a_rehearsal(self) -> None:
        record = seal(base_record() | {"cluster": "localnet"})
        text = visible(page.chain_slot(reading(artefact_file(self, record))))
        self.assertIn("recorded on cluster localnet", text)
        self.assertIn("A local rehearsal was recorded and is not devnet evidence", text)


class TestTheCheckerClockAndThePathRead(unittest.TestCase):
    """MINOR. `checkedAt` is the checker's clock and carried a [DEVNET] badge."""

    def test_the_checker_timestamp_is_not_badged(self) -> None:
        html = page.chain_slot(real_reading())
        text = visible(html)
        self.assertNotIn("[DEVNET] 2026-11-08T00:50:25.281Z", text)
        self.assertIn("The checker wrote 2026-11-08T00:50:25.281Z", text)

    def test_the_page_prints_the_path_it_read_not_a_constant(self) -> None:
        record = seal(base_record())
        path = artefact_file(self, record)
        payload = reading(path)
        self.assertEqual(payload["chain"]["programStatus"]["recorded"]["source"], str(path))
        text = visible(page.chain_slot(payload))
        self.assertIn(str(path), text)
        self.assertNotIn("records/devnet-artefacts.json", text)

    @unittest.skipUnless(REAL_ARTEFACT.exists(), "the operator's record is not on disk")
    def test_the_operator_file_keeps_its_short_name(self) -> None:
        payload = real_reading()
        self.assertEqual(payload["chain"]["source"], "records/devnet-artefacts.json")
        self.assertIn(
            "records/devnet-artefacts.json",
            visible(page.chain_slot(payload)),
        )


class TestAClusterWithNoMeasuredMemoProgramSaysSo(unittest.TestCase):
    """The review's finding on the testnet server: nothing on the page named the silence."""

    def test_a_testnet_server_says_the_cluster_has_no_measured_memo_program(self) -> None:
        engine = engine_at(REAL_ARTEFACT, cluster="testnet")
        payload = engine.price_guidance()
        payload["canonicalUrl"] = ""
        self.assertIsNone(payload["chain"]["memoProgram"])
        text = visible(page.chain_slot(payload))
        self.assertIn(
            labels.render("P_CHAIN_NO_MEMO_PROGRAM", cluster="testnet"), text
        )

    def test_a_devnet_server_names_the_measured_memo_program_nowhere_it_should_not(self) -> None:
        payload = real_reading()
        self.assertEqual(payload["chain"]["memoProgram"], chain_client.memo_program_id("devnet"))
        self.assertNotIn(
            "no memo program id has been measured",
            visible(page.chain_slot(payload)),
        )


if __name__ == "__main__":
    unittest.main()
