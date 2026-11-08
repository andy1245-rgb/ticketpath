"""Feature 2: the console renders the recorded devnet artefact as recorded.

The measured defect these tests pin. `_chain_payload` used to render the artefact only when
its quote hash equalled the hash of the quote the page had just computed, and downgrade it to
`unverified / quote_hash_mismatch` otherwise. The artefact is recorded for one instant, so
every other instant rendered it as absent: the page printed "No devnet transaction has been
recorded." while `records/devnet-artefacts.json` verified, and the recorded signature, slot,
mint and two transfers appeared nowhere.

The rule (decision MD2). `state` answers one question: did the artefact verify. It does not
answer "is this the quote on screen". `matchesCurrentQuote` answers that, separately. The
recorded block is the file's, never the live recommendation, and a page may not print a field
the file does not carry.

The fixture artefacts here are built by `seal()` rather than pasted: the hash has to be the
grammar's own, or a test would be pinning a file the verifier rejects. The one class that
reads `records/devnet-artefacts.json` is skipped where the file is absent, because a fresh
checkout of this repository does not carry the operator's proven record.
"""

from __future__ import annotations

import datetime as dt
import html as html_module
import json
import re
import tempfile
import unittest
from pathlib import Path

from ticketpath.adapters import chain_client
from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.console import page
from ticketpath.core import labels
from ticketpath.orchestrator import Orchestrator

UTC = dt.timezone.utc
CLOCK = dt.datetime(2026, 11, 8, 12, 0, 0, tzinfo=UTC)
REAL_ARTEFACT = Path(__file__).resolve().parents[1] / "records" / "devnet-artefacts.json"

# The values the operator's artefact records, quoted here because a page that renders a
# different string renders a different transaction.
RECORDED_AS_OF = "2026-11-07T18:34:29.183Z"
RECORDED_QUOTE_ID = "q-18f4ec73dd8d8fd1"
RECORDED_SIGNATURE = (
    "2Lx6cboK8kvuJ7H6w2CELvZg3xF7cSHtBTSBXqi1w6KN2eXkQ6skqNPwnT5iVVAdrfBs5LiAau3pXiBMTtZMGCPZ"
)
RECORDED_MINT = "6RPS73X519CRCdyR7diqvcjBACEVdB2cADKewCXYnimV"
RECORDED_SLOT = 519845921
ACCEPTED_SIGNATURE = (
    "E5RCrLwWikWCdHSd5MfqEBowXsmLn2n9fwYjnSwn8NhPi9j7weahbuRhgofu8ca8MVXzQUbvPrJqENDLNab7pJf"
)
REFUSED_SIGNATURE = (
    "22dqSriig968nx8aA3YaFVt4CErgNbkwvxFtDKn2MWpcCdnA2KQhFYvhwTWZSpP64wzQjoBeMUKEZLRW1e7jKe79"
)
REFUSED_ERROR = "custom program error: 0x177a (6010 E_CAP_EXCEEDED)"


def gen_engine(artefact_path=None, clock: dt.datetime = CLOCK) -> Orchestrator:
    """The console's engine, optionally pointed at an artefact file of the test's choosing."""
    extra = {} if artefact_path is None else {"artefact_path": artefact_path}
    return Orchestrator(
        ledger=LedgerAdapter.from_fixture(),
        rpc=RpcAdapter.from_env("devnet"),
        pricing_model=PricingModelAdapter(),
        cluster="devnet",
        now=lambda: clock,
        **extra,
    )


def reading(artefact_path=None, **query) -> dict:
    """The payload the console builds for one state, with the canonical URL a server adds."""
    payload = gen_engine(artefact_path).price_guidance(**query)
    payload["canonicalUrl"] = ""
    return payload


def recorded_number(payload: dict, name: str):
    """The value behind one recorded wrapper, so an assertion is about the number not the shape."""
    return payload["chain"]["recorded"][name]["value"]


def visible(html: str) -> str:
    """The page as a reader sees it: tags gone, entities resolved, whitespace collapsed."""
    without_style = re.sub(r"<style>.*?</style>", " ", html, flags=re.S)
    plain = re.sub(r"<[^>]+>", " ", without_style)
    return re.sub(r"\s+", " ", html_module.unescape(plain))


def base_record() -> dict:
    """A devnet artefact that verifies, with the two transfer legs the publisher writes."""
    return {
        "asOf": "2026-11-07T18:00:00.000Z",
        "blockTime": 1794099003,
        "capBps": 2500,
        "checkedAt": "2026-11-08T00:50:25.281Z",
        "checkerVersion": "devnet-publish-2026-11-07",
        "cluster": "devnet",
        "eventId": "evt_syn_02",
        "faceLamports": 1000000000,
        "mint": RECORDED_MINT,
        "modelVersion": "engine-2026-11-07",
        "programId": "5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva",
        "quoteId": "q-18f4ec73dd8d8fd1",
        "recommendedLamports": 1200000000,
        "rpcUrl": "https://api.devnet.solana.com",
        "signature": "5" * 87,
        "slot": RECORDED_SLOT,
        "tierId": "tier_stg_general",
        "transfers": {
            "acceptedAtCap": {
                "blockTime": 1794099006,
                "error": None,
                "priceLamports": 1250000000,
                "signature": "A" * 87,
                "slot": 519845933,
            },
            "refusedOverCap": {
                "blockTime": 1794099023,
                "error": REFUSED_ERROR,
                "priceLamports": 1250000001,
                "signature": "R" * 87,
                "slot": 519846008,
            },
        },
    }


def seal(record: dict) -> dict:
    """Give the record the hash and memo its own fields imply, so it verifies."""
    digest = chain_client.quote_hash(record)
    record["quoteHash"] = digest
    record["memoText"] = chain_client.expected_memo(record["quoteId"], digest)
    return record


def matching_record() -> dict:
    """A record whose quote is the one the console computes for the recorded instant.

    The live recommendation at evt_syn_02 / tier_stg_general / 2026-11-07T18:00:00.000Z is
    1,380,000,000 lamports, and the quote id is derived from event, tier and instant; a record
    that states both is the quote on screen, which is the only way to reach the agreeing
    sentence from a fixture.
    """
    record = base_record()
    record["recommendedLamports"] = 1380000000
    record["quoteId"] = chain_client.quote_id_for(
        event_id=record["eventId"], tier_id=record["tierId"], as_of=record["asOf"]
    )
    return seal(record)


class ArtefactFile:
    """A temp directory holding one artefact file, for states a repo path cannot reach."""

    def __init__(self, record: dict | None) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "devnet-artefacts.json"
        if record is not None:
            self.path.write_text(json.dumps(record), encoding="utf-8")

    def close(self) -> None:
        self.directory.cleanup()


def artefact_file(test: unittest.TestCase, record: dict | None) -> Path:
    """A file the test's own cleanup removes, so no tmp directory outlives the run."""
    handle = ArtefactFile(record)
    test.addCleanup(handle.close)
    return handle.path


class TestTheRecordedBlockIsTheFiles(unittest.TestCase):
    """The payload's recorded block is read off the file, not off the live recommendation."""

    def setUp(self) -> None:
        self.record = seal(base_record())
        self.path = artefact_file(self, self.record)

    def test_a_verified_artefact_carries_its_own_instant_and_its_own_quote(self) -> None:
        chain = reading(self.path)["chain"]
        self.assertEqual(chain["state"], "verified")
        recorded = chain["recorded"]
        for name in ("asOf", "quoteId", "quoteHash", "signature"):
            with self.subTest(field=name):
                self.assertEqual(recorded[name], self.record[name])
        # The numbers are payload wrappers: badge, basis and label travel with the value.
        for name in ("recommendedLamports", "slot", "blockTime"):
            with self.subTest(field=name):
                self.assertEqual(recorded[name]["value"], self.record[name])
                self.assertEqual(recorded[name]["badge"], "DEVNET")
        self.assertEqual(recorded["cluster"], "devnet")
        self.assertEqual(recorded["mint"], self.record["mint"])
        self.assertEqual(recorded["programId"], self.record["programId"])
        self.assertEqual(recorded["checkedAt"], self.record["checkedAt"])
        self.assertEqual(recorded["checkerVersion"], self.record["checkerVersion"])
        self.assertEqual(recorded["memoText"], self.record["memoText"])
        self.assertEqual(recorded["transfers"]["acceptedAtCap"]["priceLamports"]["value"], 1250000000)
        self.assertEqual(recorded["transfers"]["refusedOverCap"]["error"], REFUSED_ERROR)

    def test_the_recorded_number_never_borrows_the_live_recommendation(self) -> None:
        """The defect MD2 names: the page showed the live number as the one on chain."""
        payload = reading(self.path)
        live = payload["decision"]["recommendedLamports"]["value"]
        self.assertNotEqual(live, self.record["recommendedLamports"])
        self.assertEqual(recorded_number(payload, "recommendedLamports"), self.record["recommendedLamports"])
        self.assertNotIn(f"recommended {live:,}", visible(page.chain_slot(payload)))

    def test_matches_current_quote_is_false_when_the_instants_differ(self) -> None:
        payload = reading(self.path)
        self.assertIs(payload["chain"]["matchesCurrentQuote"], False)
        text = visible(page.chain_slot(payload))
        # The sentence is about the QUOTE -- its id and its instant -- not about "the number":
        # on the shipped artefact the two recommendations are the same number and the old
        # sentence called them different (feature 2 review).
        self.assertIn(
            labels.render(
                "P_CHAIN_QUOTE_DISAGREE",
                liveQuoteId=payload["chain"]["quoteId"],
                liveAsOf=payload["asOf"],
                recordedQuoteId=self.record["quoteId"],
                recordedAsOf=self.record["asOf"],
            ),
            text,
        )
        self.assertNotIn(labels.render("P_CHAIN_QUOTE_AGREE", quoteId="x", asOf="y"), text)
        self.assertNotIn("is not the number the chain recorded", text)

    def test_matches_current_quote_is_true_on_the_recorded_instant(self) -> None:
        record = matching_record()
        path = artefact_file(self, record)
        payload = reading(
            path,
            event_id=record["eventId"],
            tier_id=record["tierId"],
            as_of=record["asOf"],
        )
        self.assertIs(payload["chain"]["matchesCurrentQuote"], True)
        text = visible(page.chain_slot(payload))
        self.assertIn(
            labels.render("P_CHAIN_QUOTE_AGREE", quoteId=record["quoteId"], asOf=record["asOf"]),
            text,
        )
        self.assertNotIn("is not the number the chain recorded", text)

    def test_a_field_the_file_does_not_carry_is_not_printed(self) -> None:
        """A missing mint or transfer is not filled in from anywhere, and is not rendered."""
        record = base_record()
        for name in ("mint", "programId", "transfers", "checkedAt", "checkerVersion"):
            record.pop(name, None)
        path = artefact_file(self, seal(record))
        payload = reading(path)
        self.assertEqual(payload["chain"]["state"], "verified")
        recorded = payload["chain"]["recorded"]
        self.assertIsNone(recorded["mint"])
        self.assertIsNone(recorded["programId"])
        self.assertIsNone(recorded["transfers"])
        self.assertIsNone(recorded["checkedAt"])
        text = visible(page.chain_slot(payload))
        self.assertNotIn("mint", text)
        self.assertNotIn("refused by the chain", text)
        self.assertNotIn("None", text)


class TestThreeStatesStayDistinct(unittest.TestCase):
    def test_an_absent_file_renders_absent_and_prints_no_signature(self) -> None:
        payload = reading(artefact_file(self, None))
        self.assertEqual(payload["chain"]["state"], "absent")
        self.assertIsNone(payload["chain"]["recorded"])
        self.assertIsNone(payload["chain"]["matchesCurrentQuote"])
        text = visible(page.chain_slot(payload))
        self.assertIn("No devnet transaction is recorded in the console", text)
        self.assertNotIn("Unverified:", text)

    def test_a_local_rehearsal_is_refused_as_not_devnet(self) -> None:
        record = seal(base_record() | {"cluster": "localnet"})
        path = artefact_file(self, record)
        payload = reading(path)
        self.assertEqual(payload["chain"]["state"], "unverified")
        self.assertEqual(payload["chain"]["reason"], "cluster_not_devnet")
        self.assertIsNone(payload["chain"]["recorded"])
        html = page.chain_slot(payload)
        self.assertIn("A local rehearsal was recorded and is not devnet evidence", visible(html))
        self.assertNotIn(record["signature"], html)

    def test_a_tampered_hash_is_unverified_names_the_reason_and_hides_the_signature(self) -> None:
        record = base_record()
        record["quoteHash"] = "0" * 64
        record["memoText"] = chain_client.expected_memo(record["quoteId"], record["quoteHash"])
        path = artefact_file(self, record)
        payload = reading(path)
        self.assertEqual(payload["chain"]["state"], "unverified")
        self.assertEqual(payload["chain"]["reason"], "quote_hash_mismatch")
        self.assertIsNone(payload["chain"]["recorded"])
        html = page.chain_slot(payload)
        text = visible(html)
        self.assertIn("Unverified:", text)
        self.assertIn("quote_hash_mismatch", text)
        # The absent sentence is not printed here: a tampered file is not an empty disk.
        self.assertNotIn("No devnet transaction has been recorded.", text)
        self.assertNotIn(record["signature"], html)
        self.assertNotIn("Verified at", text)

    def test_a_tampered_memo_names_its_own_reason(self) -> None:
        record = seal(base_record())
        record["memoText"] = "ticketpath:quote:q-wrong:" + "1" * 64
        path = artefact_file(self, record)
        payload = reading(path)
        self.assertEqual(payload["chain"]["reason"], "memo_grammar_mismatch")
        html = page.chain_slot(payload)
        self.assertIn("memo_grammar_mismatch", visible(html))
        self.assertNotIn(record["signature"], html)

    def test_a_file_missing_a_required_field_is_unverified(self) -> None:
        record = seal(base_record())
        record.pop("recommendedLamports")
        path = artefact_file(self, record)
        payload = reading(path)
        self.assertEqual(payload["chain"]["state"], "unverified")
        self.assertEqual(payload["chain"]["reason"], "devnet_unverified")
        self.assertIn("devnet_unverified", visible(page.chain_slot(payload)))


class TestTheProgramFactsAreThree(unittest.TestCase):
    """A program id recorded in the file, a server that asked nobody, and the design doc."""

    def setUp(self) -> None:
        self.record = seal(base_record())
        self.path = artefact_file(self, self.record)

    def test_the_slot_names_the_recorded_program_and_the_server_s_own_silence(self) -> None:
        payload = reading(self.path)
        html = page.chain_slot(payload)
        text = visible(html)
        self.assertIn(self.record["programId"], html)
        self.assertIn(labels.render("P_CHAIN_NOT_ASKED"), text)
        self.assertIn("docs/ON-CHAIN-DESIGN.md", text)
        self.assertNotIn("No program is deployed on any cluster", text)

    def test_the_program_status_never_claims_a_deployment_it_did_not_read(self) -> None:
        status = reading(self.path)["chain"]["programStatus"]
        self.assertIs(status["programDeployed"], False)
        self.assertIs(status["askedCluster"], False)
        self.assertEqual(status["designDoc"], "docs/ON-CHAIN-DESIGN.md")
        self.assertEqual(status["recorded"]["programId"], self.record["programId"])
        # The path this server actually read, not the display name of the operator's file:
        # a verified copy elsewhere may not claim to be `records/devnet-artefacts.json`.
        self.assertEqual(status["recorded"]["source"], str(self.path))
        self.assertIsNone(status["programId"])  # the configured id: nothing was configured

    def test_health_and_the_page_cannot_disagree_about_the_program(self) -> None:
        payload = reading(self.path)
        health = gen_engine(self.path).health(9, 9, 10)
        self.assertEqual(health["chain"]["recorded"]["programId"], payload["chain"]["recorded"]["programId"])
        self.assertEqual(health["chain"]["askedCluster"], payload["chain"]["programStatus"]["askedCluster"])
        self.assertIs(health["chain"]["programDeployed"], False)

    def test_an_absent_file_leaves_the_program_status_with_nothing_recorded(self) -> None:
        status = gen_engine(artefact_file(self, None)).health(9, 9, 10)["chain"]
        self.assertIsNone(status["recorded"])
        self.assertIs(status["askedCluster"], False)


class TestTheEvidenceCountFollowsTheChainBlock(unittest.TestCase):
    def test_a_verified_artefact_counts_every_signature_the_file_carries(self) -> None:
        """Three, not one: the quote memo and the two transfer legs (feature 2 review)."""
        payload = reading(artefact_file(self, seal(base_record())))
        self.assertEqual(payload["chain"]["state"], "verified")
        self.assertEqual(payload["evidence"]["onchainTransactions"]["value"], 3)
        self.assertEqual(
            payload["evidence"]["onchainTransactions"]["value"],
            payload["chain"]["signaturesRecorded"]["value"],
        )
        text = visible(page.evidence(payload))
        self.assertIn("3 on-chain transactions", text)

    def test_an_absent_artefact_counts_zero_and_names_the_label(self) -> None:
        payload = reading(artefact_file(self, None))
        self.assertEqual(payload["evidence"]["onchainTransactions"]["value"], 0)
        self.assertEqual(payload["evidence"]["onchainTransactions"]["labelId"], "devnet_absent")
        # The basis is about the file, not about the project: three devnet transactions exist
        # and only the console's file is missing.
        self.assertIn("no artefact file is present", payload["evidence"]["onchainTransactions"]["basis"])
        self.assertNotIn("has been recorded", payload["evidence"]["onchainTransactions"]["basis"])

    def test_an_unverified_artefact_says_the_file_did_not_verify(self) -> None:
        record = base_record()
        record["quoteHash"] = "0" * 64
        record["memoText"] = chain_client.expected_memo(record["quoteId"], record["quoteHash"])
        payload = reading(artefact_file(self, record))
        basis = payload["evidence"]["onchainTransactions"]["basis"]
        self.assertEqual(payload["evidence"]["onchainTransactions"]["value"], 0)
        self.assertIn("did not verify", basis)
        self.assertNotIn("nothing was recorded", basis)
        self.assertEqual(
            payload["evidence"]["onchainTransactions"]["labelId"], "devnet_unverified"
        )


@unittest.skipUnless(REAL_ARTEFACT.exists(), "the operator's proven record is not on disk")
class TestTheRealDevnetArtefact(unittest.TestCase):
    """The deliverable itself: the page a visitor sees with the proven record on disk."""

    def test_the_default_page_renders_the_recorded_transaction(self) -> None:
        payload = reading()
        chain = payload["chain"]
        self.assertEqual(chain["state"], "verified")
        recorded = chain["recorded"]
        self.assertEqual(recorded["signature"], RECORDED_SIGNATURE)
        self.assertEqual(recorded["slot"]["value"], RECORDED_SLOT)
        self.assertEqual(recorded["mint"], RECORDED_MINT)
        self.assertEqual(recorded["asOf"], RECORDED_AS_OF)
        self.assertIs(chain["matchesCurrentQuote"], False)
        html = page.chain_slot(payload)
        text = visible(html)
        self.assertIn(RECORDED_SIGNATURE, html)
        self.assertIn(str(RECORDED_SLOT), text)
        self.assertIn(RECORDED_MINT, html)
        self.assertIn("1,250,000,000", text)
        self.assertIn("1,250,000,001", text)
        self.assertIn("6010", text)
        self.assertIn("refused by the chain", text)
        self.assertIn(labels.render("P_CHAIN_QUOTE_DISAGREE", liveQuoteId=chain["quoteId"], liveAsOf=payload["asOf"], recordedQuoteId=RECORDED_QUOTE_ID, recordedAsOf=RECORDED_AS_OF), text)
        self.assertNotIn("No devnet transaction has been recorded.", text)
        self.assertNotIn("None", text)

    def test_the_recorded_instant_says_the_two_quotes_are_one(self) -> None:
        payload = reading(event_id="evt_syn_02", tier_id="tier_stg_general", as_of=RECORDED_AS_OF)
        self.assertIs(payload["chain"]["matchesCurrentQuote"], True)
        text = visible(page.chain_slot(payload))
        self.assertIn(
            labels.render("P_CHAIN_QUOTE_AGREE", quoteId=RECORDED_QUOTE_ID, asOf=RECORDED_AS_OF),
            text,
        )
        self.assertNotIn("is not the number the chain recorded", text)
        # MD2: the recorded instant is printed even where it is the instant on screen.
        self.assertIn(RECORDED_AS_OF, page.chain_slot(payload))
        self.assertIn(str(RECORDED_SLOT), text)

    def test_the_two_transfer_signatures_are_both_rendered(self) -> None:
        html = page.chain_slot(reading())
        self.assertIn(ACCEPTED_SIGNATURE, html)
        self.assertIn(REFUSED_SIGNATURE, html)


if __name__ == "__main__":
    unittest.main()
