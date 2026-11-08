"""The publish script's public surface: the artefact, the grammar, and the bytes on the wire.

Nothing here needs a cluster, a Solana binary or a keypair. The artefact is built by a pure
function, the quote comes from the console's own code, and the two byte-level claims -- the
transaction message and the transfer instruction -- are pinned against samples measured from
the toolchain (see `tests/test_solana_sign.py` for the signer).
"""

from __future__ import annotations

import contextlib
import inspect
import io
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
# A program id that is not the frozen devnet one. The dry-run tests need a target the
# frozen-upgrade guard does not refuse, so they say so rather than relying on the tree.
NOT_FROZEN = "BMrcjbC2mq99YnFKkDGJDK9x1wchDmytotuhrSkfRLWQ"
MEMO_SIGNATURE = "2NrUUq5fkjbxeTZEmoRwceK2okpiwQ7CoFrF7Q3u9GnhR6FfYUQ2CeLqmaXkj8ESfWwqREVkwVXHaSu6JbSiiE3c"


def console_quote() -> dict:
    """The quote the console renders for the pinned instant. Pure: fixtures, no network."""
    return dp.console_quote()


def artefact(*, cluster: str = "devnet", quote: dict | None = None, memo: dict | None = None) -> dict:
    quote = quote or console_quote()
    # `memoPrograms` is what a run's `getTransaction` read-back carries. The artefact records
    # that observation and not the table's claim, so a memo dict without it records None --
    # which is why every test below that expects an id passes one.
    observed = [chain_client.memo_program_id(cluster)] if cluster in chain_client.MEMO_PROGRAMS else []
    return dp.build_artefact(
        cluster=cluster,
        rpc_url="https://api.devnet.solana.com" if cluster == "devnet" else "http://127.0.0.1:1",
        quote=quote,
        memo=memo
        or {
            "signature": MEMO_SIGNATURE,
            "slot": 679,
            "blockTime": 1_762_000_000,
            "memoPrograms": observed,
        },
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

    def test_the_artefact_records_the_memo_program_the_run_read_back(self) -> None:
        self.assertEqual(artefact()["memoProgram"], chain_client.MEMO_PROGRAM_DEVNET)
        self.assertEqual(artefact(cluster="localnet")["memoProgram"], chain_client.memo_program_id("localnet"))
        # The claim and the observation are separate facts: a run that read a different id
        # records the different id, and the assertion that caught it ran before this record
        # was built.
        other = {"signature": MEMO_SIGNATURE, "slot": 679, "blockTime": 1_762_000_000,
                 "memoPrograms": [chain_client.MEMO_PROGRAM_CLI]}
        self.assertEqual(artefact(memo=other)["memoProgram"], chain_client.MEMO_PROGRAM_CLI)

    def test_an_artefact_built_without_a_read_back_records_no_memo_program(self) -> None:
        bare = {"signature": MEMO_SIGNATURE, "slot": 679, "blockTime": 1_762_000_000}
        self.assertIsNone(artefact(memo=bare)["memoProgram"])

    def test_the_recorded_memo_program_survives_the_write_and_verifies(self) -> None:
        loaded = chain_client.load_artefact(self.written(artefact()))
        self.assertEqual(loaded["state"], "verified")
        self.assertEqual(loaded["memoProgram"], chain_client.MEMO_PROGRAM_DEVNET)

    def test_a_record_written_before_the_field_existed_still_verifies(self) -> None:
        # records/devnet-artefacts.json is the proven record and is not rewritten by hand, so
        # the field has to be an addition the checker tolerates and not one it requires.
        record = artefact()
        del record["memoProgram"]
        loaded = chain_client.load_artefact(self.written(record))
        self.assertEqual(loaded["state"], "verified")
        self.assertEqual(loaded["signature"], MEMO_SIGNATURE)
        self.assertIsNone(loaded["memoProgram"])


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
    """The slot renders the payload the orchestrator builds, not a hand-shaped one.

    The recorded block is the file's, so this test serves the file's own block: it loads a
    publisher artefact into `chain.recorded` and asserts what a reader sees. A hand-written
    signature block would pass while the real payload drifted.
    """

    def payload(self, *, state: str, reason: str, cluster: str = "devnet") -> dict:
        from ticketpath.api import guidance

        quote = console_quote()
        chain = {
            "state": state,
            "reason": reason,
            # The cluster the refusal is about, and the path the server read: the page names
            # both (feature 2 review).
            "reasonCluster": cluster,
            "source": "records/devnet-artefacts.json",
            "signaturesRecorded": None,
            "recorded": None,
            "matchesCurrentQuote": None,
            "quoteId": quote["quoteId"],
            "quoteHash": quote["quoteHash"],
            "memoText": quote["memoText"],
            "programStatus": {
                "programDeployed": False,
                "askedCluster": False,
                "programId": None,
                "designDoc": "docs/ON-CHAIN-DESIGN.md",
                "recorded": None,
            },
        }
        if state == "verified":
            loaded = chain_client.load_artefact(self.written(artefact(cluster=cluster)))
            self.assertEqual(loaded["state"], "verified", loaded)
            recorded = dict(loaded)
            recorded.pop("state", None)
            for name in ("recommendedLamports", "slot", "blockTime"):
                if recorded.get(name) is not None:
                    recorded[name] = guidance.num(recorded[name], "DEVNET", "recorded", "A_CHAIN_RECORDED")
            recorded["transfers"] = {
                leg: {
                    key: (
                        guidance.num(value, "DEVNET", "recorded", "A_CHAIN_RECORDED")
                        if isinstance(value, int) and not isinstance(value, bool)
                        else value
                    )
                    for key, value in row.items()
                }
                for leg, row in (recorded.get("transfers") or {}).items()
            }
            chain["recorded"] = recorded
            chain["matchesCurrentQuote"] = recorded["quoteHash"] == quote["quoteHash"]
            chain["programStatus"]["recorded"] = {
                "programId": recorded.get("programId"),
                "cluster": recorded.get("cluster"),
                "source": "records/devnet-artefacts.json",
            }
        return {"chain": chain}

    def test_a_verified_slot_renders_the_signature_the_explorer_link_and_the_program_id(self) -> None:
        html = page.chain_slot(self.payload(state="verified", reason=""))
        self.assertIn(MEMO_SIGNATURE, html)
        self.assertIn(f"https://explorer.solana.com/tx/{MEMO_SIGNATURE}?cluster=devnet", html)
        self.assertIn("BMrcjbC2mq99YnFKkDGJDK9x1wchDmytotuhrSkfRLWQ", html)
        self.assertIn("Recorded, not independently re-read", html)

    def test_a_local_rehearsal_renders_no_signature_and_no_link(self) -> None:
        html = page.chain_slot(
            self.payload(state="unverified", reason="cluster_not_devnet", cluster="localnet")
        )
        self.assertNotIn("explorer.solana.com", html)
        self.assertNotIn(MEMO_SIGNATURE, html)
        self.assertIn("A local rehearsal was recorded and is not devnet evidence", html)

    def test_a_missing_artefact_still_renders_the_design_quote_it_would_commit(self) -> None:
        html = page.chain_slot(self.payload(state="absent", reason="devnet_absent"))
        self.assertIn("No devnet transaction is recorded in the console", html)
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


class TestResumeFile(WriteReadMixin):
    """The file that makes a rerun a resume. Its whole job is to be written early and trusted late."""

    def progress(self, *, cluster: str = "localnet", writable: bool = True) -> dp.Progress:
        return dp.Progress(self.directory / "devnet-progress.local.json", cluster=cluster, writable=writable)

    def test_a_finished_step_is_on_disk_before_the_next_one_starts(self) -> None:
        progress = self.progress()
        progress.put("mint", "7jobXedkdwKo94PLenYcHzSB4J2QgvDihRKSTGjWahz5")
        on_disk = json.loads(progress.path.read_text(encoding="utf-8"))
        self.assertEqual(on_disk["mint"], "7jobXedkdwKo94PLenYcHzSB4J2QgvDihRKSTGjWahz5")
        self.assertEqual(on_disk["cluster"], "localnet")
        self.assertEqual(on_disk["version"], dp.PROGRESS_VERSION)
        self.assertEqual(dict(dp.Progress(progress.path, cluster="localnet").load().state), on_disk)

    def test_the_file_is_private_and_leaves_no_temporary_copy(self) -> None:
        progress = self.progress()
        progress.put("mint", "7jobXedkdwKo94PLenYcHzSB4J2QgvDihRKSTGjWahz5")
        self.assertEqual(progress.path.stat().st_mode & 0o777, 0o600)
        leftovers = [p.name for p in self.directory.iterdir() if p.name not in {progress.path.name}]
        self.assertEqual(leftovers, [])

    def test_a_path_never_enters_the_file(self) -> None:
        progress = self.progress()
        with self.assertRaises(dp.PublishError):
            progress.put("mint", "/somewhere/a/keypair.json")
        self.assertFalse(progress.path.exists())

    def test_a_key_handle_never_enters_the_file(self) -> None:
        progress = self.progress()
        with self.assertRaises(dp.PublishError):
            progress.put("memo", {"signature": "mint-keypair.json"})
        self.assertFalse(progress.path.exists())

    def test_a_field_the_loader_does_not_know_is_refused(self) -> None:
        progress = self.progress()
        with self.assertRaises(dp.PublishError):
            progress.put("keypairPath", "elsewhere")
        self.assertFalse(progress.path.exists())

    def test_a_file_from_the_other_cluster_is_not_reused(self) -> None:
        self.progress(cluster="localnet").put("mint", "7jobXedkdwKo94PLenYcHzSB4J2QgvDihRKSTGjWahz5")
        with self.assertRaises(dp.PublishError) as caught:
            dp.Progress(self.progress().path, cluster="devnet").load()
        self.assertIn("localnet", str(caught.exception))

    def test_an_unreadable_file_says_so_instead_of_starting_over(self) -> None:
        path = self.directory / "devnet-progress.json"
        path.write_text("{not json", encoding="utf-8")
        with self.assertRaises(dp.PublishError):
            dp.Progress(path, cluster="devnet").load()

    def test_a_dry_run_reads_the_file_and_never_writes_it(self) -> None:
        progress = self.progress(writable=False)
        progress.put("mint", "7jobXedkdwKo94PLenYcHzSB4J2QgvDihRKSTGjWahz5")
        self.assertFalse(progress.path.exists())

    def test_the_two_legs_and_a_pending_signature_round_trip(self) -> None:
        progress = self.progress()
        progress.put_pending(
            "acceptedAtCap", signature=SIGNATURE, blockhash="HDizv5j63S3Kbka4Fsh7xW1GvyH5tWUL5QB94Kpaz6Xg"
        )
        self.assertEqual(progress.pending("acceptedAtCap")["signature"], SIGNATURE)
        progress.put_leg(
            "acceptedAtCap",
            {"signature": SIGNATURE, "slot": 1, "blockTime": 2, "priceLamports": dp.ACCEPTED_PRICE_LAMPORTS, "error": None, "explorer": None},
        )
        progress.clear_pending("acceptedAtCap")
        reloaded = dp.Progress(progress.path, cluster="localnet").load()
        self.assertIsNone(reloaded.pending("acceptedAtCap"))
        self.assertEqual(reloaded.leg("acceptedAtCap")["priceLamports"], dp.ACCEPTED_PRICE_LAMPORTS)
        self.assertIsNone(reloaded.leg("refusedOverCap"))


class TestMemoProgramAtRunTime(WriteReadMixin):
    """The run reads the program id off the transaction it sent, and the table has to agree.

    The RPC answer is faked here, so no cluster is asked anything: the point is that the check
    exists in the code path and that it fails on a mismatch instead of printing the table.

    Every case below is written against a pair -- (memo text, program id) -- and not against
    two lists. The previous version compared the table's id with "the program of every
    instruction whose data decodes as a string", which the System program satisfies, so a
    transaction carrying our memo under the right program *and* a second memo under the wrong
    one passed whichever cluster was named. `decoys` is that transaction.
    """

    def landed(
        self,
        *,
        program_id: str,
        memo: str,
        slot: int = 679,
        decoys: tuple[tuple[str, str], ...] = (),
    ) -> dict:
        """A getTransaction answer shaped exactly like devnet's json encoding.

        `decoys` are (program id, text) pairs for other memo-shaped instructions in the same
        transaction, which is how a reader that matches on "some text in this transaction"
        gets fooled.
        """
        keys = ["payer", dp.SYSTEM_PROGRAM, program_id]
        instructions = [
            {"programIdIndex": 1, "accounts": [0, 2], "data": ""},
            {"programIdIndex": 2, "accounts": [], "data": base58.encode(memo.encode("utf-8"))},
        ]
        for decoy_program, decoy_text in decoys:
            keys.append(decoy_program)
            instructions.append(
                {"programIdIndex": len(keys) - 1, "accounts": [], "data": base58.encode(decoy_text.encode("utf-8"))}
            )
        return {
            "slot": slot,
            "blockTime": 1_762_000_000,
            "transaction": {"message": {"accountKeys": keys, "instructions": instructions}},
            "meta": {"err": None, "fee": 5000, "logMessages": []},
        }

    def context(self, *, cluster: str = "devnet", memo_recorded: bool = True):
        progress = dp.Progress(self.directory / "progress.json", cluster=cluster, writable=True)
        quote = console_quote()
        if memo_recorded:
            progress.put("memo", {"signature": MEMO_SIGNATURE, "slot": 679, "quoteHash": quote["quoteHash"]})
        ctx = dp.Context(
            cluster=cluster,
            rpc_url="http://127.0.0.1:1",
            keypair=self.directory / "authority.json",
            buyer_keypair=self.directory / "buyer.json",
            out=self.directory / "artefact.json",
            progress=progress,
        )
        return ctx, quote

    def test_a_memo_that_landed_under_another_program_stops_the_run_naming_both_ids(self) -> None:
        ctx, quote = self.context(cluster="devnet")
        answer = self.landed(program_id=chain_client.MEMO_PROGRAM_CLI, memo=quote["memoText"])
        with _SetAttr(dp, "rpc", lambda *a, **k: answer):
            with self.assertRaises(dp.PublishError) as caught:
                dp.step_memo(ctx, quote, "buyer")
        message = str(caught.exception)
        self.assertIn(chain_client.MEMO_PROGRAM_CLI, message)
        self.assertIn(chain_client.MEMO_PROGRAM_DEVNET, message)
        self.assertIn("devnet", message)

    def test_a_memo_that_landed_under_the_table_s_id_is_accepted_and_read_back(self) -> None:
        ctx, quote = self.context(cluster="devnet")
        answer = self.landed(program_id=chain_client.MEMO_PROGRAM_DEVNET, memo=quote["memoText"])
        with _SetAttr(dp, "rpc", lambda *a, **k: answer):
            details = dp.step_memo(ctx, quote, "buyer")
        self.assertEqual(details["memoPrograms"], [chain_client.MEMO_PROGRAM_DEVNET])
        self.assertEqual(details["signature"], MEMO_SIGNATURE)

    def test_a_second_memo_under_another_program_does_not_save_a_wrong_one(self) -> None:
        """The bypass the previous reader allowed: our memo under A, a decoy under B.

        Matching on "the text is in this transaction" cannot tell these apart, so this case
        passes only when the reader asserts on the pair whose text *equals* our memo. Delete
        the text-match clause in `_programs_for` and this test goes red.
        """
        ctx, quote = self.context(cluster="devnet")
        answer = self.landed(
            program_id=chain_client.MEMO_PROGRAM_CLI,
            memo=quote["memoText"],
            decoys=((chain_client.MEMO_PROGRAM_DEVNET, "an unrelated memo that also decodes"),),
        )
        with _SetAttr(dp, "rpc", lambda *a, **k: answer):
            with self.assertRaises(dp.PublishError) as caught:
                dp.step_memo(ctx, quote, "buyer")
        message = str(caught.exception)
        self.assertIn(chain_client.MEMO_PROGRAM_CLI, message)
        self.assertNotIn(chain_client.MEMO_PROGRAM_DEVNET, message.split("landed under")[1].split(",")[0])

    def test_a_decoy_memo_does_not_enter_the_recorded_program_list(self) -> None:
        # The measured devnet transaction reports the System program as a "memo program" when
        # the whole list is passed through. The artefact must carry the one id that carried
        # the quote, so a decoy in the same transaction must not appear beside it.
        ctx, quote = self.context(cluster="devnet")
        answer = self.landed(
            program_id=chain_client.MEMO_PROGRAM_DEVNET,
            memo=quote["memoText"],
            decoys=((chain_client.MEMO_PROGRAM_CLI, "a decoy memo"),),
        )
        with _SetAttr(dp, "rpc", lambda *a, **k: answer):
            details = dp.step_memo(ctx, quote, "buyer")
        self.assertEqual(details["memoPrograms"], [chain_client.MEMO_PROGRAM_DEVNET])

    def test_localnet_is_held_to_the_id_the_cli_writes(self) -> None:
        """A local rehearsal names the id measured for the CLI, and refuses the v3 one."""
        ctx, quote = self.context(cluster="localnet")
        accepted = self.landed(program_id=chain_client.MEMO_PROGRAM_DEVNET, memo=quote["memoText"])
        with _SetAttr(dp, "rpc", lambda *a, **k: accepted):
            details = dp.step_memo(ctx, quote, "buyer")
        self.assertEqual(details["memoPrograms"], [chain_client.MEMO_PROGRAM_DEVNET])

        refused = self.landed(program_id=chain_client.MEMO_PROGRAM_CLI, memo=quote["memoText"])
        with _SetAttr(dp, "rpc", lambda *a, **k: refused):
            with self.assertRaises(dp.PublishError) as caught:
                dp.step_memo(ctx, quote, "buyer")
        self.assertIn("localnet", str(caught.exception))

    def fresh_cli(self, signature: str):
        """The two fakes the send path needs: the CLI's output and the confirmation."""

        def solana(*_args, **_kwargs):
            return f"Signature: {signature}\n"

        def confirm(*_args, **_kwargs):
            return {"ok": True, "err": None}

        return solana, confirm

    def test_the_fresh_send_path_is_held_to_the_same_check(self) -> None:
        """Empty resume file, so the send path runs, and the landed id is the wrong one."""
        ctx, quote = self.context(cluster="devnet", memo_recorded=False)
        solana, confirm = self.fresh_cli(MEMO_SIGNATURE)
        answer = self.landed(program_id=chain_client.MEMO_PROGRAM_CLI, memo=quote["memoText"])
        with _SetAttr(dp, "solana", solana), _SetAttr(dp, "confirm", confirm), _SetAttr(dp, "rpc", lambda *a, **k: answer):
            with self.assertRaises(dp.PublishError) as caught:
                dp.step_memo(ctx, quote, "buyer")
        message = str(caught.exception)
        self.assertIn(chain_client.MEMO_PROGRAM_CLI, message)
        self.assertIn(chain_client.MEMO_PROGRAM_DEVNET, message)

    def test_the_fresh_send_path_accepts_the_id_the_table_names(self) -> None:
        ctx, quote = self.context(cluster="devnet", memo_recorded=False)
        solana, confirm = self.fresh_cli(MEMO_SIGNATURE)
        answer = self.landed(program_id=chain_client.MEMO_PROGRAM_DEVNET, memo=quote["memoText"])
        with _SetAttr(dp, "solana", solana), _SetAttr(dp, "confirm", confirm), _SetAttr(dp, "rpc", lambda *a, **k: answer):
            details = dp.step_memo(ctx, quote, "buyer")
        self.assertEqual(details["memoPrograms"], [chain_client.MEMO_PROGRAM_DEVNET])
        self.assertEqual(details["signature"], MEMO_SIGNATURE)
        self.assertEqual(ctx.recorded("memo")["signature"], MEMO_SIGNATURE)

    def test_the_measured_devnet_answer_reads_back_as_the_devnet_id(self) -> None:
        # The shape the reader is written against, taken from the cluster on 2026-11-08: the
        # memo instruction is instruction 1 and its programIdIndex is 3 of that message, and
        # instruction 0 is the System transfer whose data also decodes as UTF-8.
        quote = console_quote()
        answer = {
            "slot": 519_845_921,
            "blockTime": 1_794_099_003,
            "transaction": {
                "message": {
                    "accountKeys": [
                        "75UcdvvgZYVK6Z8BCs8RnNP4WBpDiTtKBEijZxdovxGy",
                        "2k1PvrHrue11in9kmwV9gjhLtFMVM8ndHSFiscV79GVd",
                        dp.SYSTEM_PROGRAM,
                        chain_client.MEMO_PROGRAM_DEVNET,
                    ],
                    "instructions": [
                        {"programIdIndex": 2, "accounts": [0, 1], "data": "3Bxs3zzLZLuLQEYX"},
                        {"programIdIndex": 3, "accounts": [], "data": base58.encode(quote["memoText"].encode("utf-8"))},
                    ],
                }
            },
            "meta": {"err": None, "fee": 5000, "logMessages": []},
        }
        details = dp._summarise_transaction(answer, "signature", memo=quote["memoText"])
        self.assertIn(quote["memoText"], details["memos"])
        self.assertEqual(details["memoPrograms"], [chain_client.MEMO_PROGRAM_DEVNET])
        self.assertEqual(
            dp.assert_memo_program(details, "devnet", memo=quote["memoText"]), chain_client.MEMO_PROGRAM_DEVNET
        )
        # The System instruction is in the pairs, and is not what `memoPrograms` answers.
        self.assertTrue(any(program == dp.SYSTEM_PROGRAM for _, program in details["memoInstructions"]))
        self.assertNotIn(dp.SYSTEM_PROGRAM, details["memoPrograms"])

    def test_a_log_only_memo_is_credited_to_the_program_that_logged_it(self) -> None:
        """The two-line shape, measured under Memo4c2p, with no instruction data to read."""
        quote = console_quote()
        answer = {
            "slot": 1,
            "blockTime": 2,
            "transaction": {"message": {"accountKeys": ["payer"], "instructions": []}},
            "meta": {
                "err": None,
                "fee": 5000,
                "logMessages": [
                    f"Program {chain_client.MEMO_PROGRAM_DEVNET} invoke [1]",
                    f"Program log: Memo (len {len(quote['memoText'].encode('utf-8'))})",
                    f"Program log: {quote['memoText']}",
                    f"Program {chain_client.MEMO_PROGRAM_DEVNET} success",
                ],
            },
        }
        details = dp._summarise_transaction(answer, "signature", memo=quote["memoText"])
        self.assertEqual(details["memoPrograms"], [chain_client.MEMO_PROGRAM_DEVNET])

    def test_the_one_line_log_shape_keeps_its_program_too(self) -> None:
        quote = console_quote()
        answer = {
            "slot": 1,
            "blockTime": 2,
            "transaction": {"message": {"accountKeys": ["payer"], "instructions": []}},
            "meta": {
                "err": None,
                "fee": 5000,
                "logMessages": [
                    f"Program {chain_client.MEMO_PROGRAM_CLI} invoke [1]",
                    f'Program log: Memo (len {len(quote["memoText"])}): "{quote["memoText"]}"',
                    f"Program {chain_client.MEMO_PROGRAM_CLI} success",
                ],
            },
        }
        details = dp._summarise_transaction(answer, "signature", memo=quote["memoText"])
        self.assertEqual(details["memoPrograms"], [chain_client.MEMO_PROGRAM_CLI])


class TestRetries(unittest.TestCase):
    """A 502 must not cost a mint. `urlopen` is faked, so these run with no cluster and no clock."""

    def setUp(self) -> None:
        self.original = dp.urlrequest.urlopen
        self.calls = 0
        self.waits: list[float] = []
        self.original_sleep = dp.time.sleep
        dp.time.sleep = self.waits.append  # type: ignore[assignment]
        self.addCleanup(setattr, dp.urlrequest, "urlopen", self.original)
        self.addCleanup(setattr, dp.time, "sleep", self.original_sleep)
        dp.FAULTS.after.clear()
        dp.FAULTS.rpc.clear()
        self.addCleanup(dp.FAULTS.after.clear)
        self.addCleanup(dp.FAULTS.rpc.clear)

    def fake(self, *failures: Exception):
        """A transport that raises each failure in turn, then answers with `result`."""

        class Response:
            def __init__(self, payload: bytes):
                self.payload = payload

            def read(self) -> bytes:
                return self.payload

            def __enter__(self):
                return self

            def __exit__(self, *rest) -> None:
                return None

        pending = list(failures)

        def urlopen(_call, timeout=None):  # noqa: ANN001, ARG001 - shaped like the real one
            self.calls += 1
            if pending:
                raise pending.pop(0)
            return Response(json.dumps({"jsonrpc": "2.0", "id": 1, "result": "ok"}).encode("utf-8"))

        dp.urlrequest.urlopen = urlopen  # type: ignore[assignment]

    @staticmethod
    def http(code: int) -> Exception:
        return dp.urlrequest.HTTPError("https://api.devnet.solana.com", code, "injected", None, None)

    def test_a_transient_http_error_is_retried_and_the_call_still_answers(self) -> None:
        self.fake(self.http(502))
        self.assertEqual(dp.rpc("https://api.devnet.solana.com", "getSignatureStatuses", [[]]), "ok")
        self.assertEqual(self.calls, 2)
        self.assertEqual(self.waits, [dp.RPC_BACKOFF_BASE])

    def test_the_backoff_grows_and_stays_bounded(self) -> None:
        self.fake(*[self.http(503) for _ in range(dp.RPC_ATTEMPTS - 1)])
        self.assertEqual(dp.rpc("https://api.devnet.solana.com", "getHealth", []), "ok")
        self.assertEqual(self.waits, [0.5, 1.0, 2.0])
        self.assertTrue(all(wait <= dp.RPC_BACKOFF_CAP for wait in self.waits))

    def test_giving_up_is_one_sentence_that_says_how_many_attempts(self) -> None:
        self.fake(*[self.http(502) for _ in range(dp.RPC_ATTEMPTS)])
        with self.assertRaises(dp.PublishError) as caught:
            dp.rpc("https://api.devnet.solana.com", "getSignatureStatuses", [[]])
        message = str(caught.exception)
        self.assertIn("getSignatureStatuses", message)
        self.assertIn(f"after {dp.RPC_ATTEMPTS} attempts", message)
        self.assertIn("HTTPError 502", message)
        self.assertEqual(self.calls, dp.RPC_ATTEMPTS)

    def test_a_rejected_request_is_not_retried(self) -> None:
        self.fake(self.http(400))
        with self.assertRaises(dp.PublishError):
            dp.rpc("https://api.devnet.solana.com", "getAccountInfo", ["x"])
        self.assertEqual(self.calls, 1)

    def test_a_timeout_is_transient_and_a_slow_call_recovers(self) -> None:
        self.fake(TimeoutError("read timed out"))
        self.assertEqual(dp.rpc("https://api.devnet.solana.com", "getHealth", []), "ok")
        self.assertEqual(self.calls, 2)

    def test_a_jsonrpc_error_that_is_not_transient_is_reported_at_once(self) -> None:
        class Response:
            def read(self) -> bytes:
                return json.dumps({"jsonrpc": "2.0", "id": 1, "error": {"message": "Invalid param"}}).encode("utf-8")

            def __enter__(self):
                return self

            def __exit__(self, *rest) -> None:
                return None

        dp.urlrequest.urlopen = lambda *a, **k: Response()  # type: ignore[assignment]
        with self.assertRaises(dp.PublishError) as caught:
            dp.rpc("https://api.devnet.solana.com", "getAccountInfo", ["x"])
        self.assertIn("Invalid param", str(caught.exception))

    def test_the_injected_fault_is_the_same_class_of_failure_the_terminal_run_saw(self) -> None:
        dp.FAULTS.arm(["rpc:getSignatureStatuses:1"])
        self.fake()
        self.assertEqual(dp.rpc("http://127.0.0.1:1", "getSignatureStatuses", [[]]), "ok")
        self.assertEqual(self.calls, 1)
        self.assertEqual(len(self.waits), 1)


def fake_rpc(monkeypatch, answers: dict):
    """Replace `dp.rpc` with a table: method -> list of answers to hand out in order.

    An answer list whose last entry is `REPEAT` keeps answering with it, which is how a test
    says "and it kept saying the same thing" without writing a loop.
    """
    patched = dict(answers)
    monkeypatch.setattr(dp, "rpc", _table(patched))


REPEAT = object()


def _table(answers: dict):
    def rpc(_url, method, _params, **_kwargs):
        queue = answers.get(method)
        if not queue:
            raise AssertionError(f"unexpected rpc call {method}")
        if len(queue) > 1 and queue[1] is REPEAT:
            answer = queue[0]
        else:
            answer = queue.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    return rpc


class TestRecoverSignature(unittest.TestCase):
    """"Did it land?" is the question that decides whether a resend moves a second ticket."""

    def setUp(self) -> None:
        self.original_sleep = dp.time.sleep
        dp.time.sleep = lambda _seconds: None  # type: ignore[assignment]
        self.addCleanup(setattr, dp.time, "sleep", self.original_sleep)

    def patch(self, answers: dict) -> None:
        self.original_rpc = dp.rpc
        dp.rpc = _table(dict(answers))  # type: ignore[assignment]
        self.addCleanup(setattr, dp, "rpc", self.original_rpc)

    def test_a_landed_signature_is_reported_as_landed(self) -> None:
        self.patch({"getSignatureStatuses": [{"value": [{"slot": 679, "err": None, "confirmationStatus": "confirmed"}]}]})
        result = dp.recover_signature("http://127.0.0.1:1", SIGNATURE, blockhash="x")
        self.assertEqual(result["state"], "landed")
        self.assertTrue(result["ok"])
        self.assertEqual(result["slot"], 679)

    def test_a_failed_transaction_is_landed_and_says_what_failed(self) -> None:
        self.patch({"getSignatureStatuses": [{"value": [{"slot": 7, "err": {"InstructionError": [0, {"Custom": 6010}]}, "confirmationStatus": "confirmed"}]}]})
        result = dp.recover_signature("http://127.0.0.1:1", SIGNATURE, blockhash="x")
        self.assertEqual(result["state"], "landed")
        self.assertFalse(result["ok"])

    def test_invisible_and_a_dead_blockhash_is_the_only_case_that_may_be_resent(self) -> None:
        self.patch(
            {
                "getSignatureStatuses": [{"value": [None]}, {"value": [None]}],
                "isBlockhashValid": [{"value": False}],
            }
        )
        self.assertEqual(dp.recover_signature("http://127.0.0.1:1", SIGNATURE, blockhash="x", timeout=30)["state"], "dropped")

    def test_invisible_with_a_live_blockhash_stops_the_run_instead_of_resending(self) -> None:
        self.patch(
            {
                "getSignatureStatuses": [{"value": [None]}, REPEAT],
                "isBlockhashValid": [{"value": True}, REPEAT],
            }
        )
        with self.assertRaises(dp.PublishError) as caught:
            dp.recover_signature("http://127.0.0.1:1", SIGNATURE, blockhash="x", timeout=0.4)
        self.assertIn("will not resend", str(caught.exception))

    def test_a_status_read_that_keeps_failing_is_not_read_as_absence(self) -> None:
        self.patch({"getSignatureStatuses": [dp.PublishError("502"), REPEAT]})
        with self.assertRaises(dp.PublishError) as caught:
            dp.recover_signature("http://127.0.0.1:1", SIGNATURE, blockhash=None, timeout=0.4)
        self.assertIn("not visible", str(caught.exception))


class TestSettledCli(unittest.TestCase):
    """The CLI lags the RPC by about a second; a "not found" is a "not yet", and nothing else is."""

    def setUp(self) -> None:
        self.original_sleep = dp.time.sleep
        dp.time.sleep = lambda _s: None  # type: ignore[assignment]
        self.addCleanup(setattr, dp.time, "sleep", self.original_sleep)

    def test_a_not_found_is_retried_until_the_cli_sees_the_account(self) -> None:
        calls = []

        def flaky():
            calls.append(1)
            if len(calls) < 3:
                raise dp.PublishError('spl-token mint failed (rc 1):\nError: "Account X not found"')
            return "ok"

        self.assertEqual(dp.settled(flaky, what="spl-token mint"), "ok")
        self.assertEqual(len(calls), 3)

    def test_four_looks_and_then_the_failure_is_reported(self) -> None:
        calls = []

        def never():
            calls.append(1)
            raise dp.PublishError("Error: Could not find token account X")

        with self.assertRaises(dp.PublishError):
            dp.settled(never, what="spl-token balance")
        self.assertEqual(len(calls), 3)

    def test_any_other_failure_is_raised_at_once(self) -> None:
        calls = []

        def wrong():
            calls.append(1)
            raise dp.PublishError("spl-token mint failed (rc 1): custom program error: 0x0")

        with self.assertRaises(dp.PublishError):
            dp.settled(wrong, what="spl-token mint")
        self.assertEqual(len(calls), 1)


class TestResumeBehaviour(WriteReadMixin):
    """The decisions a rerun makes, without a cluster: reuse, never repeat."""

    def context(self, *, progress: dp.Progress | None = None) -> dp.Context:
        return dp.Context(
            cluster="localnet",
            rpc_url="http://127.0.0.1:1",
            keypair=self.directory / "authority.json",
            buyer_keypair=self.directory / "buyer.json",
            out=self.directory / "devnet-artefacts.local.json",
            progress=progress,
        )

    def progress(self, state: dict | None = None) -> dp.Progress:
        progress = dp.Progress(self.directory / "devnet-progress.local.json", cluster="localnet")
        progress.state = dict(state or {})
        return progress

    def test_a_recorded_mint_is_reused_and_nothing_is_created(self) -> None:
        mint = "7jobXedkdwKo94PLenYcHzSB4J2QgvDihRKSTGjWahz5"
        ctx = self.context(progress=self.progress({"mint": mint, "mintMetadata": True}))
        seen: list[str] = []
        self.enterContext(self.patch_account_exists(seen, mint, True))
        self.enterContext(self.patch_run_forbidden())
        self.assertEqual(dp.step_mint(ctx, "BMrcjbC2mq99YnFKkDGJDK9x1wchDmytotuhrSkfRLWQ"), mint)
        self.assertEqual(seen, [mint])

    def test_a_mint_recorded_before_its_metadata_gets_its_metadata_on_the_rerun(self) -> None:
        mint = "7jobXedkdwKo94PLenYcHzSB4J2QgvDihRKSTGjWahz5"
        ctx = self.context(progress=self.progress({"mint": mint}))
        self.enterContext(self.patch_account_exists([], mint, True))
        self.enterContext(self.patch_run_forbidden())
        original = dp.mint_metadata_on_chain
        dp.mint_metadata_on_chain = lambda *_a, **_k: True  # type: ignore[assignment]
        self.addCleanup(setattr, dp, "mint_metadata_on_chain", original)
        self.assertEqual(dp.step_mint(ctx, "BMrcjbC2mq99YnFKkDGJDK9x1wchDmytotuhrSkfRLWQ"), mint)
        self.assertIs(ctx.recorded("mintMetadata"), True)

    def test_the_mint_address_is_on_disk_before_the_transaction_that_creates_it(self) -> None:
        # The regression that cost a duplicate mint: the address existed only in the process.
        ctx = self.context(progress=self.progress())
        mint = "7jobXedkdwKo94PLenYcHzSB4J2QgvDihRKSTGjWahz5"
        keypair = self.directory / "mint-keypair.json"
        seen: list[str | None] = []

        def fake_run(command, **_kwargs):
            if "new" in command:
                keypair.write_text("[0]", encoding="utf-8")  # the shape does not matter: it is not read here
                return ""
            if "create-token" in command:
                seen.append(ctx.recorded("mint"))  # read the file *while* the CLI is running
                return f"Creating token {mint} under program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
            if "initialize-metadata" in command:
                return "Signature: 4vJ9JU1bJJE96FWSJKvHsmmFADCg4gpZQff4P3bkLKi\n"
            raise AssertionError(f"unexpected command {command}")

        ctx.mint_keypair_path = keypair
        original_run = dp.run
        original_keypair_pubkey = dp.keypair_pubkey
        original_metadata = dp.mint_metadata_on_chain
        dp.run = fake_run  # type: ignore[assignment]
        dp.keypair_pubkey = lambda *_a, **_k: mint  # type: ignore[assignment]
        dp.mint_metadata_on_chain = lambda *_a, **_k: False  # type: ignore[assignment]
        self.enterContext(self.patch_account_exists([], mint, False))
        self.addCleanup(setattr, dp, "run", original_run)
        self.addCleanup(setattr, dp, "keypair_pubkey", original_keypair_pubkey)
        self.addCleanup(setattr, dp, "mint_metadata_on_chain", original_metadata)
        self.assertEqual(dp.step_mint(ctx, "BMrcjbC2mq99YnFKkDGJDK9x1wchDmytotuhrSkfRLWQ"), mint)
        self.assertEqual(seen, [mint])

    def test_no_third_ticket_is_minted_after_the_pair_has_moved_one(self) -> None:
        # The seller alone holds one after the at-cap transfer; asking the seller alone would
        # mint a third ticket on every rerun and break the pair's own arithmetic.
        ctx = self.context(progress=self.progress())
        balances = {"seller": 1, "buyer": 1}
        original = dp.token_balance
        original_run = dp.run
        dp.token_balance = lambda _ctx, address: balances["seller"] if address == "seller" else balances["buyer"]  # type: ignore[assignment]
        dp.run = lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("nothing should be minted"))  # type: ignore[assignment]
        self.addCleanup(setattr, dp, "token_balance", original)
        self.addCleanup(setattr, dp, "run", original_run)
        dp.step_ticket(ctx, "mint", "seller", "buyer")
        self.assertEqual(ctx.recorded("ticketsMinted"), 2)

    def test_a_different_buyer_is_refused_rather_than_mixed_into_the_record(self) -> None:
        ctx = self.context(progress=self.progress({"buyerAta": "B" * 44}))
        with self.assertRaises(dp.PublishError) as caught:
            ctx.record_accounts(authority_ata="A" * 44, buyer="C" * 44, buyer_ata="C" * 44)
        self.assertIn("restart", str(caught.exception).lower())

    def test_an_artefact_for_this_cluster_is_taken_into_the_resume_file(self) -> None:
        # `--restart`, or a resume file someone deleted, must not turn a finished run into one
        # that resends its transfers.
        record = artefact(cluster="localnet")
        dp.write_artefact(self.directory / "devnet-artefacts.local.json", record)
        ctx = self.context(progress=self.progress())
        dp.seed_from_artefact(ctx)
        self.assertEqual(ctx.recorded("mint"), record["mint"])
        self.assertIs(ctx.recorded("mintMetadata"), True)
        self.assertEqual(ctx.recorded("transfers")["acceptedAtCap"]["signature"], record["transfers"]["acceptedAtCap"]["signature"])
        self.assertEqual(ctx.recorded("memo")["quoteHash"], record["quoteHash"])

    def test_an_artefact_from_another_cluster_is_not_taken(self) -> None:
        dp.write_artefact(self.directory / "devnet-artefacts.local.json", artefact(cluster="devnet"))
        ctx = self.context(progress=self.progress())
        dp.seed_from_artefact(ctx)
        self.assertIsNone(ctx.recorded("mint"))
        self.assertIsNone(ctx.recorded("transfers"))

    def test_an_attempted_metadata_twice_is_harmless_when_the_chain_already_has_it(self) -> None:
        ctx = self.context(progress=self.progress({"mint": "7jobXedkdwKo94PLenYcHzSB4J2QgvDihRKSTGjWahz5"}))
        original_run = dp.run
        original_metadata = dp.mint_metadata_on_chain
        dp.run = lambda *_a, **_k: (_ for _ in ()).throw(dp.PublishError("metadata already initialised"))  # type: ignore[assignment]
        dp.mint_metadata_on_chain = lambda *_a, **_k: True  # type: ignore[assignment]
        self.addCleanup(setattr, dp, "run", original_run)
        self.addCleanup(setattr, dp, "mint_metadata_on_chain", original_metadata)
        dp.ensure_mint_metadata(ctx, "7jobXedkdwKo94PLenYcHzSB4J2QgvDihRKSTGjWahz5", already=False)
        self.assertIs(ctx.recorded("mintMetadata"), True)

    def patch_account_exists(self, seen: list[str], address: str, answer: bool):
        original = dp.account_exists

        def fake(_url: str, candidate: str) -> bool:
            seen.append(candidate)
            return answer and candidate == address

        return _SetAttr(dp, "account_exists", fake)

    def patch_run_forbidden(self):
        def forbidden(*_a, **_k):
            raise AssertionError("no child process should have run")

        return _SetAttr(dp, "run", forbidden)


class _SetAttr:
    """A one-line monkeypatch usable with `enterContext`, so a test reads top to bottom."""

    def __init__(self, module, name: str, value):
        self.module = module
        self.name = name
        self.value = value
        self.original = None

    def __enter__(self) -> "_SetAttr":
        self.original = getattr(self.module, self.name)
        setattr(self.module, self.name, self.value)
        return self

    def __exit__(self, *rest) -> None:
        setattr(self.module, self.name, self.original)


class TestFaultHook(unittest.TestCase):
    def setUp(self) -> None:
        dp.FAULTS.after.clear()
        dp.FAULTS.rpc.clear()
        self.addCleanup(dp.FAULTS.after.clear)
        self.addCleanup(dp.FAULTS.rpc.clear)

    def test_a_named_step_fires_once_and_then_is_spent(self) -> None:
        dp.FAULTS.arm(["after:mint"])
        with self.assertRaises(dp.InjectedFault):
            dp.FAULTS.after_step("mint")
        dp.FAULTS.after_step("mint")

    def test_a_fault_never_fires_without_the_flag(self) -> None:
        dp.FAULTS.after_step("mint")
        dp.FAULTS.before_rpc("getSignatureStatuses")

    def test_a_counted_rpc_fault_runs_out(self) -> None:
        dp.FAULTS.arm(["rpc:getSignatureStatuses:2"])
        for _ in range(2):
            with self.assertRaises(dp.urlrequest.HTTPError):
                dp.FAULTS.before_rpc("getSignatureStatuses")
        dp.FAULTS.before_rpc("getSignatureStatuses")

    def test_a_malformed_spec_is_refused_rather_than_ignored(self) -> None:
        for spec in ("mint", "after:", "rpc:getHealth", "rpc:getHealth:x", "sometimes:x"):
            with self.assertRaises(ValueError):
                dp.FAULTS.arm([spec])


class TestDryRun(WriteReadMixin):
    def test_a_dry_run_plans_and_writes_nothing(self) -> None:
        out = self.directory / "should-not-exist.json"
        # `--program-id` keeps this test about planning: the frozen id with the v2 build on
        # disk is the refusal `TestFrozenDevnetUpgradeGuard` is for, and a plan is not what
        # that combination produces.
        code = dp.main(["--dry-run", "--program-id", NOT_FROZEN, "--out", str(out)])
        self.assertEqual(code, dp.EXIT_OK)
        self.assertFalse(out.exists())

    def test_dry_run_needs_no_keypair_and_no_binary(self) -> None:
        # It resolves the plan from files and fixtures alone; a missing keypair is only fatal
        # on a real run. Proven by pointing it at a path that does not exist.
        out = self.directory / "still-not-there.json"
        code = dp.main(
            ["--dry-run", "--program-id", NOT_FROZEN, "--keypair", str(self.directory / "absent.json"), "--out", str(out)]
        )
        self.assertEqual(code, dp.EXIT_OK)
        self.assertFalse(out.exists())


class TestFrozenDevnetUpgradeGuard(unittest.TestCase):
    """The guard that makes the proven devnet deploy impossible to overwrite by accident.

    The facts it is built on: `5EJ1GU3M...` was deployed from the **v1** build with
    `target/deploy/cap_hook-keypair.json`, that keypair still unlocks it, and
    `cargo-build-sbf` writes the **v2** build over the same `target/deploy/cap_hook.so`
    this file deploys. So the deploy is an upgrade of a proven program, and the only thing
    that can say which build is in the file is the bytes. These tests hold the detector to
    the real `.so` on disk and to a v1-shaped blob built from the v1 log strings in git.
    """

    # The v1 build's own log lines, verbatim from `git show HEAD:programs/cap_hook/src/lib.rs`.
    # A real `.so` is ELF plus its string table and the detector reads strings, so these are
    # the bytes that decide it. The near-misses are deliberate: "below cap" is not "below
    # floor", "policy=capped" is not "policy=monitored", and "held_unix" is not
    # "held_since_unix", so a detector that matched a fragment fails here.
    V1_LIKE = (
        b"\x7fELF\x02\x01\x01\x00"
        b"ticketpath: cap exceeded price={} face={} cap_bps={}\x00"
        b"ticketpath: cap admitted price={} face={} cap_bps={}\x00"
        b"ticketpath: amount is not one\x00"
        b"ticketpath: transfer is not staged\x00"
        b"ticketpath: below cap price={}\x00"
        b"ticketpath: policy=capped price={}\x00"
        b"ticketpath: held_unix unknown\x00"
    )

    def real_bytes(self) -> bytes:
        if not dp.SO_PATH.exists():
            self.skipTest(f"{dp.SO_PATH.name} is not on disk: target/ is git-ignored and never committed")
        return dp.SO_PATH.read_bytes()

    # -- the detector -------------------------------------------------------------

    def test_the_detector_reads_the_real_so_as_the_v2_build(self) -> None:
        markers = dp.v2_log_strings_in(self.real_bytes())
        self.assertEqual(sorted(markers), sorted(dp.V2_ONLY_LOG_STRINGS))

    def test_the_detector_reads_a_v1_like_blob_as_v1(self) -> None:
        self.assertEqual(dp.v2_log_strings_in(self.V1_LIKE), ())

    def test_the_detector_reads_content_and_not_a_prefix(self) -> None:
        # One marker is enough, wherever in the file it sits: a partial v2 build is still v2.
        blob = b"\x7fELF" + b"x" * 4096 + b"ticketpath: held_since_unix not written"
        self.assertEqual(dp.v2_log_strings_in(blob), ("held_since_unix",))

    # -- the refusal --------------------------------------------------------------

    def test_the_guard_refuses_a_v2_binary_at_the_frozen_id(self) -> None:
        with self.assertRaises(dp.Refused) as caught:
            dp.refuse_frozen_devnet_upgrade(
                program_id=dp.FROZEN_DEVNET_PROGRAM,
                binary=self.real_bytes(),
                source="programs/cap_hook/target/deploy/cap_hook.so",
            )
        message = str(caught.exception)
        self.assertIn(dp.FROZEN_DEVNET_PROGRAM, message, "the refusal names the program id")
        self.assertIn("below floor", message, "and the reason: the v2-only log strings it carries")
        self.assertIn("v2", message)
        self.assertIn("publish_v2.py", message, "and the recorded way to deploy v2")
        self.assertIn("no flag", message, "and that nothing turns it off")

    def test_the_guard_does_not_refuse_a_v1_like_blob_at_the_frozen_id(self) -> None:
        dp.refuse_frozen_devnet_upgrade(
            program_id=dp.FROZEN_DEVNET_PROGRAM, binary=self.V1_LIKE, source="a v1 build"
        )

    def test_the_guard_does_not_fire_for_a_different_program_id(self) -> None:
        # Deploying the v2 build to a program of its own is `tools/publish_v2.py`'s job, and
        # this guard has no business in it.
        dp.refuse_frozen_devnet_upgrade(program_id=NOT_FROZEN, binary=self.real_bytes(), source="a v2 build")

    def test_an_absent_binary_is_not_a_v2_binary(self) -> None:
        # `--dry-run` before the first build: there is nothing to inspect and nothing sent.
        dp.refuse_frozen_devnet_upgrade(program_id=dp.FROZEN_DEVNET_PROGRAM, binary=b"", source="no file")

    def test_a_binary_that_cannot_be_read_stops_the_step(self) -> None:
        # Unknown bytes are not the same as absent bytes: a file that cannot be read could be
        # the v2 build, so the step stops rather than deploying something unchecked.
        directory = Path(tempfile.mkdtemp(prefix="tp-devnet-test-"))
        self.addCleanup(shutil.rmtree, directory, True)
        ctx = dp.Context(
            cluster="devnet",
            rpc_url="https://api.devnet.solana.com",
            keypair=directory / "authority.json",
            buyer_keypair=directory / "buyer.json",
            out=directory / "never-written.json",
            dry_run=True,
        )
        with _SetAttr(dp, "SO_PATH", directory):
            with self.assertRaises(dp.PublishError) as caught:
                dp.step_deploy(ctx, dp.FROZEN_DEVNET_PROGRAM)
        self.assertIn("cannot be checked", str(caught.exception))

    def test_nothing_in_the_environment_can_disarm_it(self) -> None:
        # The requirement is an absence, so it is checked as one: no `os.environ`, no getenv
        # and no argv in the detector or the refusal, and no parameter but the id and the bytes.
        source = inspect.getsource(dp.v2_log_strings_in) + inspect.getsource(dp.refuse_frozen_devnet_upgrade)
        for escape in ("os.environ", "getenv", "argv"):
            self.assertNotIn(escape, source)
        parameters = list(inspect.signature(dp.refuse_frozen_devnet_upgrade).parameters)
        self.assertEqual(parameters, ["program_id", "binary", "source"])

    # -- where it sits, and the rehearsal -----------------------------------------

    def test_the_guard_is_called_before_the_dry_run_branch(self) -> None:
        # A rehearsal is the run that shows the accident before anything is sent, so the guard
        # cannot sit inside the branch that only a real run takes.
        source = inspect.getsource(dp.step_deploy)
        self.assertLess(
            source.index("refuse_frozen_devnet_upgrade"),
            source.index("ctx.dry_run"),
            "step_deploy must guard before it plans, not after",
        )

    def test_the_dry_run_reports_the_refusal_and_sends_nothing(self) -> None:
        if not dp.SO_PATH.exists():
            self.skipTest(f"{dp.SO_PATH.name} is not on disk")
        out = Path(tempfile.mkdtemp(prefix="tp-devnet-test-")) / "never-written.json"
        self.addCleanup(shutil.rmtree, out.parent, True)
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = dp.main(["--dry-run", "--program-id", dp.FROZEN_DEVNET_PROGRAM, "--out", str(out)])
        self.assertEqual(code, dp.EXIT_REFUSED)
        self.assertIn(dp.FROZEN_DEVNET_PROGRAM, stderr.getvalue())
        self.assertIn("publish_v2.py", stderr.getvalue())
        self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
