"""The publish script's public surface: the artefact, the grammar, and the bytes on the wire.

Nothing here needs a cluster, a Solana binary or a keypair. The artefact is built by a pure
function, the quote comes from the console's own code, and the two byte-level claims -- the
transaction message and the transfer instruction -- are pinned against samples measured from
the toolchain (see `tests/test_solana_sign.py` for the signer).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
for entry in (str(REPO_ROOT), str(REPO_ROOT / "tools")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

import devnet_publish as dp  # noqa: E402
from ticketpath.adapters import chain_client  # noqa: E402
from ticketpath.console import page  # noqa: E402
from ticketpath.core import base58  # noqa: E402

SIGNATURE = "4vJ9JU1bJJE96FWSJKvHsmmFADCg4gpZQff4P3bkLKi" + "1" * 24  # a shape, not a real one
MEMO_SIGNATURE = "2NrUUq5fkjbxeTZEmoRwceK2okpiwQ7CoFrF7Q3u9GnhR6FfYUQ2CeLqmaXkj8ESfWwqREVkwVXHaSu6JbSiiE3c"


def console_quote() -> dict:
    """The quote the console renders for the pinned instant. Pure: fixtures, no network."""
    return dp.console_quote()


def artefact(*, cluster: str = "devnet", quote: dict | None = None, memo: dict | None = None) -> dict:
    quote = quote or console_quote()
    return dp.build_artefact(
        cluster=cluster,
        rpc_url="https://api.devnet.solana.com" if cluster == "devnet" else "http://127.0.0.1:1",
        quote=quote,
        memo=memo or {"signature": MEMO_SIGNATURE, "slot": 679, "blockTime": 1_762_000_000},
        mint="7jobXedkdwKo94PLenYcHzSB4J2QgvDihRKSTGjWahz5",
        program_id="BMrcjbC2mq99YnFKkDGJDK9x1wchDmytotuhrSkfRLWQ",
        transfers={
            "acceptedAtCap": {
                "signature": SIGNATURE,
                "slot": 1150,
                "blockTime": 1_762_000_100,
                "priceLamports": dp.ACCEPTED_PRICE_LAMPORTS,
                "error": None,
                "explorer": dp.explorer_url("tx", SIGNATURE, cluster),
            },
            "refusedOverCap": {
                "signature": SIGNATURE,
                "slot": 1134,
                "blockTime": 1_762_000_050,
                "priceLamports": dp.REFUSED_PRICE_LAMPORTS,
                "error": "custom program error: 0x177a (6010 E_CAP_EXCEEDED)",
                "explorer": dp.explorer_url("tx", SIGNATURE, cluster),
            },
        },
    )


class WriteReadMixin(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = Path(tempfile.mkdtemp(prefix="tp-devnet-test-"))
        self.addCleanup(shutil.rmtree, self.directory, True)

    def written(self, record: dict) -> Path:
        path = self.directory / "devnet-artefacts.json"
        dp.write_artefact(path, record)
        return path


class TestArtefactShape(WriteReadMixin):
    def test_a_devnet_artefact_verifies_and_carries_only_the_allowed_fields(self) -> None:
        record = artefact()
        self.assertEqual(set(record), set(dp.ARTEFACT_FIELDS))
        self.assertEqual(record["cluster"], "devnet")
        loaded = chain_client.load_artefact(self.written(record))
        self.assertEqual(loaded["state"], "verified")
        self.assertEqual(loaded["signature"], MEMO_SIGNATURE)
        self.assertEqual(loaded["slot"], 679)
        self.assertEqual(loaded["blockTime"], 1_762_000_000)
        self.assertEqual(loaded["programId"], "BMrcjbC2mq99YnFKkDGJDK9x1wchDmytotuhrSkfRLWQ")
        self.assertEqual(loaded["explorer"]["transaction"], f"https://explorer.solana.com/tx/{MEMO_SIGNATURE}?cluster=devnet")

    def test_the_recommended_price_is_the_one_the_console_shows(self) -> None:
        record = artefact()
        self.assertEqual(record["recommendedLamports"], 1_380_000_000)
        self.assertEqual(record["quoteId"], "q-18f4ec73dd8d8fd1")
        self.assertEqual(record["asOf"], "2026-11-07T18:34:29.183Z")

    def test_the_artefact_carries_no_path_and_no_keypair_shape(self) -> None:
        text = json.dumps(artefact())
        self.assertNotIn(str(Path.home()), text)
        self.assertNotIn("keypair", text.lower())
        self.assertNotIn("[", text)  # the record holds no lists at all, so no key material can hide in one

    def test_an_unexpected_field_is_refused_rather_than_written(self) -> None:
        record = artefact()
        record["keypairPath"] = "/somewhere/else.json"
        with self.assertRaises(dp.PublishError):
            dp._assert_public(record)

    def test_a_record_whose_hash_does_not_recompute_is_never_written(self) -> None:
        quote = console_quote()
        quote["recommendedLamports"] = 1  # the fields move, the hash does not
        with self.assertRaises(dp.PublishError):
            artefact(quote=quote)

    def test_an_artefact_from_a_local_rehearsal_is_never_verified_as_devnet(self) -> None:
        record = artefact(cluster="localnet")
        self.assertEqual(record["cluster"], "localnet")
        self.assertIn("localnet", json.loads(json.dumps(record))["cluster"])
        self.assertIsNone(record["explorer"]["transaction"])
        self.assertIsNone(record["explorer"]["mint"])
        loaded = chain_client.load_artefact(self.written(record))
        self.assertEqual(loaded["state"], "unverified")
        self.assertEqual(loaded["reason"], "cluster_not_devnet")
        self.assertNotIn("signature", loaded)

    def test_a_record_with_no_cluster_at_all_is_not_devnet_either(self) -> None:
        record = artefact()
        del record["cluster"]
        loaded = chain_client.load_artefact(self.written(record))
        self.assertEqual(loaded["state"], "unverified")
        self.assertEqual(loaded["reason"], "cluster_not_devnet")


class TestMemoGrammar(WriteReadMixin):
    def test_the_console_memo_is_this_repository_s_grammar_byte_for_byte(self) -> None:
        quote = console_quote()
        expected = f"ticketpath:quote:{quote['quoteId']}:{quote['quoteHash']}"
        self.assertEqual(quote["memoText"], expected)
        self.assertEqual(chain_client.expected_memo(quote["quoteId"], quote["quoteHash"]), expected)
        self.assertEqual(len(quote["memoText"].encode("utf-8")), 100)

    def test_the_commitment_function_and_the_publisher_spell_it_the_same_way(self) -> None:
        quote = console_quote()
        commit = chain_client.quote_commit(
            quote_id=quote["quoteId"],
            recommendation={"eventId": quote["eventId"], "tierId": quote["tierId"], "recommendedLamports": quote["recommendedLamports"], "asOf": quote["asOf"]},
            model_version=quote["modelVersion"],
        )
        self.assertEqual(commit["memoText"], quote["memoText"])
        self.assertEqual(commit["quoteHash"], quote["quoteHash"])

    def test_a_v1_shaped_memo_is_refused_even_when_the_hash_recomputes(self) -> None:
        record = artefact()
        record["memoText"] = f"ticketpath:v1:{record['eventId']}:counterfactual:{record['asOf']}:{record['quoteHash']}"
        loaded = chain_client.load_artefact(self.written(record))
        self.assertEqual(loaded["state"], "unverified")
        self.assertEqual(loaded["reason"], "memo_grammar_mismatch")

    def test_the_v1_form_is_a_different_string_and_a_different_hash(self) -> None:
        quote = console_quote()
        v1 = f"ticketpath:v1:{quote['eventId']}:counterfactual:{quote['asOf']}:{quote['quoteHash']}"
        self.assertNotEqual(v1, quote["memoText"])


class TestConsoleSlot(WriteReadMixin):
    def payload(self, *, state: str, reason: str, cluster: str | None = None, signature: str | None = None) -> dict:
        quote = console_quote()
        return {
            "chain": {
                "state": state,
                "reason": reason,
                "checkedAt": "2026-11-07T19:00:00.000Z",
                "signature": signature,
                "slot": 679,
                "blockTime": 1_762_000_000,
                "cluster": cluster,
                "quoteId": quote["quoteId"],
                "quoteHash": quote["quoteHash"],
                "memoText": quote["memoText"],
                "programStatus": {"programId": "BMrcjbC2mq99YnFKkDGJDK9x1wchDmytotuhrSkfRLWQ"},
            }
        }

    def test_a_verified_slot_renders_the_signature_the_explorer_link_and_the_program_id(self) -> None:
        html = page.chain_slot(self.payload(state="verified", reason="ok", cluster="devnet", signature=MEMO_SIGNATURE))
        self.assertIn(MEMO_SIGNATURE, html)
        self.assertIn(f"https://explorer.solana.com/tx/{MEMO_SIGNATURE}?cluster=devnet", html)
        self.assertIn("BMrcjbC2mq99YnFKkDGJDK9x1wchDmytotuhrSkfRLWQ", html)
        self.assertIn("Recorded, not independently re-read", html)

    def test_a_local_rehearsal_renders_no_signature_and_no_link(self) -> None:
        html = page.chain_slot(self.payload(state="unverified", reason="cluster_not_devnet", cluster="localnet", signature=MEMO_SIGNATURE))
        self.assertNotIn("explorer.solana.com", html)
        self.assertNotIn(MEMO_SIGNATURE, html)
        self.assertIn("A local rehearsal was recorded and is not devnet evidence", html)

    def test_a_missing_artefact_still_renders_the_design_quote_it_would_commit(self) -> None:
        html = page.chain_slot(self.payload(state="absent", reason="devnet_absent"))
        self.assertIn("No devnet transaction has been recorded", html)
        self.assertIn("ticketpath:quote:", html)
        self.assertNotIn("explorer.solana.com", html)


class TestTransactionBytes(unittest.TestCase):
    """The message format is four fields and a list; `solana decode-transaction` is the oracle."""

    PAYER = "75UcdvvgZYVK6Z8BCs8RnNP4WBpDiTtKBEijZxdovxGy"
    MINT = "7jobXedkdwKo94PLenYcHzSB4J2QgvDihRKSTGjWahz5"
    RECORD = "CHYJMjXvTjPRdzo25QRDDEZzocvknDyWJ9mK3Fc8hxga"
    EXTRA = "4YbyqkQSGZHzq4kbLyixjWwbYvyrtZnYvwA2a1xPsfwN"
    PROGRAM = "BMrcjbC2mq99YnFKkDGJDK9x1wchDmytotuhrSkfRLWQ"
    DESTINATION = "3vNznfqesFf1J44s8zNEXHagekghbDVv2Kw9ceoeVXMU"
    BLOCKHASH = "HDizv5j63S3Kbka4Fsh7xW1GvyH5tWUL5QB94Kpaz6Xg"

    def test_the_transfer_instruction_is_the_bytes_spl_token_produced(self) -> None:
        # Measured from a landed `spl-token transfer` on a local validator: instruction 12,
        # amount 1 as a little-endian u64, decimals 0. Base58 `g7gn3dpVguJSb` is that sample.
        instruction = dp.instruction_transfer_checked(
            source="9S7pzX3zDJRYCfAeBQi11TdMMadWqMhv5Gv5rXZLu7hU",
            mint=self.MINT,
            destination=self.DESTINATION,
            authority=self.PAYER,
            record=self.RECORD,
            hook_program=self.PROGRAM,
            extra_metas=self.EXTRA,
        )
        self.assertEqual(instruction.data, base58.decode("g7gn3dpVguJSb"))
        self.assertEqual(instruction.program_id, dp.TOKEN_2022_PROGRAM)
        self.assertEqual(
            [meta.pubkey for meta in instruction.accounts],
            ["9S7pzX3zDJRYCfAeBQi11TdMMadWqMhv5Gv5rXZLu7hU", self.MINT, self.DESTINATION, self.PAYER, self.RECORD, self.PROGRAM, self.EXTRA],
        )
        self.assertEqual([meta.is_signer for meta in instruction.accounts], [False, False, False, True, False, False, False])

    def message(self) -> bytes:
        return dp.compile_message(
            self.PAYER,
            [
                dp.instruction_init_record(
                    payer=self.PAYER, mint=self.MINT, record=self.RECORD, program_id=self.PROGRAM,
                    face=dp.FACE_LAMPORTS, cap_bps=dp.CAP_BPS,
                )
            ],
            self.BLOCKHASH,
        )

    def test_the_message_header_counts_signers_and_readonly_accounts(self) -> None:
        message = self.message()
        # one signer (the payer), no readonly signers, three readonly unsigned:
        # the mint, the system program and this program
        self.assertEqual(list(message[:3]), [1, 0, 3])
        self.assertEqual(message[3], 5)  # five account keys

    def test_the_payer_is_the_first_account_key(self) -> None:
        message = self.message()
        self.assertEqual(base58.encode(message[4:36]), self.PAYER)

    def test_the_message_decodes_with_the_toolchain_when_it_is_installed(self) -> None:
        if not shutil.which("solana", path=dp.toolchain_path()):
            self.skipTest("no solana binary on PATH to decode with")
        message = self.message()
        transaction = dp.build_transaction(message, [bytes(64)])
        encoded = __import__("base64").b64encode(transaction).decode("ascii")
        completed = subprocess.run(
            [shutil.which("solana", path=dp.toolchain_path()), "decode-transaction", encoded, "base64"],
            capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn(self.PAYER, completed.stdout)
        self.assertIn(self.PROGRAM, completed.stdout)


class TestDryRun(WriteReadMixin):
    def test_a_dry_run_plans_and_writes_nothing(self) -> None:
        out = self.directory / "should-not-exist.json"
        code = dp.main(["--dry-run", "--out", str(out)])
        self.assertEqual(code, dp.EXIT_OK)
        self.assertFalse(out.exists())

    def test_dry_run_needs_no_keypair_and_no_binary(self) -> None:
        # It resolves the plan from files and fixtures alone; a missing keypair is only fatal
        # on a real run. Proven by pointing it at a path that does not exist.
        out = self.directory / "still-not-there.json"
        code = dp.main(["--dry-run", "--keypair", str(self.directory / "absent.json"), "--out", str(out)])
        self.assertEqual(code, dp.EXIT_OK)
        self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
