"""The two machine-readable surfaces beside the console: `/guidance.json` and `/devnet-record.json`.

They are not contract endpoints and they are not in `ROUTES`; they are projections of the
console, served outside the route table for the same reason the page is. Four properties
matter here and each one has a failure it prevents:

1. `/guidance.json` prints the console payload's refusals, in the console's own words, with
   a count that is the length of the list. A second composition of the same sentence is how
   the two surfaces would come to disagree, so the test follows one sentence from the page
   to the JSON and pins a whole rendered line.
2. `/devnet-record.json` reads through `Orchestrator.devnet_record`, the loader the chain
   slot uses, and reports an absent file as absent instead of as an empty record.
3. A wrong verb gets the console's rendered 405, not the interpreter's 501 page.
4. `/health.contract.routesImplemented` stays at ten and `endpointsImplemented` at nine:
   counting a surface that is not in `API_CONTRACT.md` would make the health block claim a
   contract the frontend does not have.
"""

from __future__ import annotations

import datetime as dt
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.console import blocks, units
from ticketpath.orchestrator import DEVNET_RECORD_NOTE, Orchestrator
from ticketpath.server import CONSOLE_PATHS, EVIDENCE_PATHS, ROUTES, make_server

UTC = dt.timezone.utc
CLOCK = dt.datetime(2026, 11, 7, 12, 0, 0, tzinfo=UTC)
# A path no run creates, so the absent state is reachable without touching the real artefact.
MISSING_ARTEFACT = Path(tempfile.gettempdir()) / "ticketpath-no-such-artefact.json"


def _orchestrator(artefact_path: Path | None = None) -> Orchestrator:
    return Orchestrator(
        LedgerAdapter.from_fixture(),
        RpcAdapter.from_env("devnet"),
        PricingModelAdapter(),
        "devnet",
        now=lambda: CLOCK,
        artefact_path=artefact_path,
    )


class _Server(unittest.TestCase):
    """One server per class, on a port the OS chooses, torn down with the class."""

    orchestrator_kwargs: dict = {}

    @classmethod
    def setUpClass(cls) -> None:
        cls.server = make_server(0, "127.0.0.1", _orchestrator(**cls.orchestrator_kwargs))
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def request(self, path: str, method: str = "GET") -> tuple[int, bytes, str]:
        request = urllib.request.Request(self.base + path, method=method)
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, response.read(), response.headers.get("content-type", "")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read(), exc.headers.get("content-type", "")

    def get_json(self, path: str) -> tuple[int, dict]:
        status, body, content_type = self.request(path)
        self.assertIn("application/json", content_type, path)
        return status, json.loads(body.decode("utf-8"))


class GuidanceJsonTest(_Server):
    def test_the_default_state_is_the_console_default_event_and_six_refusals(self) -> None:
        # The default event is whatever the console prices with no query string, which is
        # the state a page prints before anyone selects anything. The count is the length
        # of the list beside it; the film's "four more" is true only for a state whose
        # count is six, so the number is measured rather than assumed.
        status, document = self.get_json("/guidance.json")
        self.assertEqual(status, 200)
        self.assertEqual(document["source"], "the console payload, computed by ticketpath.orchestrator.price_guidance")
        self.assertEqual(document["event"]["id"], "evt_syn_02")
        self.assertEqual(document["event"]["slug"], "synthetic-stage-cap-binding")
        self.assertEqual(document["event"]["capBps"], 1500)
        self.assertEqual(document["tier"], {"id": "tier_stg_general", "name": "General"})
        self.assertEqual(document["count"], 6)
        self.assertEqual(document["count"], len(document["refusals"]))
        codes = [row["code"] for row in document["refusals"]]
        self.assertIn("no_upper_bound", codes)
        self.assertIn("not_identified", codes)
        self.assertEqual(codes[-1], "insufficient_events")
        self.assertIn("/?event=evt_syn_02", document["canonicalUrl"])

    def test_a_refusal_sentence_is_the_one_the_page_prints(self) -> None:
        # The same sentence, twice, from one composition: the page escapes it into an `<li>`
        # and the JSON prints it plain. Pinning the whole line is what makes a later change
        # to either surface fail here rather than on camera.
        _, document = self.get_json("/guidance.json")
        sentence = next(row["sentence"] for row in document["refusals"] if row["code"] == "no_upper_bound")
        self.assertEqual(sentence, "We do not state an upper bound from this record.")
        _, page, _ = self.request("/")
        self.assertIn(
            f"<li>[REFUSED] no_upper_bound: {units.esc(sentence)}</li>",
            page.decode("utf-8"),
        )
        # No markup and no row badge in the JSON's own form.
        for row in document["refusals"]:
            self.assertNotIn("<", row["sentence"])
            self.assertFalse(row["sentence"].startswith("[REFUSED]"))
            self.assertTrue(row["sentence"].strip())
            self.assertTrue(row["labelId"])

    def test_the_default_count_is_the_number_of_refusal_rows_on_the_page(self) -> None:
        _, page, _ = self.request("/")
        _, document = self.get_json("/guidance.json")
        rows = page.decode("utf-8").count("<li>[REFUSED]")
        self.assertEqual(rows, document["count"])

    def test_the_query_string_selects_the_same_state_as_the_page(self) -> None:
        _, document = self.get_json("/guidance.json?event=evt_syn_01")
        self.assertEqual(document["event"]["id"], "evt_syn_01")
        self.assertEqual(document["event"]["slug"], "synthetic-hall-cap-not-binding")
        self.assertEqual(document["count"], 5)
        self.assertNotIn("no_upper_bound", [row["code"] for row in document["refusals"]])
        _, page, _ = self.request("/?event=evt_syn_01")
        self.assertEqual(page.decode("utf-8").count("<li>[REFUSED]"), 5)

    def test_a_cap_in_the_url_is_the_cap_the_document_reports(self) -> None:
        _, document = self.get_json("/guidance.json?event=evt_syn_02&capBps=298")
        self.assertEqual(document["event"]["capBps"], 1500, "the record's own cap does not move")
        self.assertIn("capBps=298", document["canonicalUrl"])

    def test_a_bad_parameter_is_a_json_error_not_a_page(self) -> None:
        status, document = self.get_json("/guidance.json?asOf=nope")
        self.assertEqual(status, 400)
        self.assertEqual(document["status"], 400)
        self.assertIn("message", document)
        self.assertTrue(document["code"])

    def test_head_answers_headers_and_no_body(self) -> None:
        status, body, content_type = self.request("/guidance.json", method="HEAD")
        self.assertEqual(status, 200)
        self.assertEqual(body, b"")
        self.assertIn("application/json", content_type)

    def test_a_wrong_verb_gets_the_consoles_rendered_405(self) -> None:
        for path in EVIDENCE_PATHS:
            with self.subTest(path=path):
                status, body, content_type = self.request(path, method="POST")
                self.assertEqual(status, 405)
                self.assertIn("text/html", content_type)
                self.assertIn("is not allowed here; allowed: GET, HEAD", body.decode("utf-8"))


class DevnetRecordJsonTest(_Server):
    def test_the_verified_record_is_what_the_loader_returned(self) -> None:
        status, document = self.get_json("/devnet-record.json")
        self.assertEqual(status, 200)
        self.assertEqual(document["source"], "records/devnet-artefacts.json")
        self.assertEqual(document["note"], DEVNET_RECORD_NOTE)
        self.assertIn("asked no cluster", document["note"])
        self.assertTrue(document["loaded"])
        self.assertEqual(document["record"]["state"], "verified")
        self.assertEqual(document["record"]["cluster"], "devnet")
        self.assertNotIn("reason", document)
        # The two legs the film needs, as the file records them. The recommendation is in
        # the record too, because the route carries the loader's own dictionary unchanged;
        # this test does not print it.
        self.assertEqual(document["record"]["faceLamports"], 1_000_000_000)
        self.assertEqual(document["record"]["capBps"], 2500)
        transfers = document["record"]["transfers"]
        self.assertIsNone(transfers["acceptedAtCap"]["error"])
        self.assertIn("6010", transfers["refusedOverCap"]["error"])

    def test_head_answers_headers_and_no_body(self) -> None:
        status, body, content_type = self.request("/devnet-record.json", method="HEAD")
        self.assertEqual(status, 200)
        self.assertEqual(body, b"")
        self.assertIn("application/json", content_type)

    def test_a_wrong_verb_gets_the_consoles_rendered_405(self) -> None:
        status, body, content_type = self.request("/devnet-record.json", method="DELETE")
        self.assertEqual(status, 405)
        self.assertIn("text/html", content_type)
        self.assertIn("is not allowed here", body.decode("utf-8"))


class DevnetRecordAbsentTest(_Server):
    orchestrator_kwargs = {"artefact_path": MISSING_ARTEFACT}

    def test_an_absent_file_is_reported_as_absent_with_no_record(self) -> None:
        status, document = self.get_json("/devnet-record.json")
        self.assertEqual(status, 200)
        self.assertFalse(document["loaded"])
        self.assertIsNone(document["record"])
        self.assertIn("no artefact file is present", document["reason"])
        self.assertEqual(document["source"], str(MISSING_ARTEFACT))
        self.assertEqual(document["note"], DEVNET_RECORD_NOTE)


class RouteTableTest(_Server):
    def test_the_surfaces_are_outside_the_route_table(self) -> None:
        self.assertEqual(len(ROUTES), 10)
        paths = {"/" + "/".join(template) for _, template, _ in ROUTES}
        for surface in EVIDENCE_PATHS + CONSOLE_PATHS:
            self.assertNotIn(surface, paths)

    def test_health_still_counts_ten_routes_and_nine_contract_endpoints(self) -> None:
        status, health = self.get_json("/health")
        self.assertEqual(status, 200)
        self.assertEqual(health["contract"]["routesImplemented"], 10)
        self.assertEqual(health["contract"]["endpointsImplemented"], 9)
        self.assertEqual(health["contract"]["endpointsInContract"], 9)


class RefusalLineUnitTest(unittest.TestCase):
    """The two wrappers, on one payload, without a socket."""

    def payload(self, refusals: list[dict]) -> dict:
        payload = _orchestrator().price_guidance(event_id="evt_syn_02")
        payload["refusals"] = refusals
        return payload

    def test_the_badge_and_the_code_belong_to_the_row_not_the_sentence(self) -> None:
        payload = self.payload([{"code": "no_upper_bound", "labelId": "no_upper_bound", "reason": None}])
        (line,) = blocks.refusal_lines(payload)
        self.assertEqual((line.code, line.label_id), ("no_upper_bound", "no_upper_bound"))
        self.assertEqual(line.sentence, "We do not state an upper bound from this record.")
        self.assertEqual(
            blocks.refusals(payload).split("<ul>")[1],
            "<li>[REFUSED] no_upper_bound: We do not state an upper bound from this record.</li></ul></section>",
        )

    def test_a_path_that_answered_keeps_its_own_badge_and_no_code_prefix(self) -> None:
        payload = self.payload([{"code": "path_answered", "labelId": "A15", "reason": None}])
        (line,) = blocks.refusal_lines(payload)
        self.assertEqual(line.tag, "[UNVALIDATED]")
        self.assertFalse(line.names_code)
        self.assertTrue(line.sentence.startswith("path curvature: "))
        self.assertIn("<li>[UNVALIDATED] path curvature: ", blocks.refusals(payload))


if __name__ == "__main__":
    unittest.main()
