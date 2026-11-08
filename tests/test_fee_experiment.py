"""The fee experiment's arithmetic, its readers, and its refusals.

The thing under test exists to replace an argument with a measurement, so the tests are
written the same way: they assert what Token-2022's `calculate_fee` actually does, and
one of them pins the reading the brief started from -- `floor(1 * 500 / 10_000) = 0` --
so that the disagreement is visible in a test that can fail rather than buried in prose.

Nothing here needs a cluster, a keypair or a Solana binary. The one test that starts a
process is the refusal test, and it starts nothing: it points the readiness check at a
port it has just closed and requires the failure.
"""

from __future__ import annotations

import socket
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
for entry in (str(REPO_ROOT), str(REPO_ROOT / "tools")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

import fee_experiment as fe  # noqa: E402

#: One real token account, in the shape `getAccountInfo(jsonParsed)` returns. Values
#: transcribed from the run this tool performed; the withheld unit is the measured one.
TOKEN_ACCOUNT = {
    "data": {
        "program": "spl-token-2022",
        "parsed": {
            "type": "account",
            "info": {
                "isNative": False,
                "mint": "FMc5YP52W5m6SMCTwmM6JDT7czvn54WTdAsNNbMNSGyd",
                "owner": "3XV47xLAGPhAEn3vGx1iEagJjpuihYyiybxGnRL53xUn",
                "state": "initialized",
                "tokenAmount": {"amount": "0", "decimals": 0, "uiAmount": 0.0, "uiAmountString": "0"},
                "extensions": [
                    {"extension": "immutableOwner"},
                    {"extension": "transferFeeAmount", "state": {"withheldAmount": 1}},
                ],
            },
        },
        "space": 182,
    },
    "executable": False,
    "lamports": 2039280,
    "owner": "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
}


def token_account_without_fee_extension() -> dict:
    return {
        "data": {
            "program": "spl-token-2022",
            "parsed": {
                "type": "account",
                "info": {
                    "mint": TOKEN_ACCOUNT["data"]["parsed"]["info"]["mint"],
                    "state": "initialized",
                    "tokenAmount": {"amount": "1", "decimals": 0, "uiAmount": 1.0, "uiAmountString": "1"},
                    "extensions": [{"extension": "immutableOwner"}],
                },
            },
        }
    }


class FeeArithmetic(unittest.TestCase):
    """`fee_for` is Token-2022's ceiling, and the ceiling is the whole finding."""

    def test_the_zero_the_brief_expected_is_not_what_the_code_asserts(self):
        """The premise was `floor(1 * bps / 10_000) = 0`. The code must not assert that.

        If this test ever fails because `fee_for(1, 500)` returned 0, the measurement and
        the tool have diverged and the finding is stale: the cluster withheld 1.
        """
        for bps in (1, 500, 1_500, 9_999):
            with self.subTest(bps=bps):
                self.assertEqual(fe.fee_for(1, bps, 1_000_000), 1)
                self.assertNotEqual(fe.fee_for(1, bps, 1_000_000), 0)

    def test_floor_reading_disagrees_at_one_unit(self):
        # The brief's formula is kept only so the disagreement is computed, never used.
        self.assertEqual(fe.floor_fee_for(1, 500), 0)
        self.assertEqual(fe.floor_fee_for(1, 1_500), 0)
        self.assertNotEqual(fe.fee_for(1, 1_500, 1_000_000), fe.floor_fee_for(1, 1_500))

    def test_ten_units_at_1500_withholds_two_not_one(self):
        # Measured: withheldAmount = 2, recipient = 8. The floor reading says 1.
        self.assertEqual(fe.fee_for(10, 1_500, 1_000_000), 2)
        self.assertEqual(fe.floor_fee_for(10, 1_500), 1)

    def test_decimals_nine_scales_with_base_units_not_with_a_price(self):
        # 1_000_000_000 base units at 1500 bps is exactly 150_000_000, no rounding either way.
        self.assertEqual(fe.fee_for(1_000_000_000, 1_500, 1_000_000_000), 150_000_000)
        # The same rate on the same *price* but a different base-unit amount is a different fee:
        self.assertEqual(fe.fee_for(1, 1_500, 1_000_000_000), 1)
        self.assertNotEqual(fe.fee_for(1, 1_500, 1_000_000_000), 150_000_000)

    def test_zero_amount_or_zero_rate_withholds_nothing(self):
        self.assertEqual(fe.fee_for(0, 1_500, 1_000_000), 0)
        self.assertEqual(fe.fee_for(1, 0, 1_000_000), 0)
        self.assertEqual(fe.fee_for(1_000_000_000, 0), 0)

    def test_maximum_fee_clamps_and_zero_maximum_switches_the_fee_off(self):
        self.assertEqual(fe.fee_for(10, 1_500, 1), 1)
        self.assertEqual(fe.fee_for(1, 1_500, 0), 0)
        self.assertEqual(fe.fee_for(1_000_000, 500, 100), 100)

    def test_a_rate_above_one_hundred_percent_is_refused(self):
        with self.assertRaises(ValueError):
            fe.fee_for(1, 10_001)
        with self.assertRaises(ValueError):
            fe.fee_for(1, -1)

    def test_ceil_div_matches_the_definition(self):
        self.assertEqual(fe.ceil_div(1, 10_000), 1)
        self.assertEqual(fe.ceil_div(10_000, 10_000), 1)
        self.assertEqual(fe.ceil_div(10_001, 10_000), 2)
        self.assertEqual(fe.ceil_div(0, 10_000), 0)
        with self.assertRaises(ValueError):
            fe.ceil_div(1, 0)


class AccountReaders(unittest.TestCase):
    def test_withheld_amount_from_jsonparsed(self):
        self.assertEqual(fe.withheld_amount(TOKEN_ACCOUNT), 1)
        self.assertEqual(fe.token_amount(TOKEN_ACCOUNT), 0)

    def test_missing_transfer_fee_extension_is_an_error_not_a_zero(self):
        # A zero is a measurement; a missing extension is a different account than the one
        # the experiment asked for. Defaulting to 0 here would fake a result.
        with self.assertRaises(fe.ExperimentError):
            fe.withheld_amount(token_account_without_fee_extension())

    def test_wrong_program_is_refused(self):
        value = dict(TOKEN_ACCOUNT)
        value["data"] = {"program": "spl-token", "parsed": {"type": "account", "info": {}}}
        with self.assertRaises(fe.ExperimentError):
            fe.withheld_amount(value)

    def test_ui_amount_conversion(self):
        self.assertEqual(fe.ui_amount(3, 0), "3")
        self.assertEqual(fe.ui_amount(1_000_000_000, 9), "1.000000000")
        self.assertEqual(fe.ui_amount(1, 9), "0.000000001")


class WireFormat(unittest.TestCase):
    """Pin the instruction bytes, so a refactor cannot quietly measure a different thing."""

    def test_transfer_checked_is_amount_in_base_units(self):
        experiment = fe.Experiment(fe.parse_arguments([]))
        experiment.payer = "11111111111111111111111111111111"
        instruction = experiment.transfer_checked(
            source="So11111111111111111111111111111111111111112",
            mint=fe.TOKEN_2022_PROGRAM,
            destination="SysvarRent111111111111111111111111111111111",
            amount=10,
            decimals=0,
            extra_accounts=(),
        )
        self.assertEqual(instruction.program_id, fe.TOKEN_2022_PROGRAM)
        # 12 = TransferChecked; amount little-endian u64; decimals u8.
        self.assertEqual(instruction.data, bytes([12]) + (10).to_bytes(8, "little") + bytes([0]))
        self.assertEqual(len(instruction.accounts), 4)
        self.assertTrue(instruction.accounts[0].is_writable)

    def test_withdraw_withheld_is_the_accounts_instruction(self):
        experiment = fe.Experiment(fe.parse_arguments([]))
        experiment.payer = "11111111111111111111111111111111"
        instruction = experiment.withdraw_withheld(
            mint=fe.TOKEN_2022_PROGRAM,
            destination="SysvarRent111111111111111111111111111111111",
            sources=["So11111111111111111111111111111111111111112"],
        )
        # 26 = TransferFeeExtension, 3 = WithdrawWithheldTokensFromAccounts, 1 source.
        self.assertEqual(instruction.data, bytes([26, 3, 1]))
        self.assertEqual(len(instruction.accounts), 4)


class Refusals(unittest.TestCase):
    """The experiment must not start on anything but a local validator it funded itself."""

    def test_refuses_devnet_and_mainnet(self):
        for url in ("https://api.devnet.solana.com", "https://api.mainnet-beta.solana.com", "http://127.0.0.1:8899/"):
            with self.subTest(url=url):
                with self.assertRaises(fe.ExperimentError):
                    fe.assert_local_url(url)
        fe.assert_local_url("http://127.0.0.1:18999")
        fe.assert_local_url("http://localhost:18999")

    def test_refuses_an_unfunded_payer(self):
        with self.assertRaises(fe.ExperimentError):
            fe.assert_funded(0)
        with self.assertRaises(fe.ExperimentError):
            fe.assert_funded(999_999_999)
        fe.assert_funded(1_000_000_000)

    def test_refuses_without_the_validator_binary(self):
        with self.assertRaises(fe.ExperimentError):
            fe.require_binary("solana-test-validator-that-does-not-exist")

    def test_refuses_to_wait_on_a_validator_that_is_not_there(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        # The port was just closed: nothing is listening, so readiness must fail, not hang.
        with self.assertRaises(fe.ExperimentError):
            fe.Validator.wait_health(f"http://127.0.0.1:{port}", timeout=1.0)

    def test_refuses_a_workdir_outside_the_git_ignored_tree(self):
        experiment = fe.Experiment(fe.parse_arguments(["--workdir", str(REPO_ROOT / "tmp" / "fee-experiment")]))
        with self.assertRaises(fe.ExperimentError):
            experiment.prepare()


if __name__ == "__main__":
    unittest.main()
