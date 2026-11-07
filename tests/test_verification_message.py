"""The verification message is frozen by the contract. These bytes must not move."""

from __future__ import annotations

import unittest

from ticketpath.core import verification_message

WALLET = "FXTUREacct111111111111111111111111111111111"
NONCE = "0123456789abcdef0123456789abcdef"


class TestVerificationMessage(unittest.TestCase):
    def test_exact_bytes(self) -> None:
        expected = (
            "Verify wallet ownership for ticket issuance.\n"
            "\n"
            "Wallet: FXTUREacct111111111111111111111111111111111\n"
            "Nonce: 0123456789abcdef0123456789abcdef\n"
            "Cluster: devnet"
        )
        self.assertEqual(verification_message.build(WALLET, NONCE, "devnet"), expected)

    def test_no_trailing_newline(self) -> None:
        text = verification_message.build(WALLET, NONCE, "devnet")
        self.assertFalse(text.endswith("\n"))
        self.assertEqual(len(text.split("\n")), 5)

    def test_bytes_are_utf8_of_the_string(self) -> None:
        text = verification_message.build(WALLET, NONCE, "devnet")
        self.assertEqual(verification_message.build_bytes(WALLET, NONCE, "devnet"), text.encode("utf-8"))

    def test_cluster_is_part_of_the_message(self) -> None:
        devnet = verification_message.build(WALLET, NONCE, "devnet")
        mainnet = verification_message.build(WALLET, NONCE, "mainnet-beta")
        self.assertNotEqual(devnet, mainnet)
        self.assertTrue(mainnet.endswith("Cluster: mainnet-beta"))


if __name__ == "__main__":
    unittest.main()
