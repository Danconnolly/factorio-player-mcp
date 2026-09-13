"""Tests for the internal RCON transport."""

from __future__ import annotations

import unittest

from factorio_player_mcp.rcon import FactorioRconSender


class FakeRconClient:
    def __init__(self) -> None:
        self.commands: list[str] = []

    def send_command(self, command: str) -> str:
        self.commands.append(command)
        return '{"status":"completed"}'


class FactorioRconSenderTests(unittest.TestCase):
    def test_sender_connects_once_and_forwards_fixed_commands(self) -> None:
        created: list[tuple[str, int, str]] = []
        client = FakeRconClient()

        def client_factory(host: str, port: int, password: str) -> FakeRconClient:
            created.append((host, port, password))
            return client

        sender = FactorioRconSender(
            host="127.0.0.1",
            port=25575,
            password="test-password",
            client_factory=client_factory,
        )

        response = sender.send_command("/silent-command rcon.print('ok')")

        self.assertEqual(response, '{"status":"completed"}')
        self.assertEqual(created, [("127.0.0.1", 25575, "test-password")])
        self.assertEqual(client.commands, ["/silent-command rcon.print('ok')"])

    def test_sender_rejects_invalid_port(self) -> None:
        with self.assertRaisesRegex(ValueError, "port"):
            FactorioRconSender(host="127.0.0.1", port=0, password="test-password")


if __name__ == "__main__":
    unittest.main()
