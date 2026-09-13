"""Tests for the narrow host-side Factorio actor service."""

from __future__ import annotations

import unittest

from factorio_player_mcp.service import ActorService


class RecordingSender:
    def __init__(self, *responses: str) -> None:
        self.responses = list(responses)
        self.commands: list[str] = []

    def send_command(self, command: str) -> str:
        self.commands.append(command)
        return self.responses.pop(0)


class ActorServiceTests(unittest.TestCase):
    def test_observe_actor_returns_the_mod_response(self) -> None:
        sender = RecordingSender('{"status":"completed","tick":42,"inventory":[]}')
        service = ActorService(sender)

        result = service.observe_actor()

        self.assertEqual(result, {"status": "completed", "tick": 42, "inventory": []})
        self.assertEqual(
            sender.commands,
            ["/silent-command rcon.print(remote.call('factorio_player_mcp', 'observe_actor'))"],
        )

    def test_observe_local_returns_the_bounded_mod_response(self) -> None:
        sender = RecordingSender('{"status":"completed","local_entities":[]}')
        service = ActorService(sender)

        result = service.observe_local(radius=10)

        self.assertEqual(result, {"status": "completed", "local_entities": []})
        self.assertEqual(
            sender.commands,
            ["/silent-command rcon.print(remote.call('factorio_player_mcp', 'observe_local', 10))"],
        )

    def test_craft_returns_the_mod_response(self) -> None:
        sender = RecordingSender('{"status":"completed","queued_count":1}')
        service = ActorService(sender)

        result = service.craft(recipe="iron-gear-wheel", count=1)

        self.assertEqual(result, {"status": "completed", "queued_count": 1})
        self.assertEqual(
            sender.commands,
            [
                "/silent-command rcon.print(remote.call("
                "'factorio_player_mcp', 'craft', 'iron-gear-wheel', 1))"
            ],
        )

    def test_wait_polls_the_same_action_until_completion(self) -> None:
        sender = RecordingSender(
            '{"status":"accepted","action_id":7,"requested_tick":10}',
            '{"status":"accepted","action_id":7,"requested_tick":10}',
            '{"status":"completed","action_id":7,"requested_tick":10,"resolved_tick":13}',
        )
        sleeps: list[float] = []
        service = ActorService(sender, sleep=sleeps.append, poll_interval_seconds=0.01)

        result = service.wait(ticks=3)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["resolved_tick"], 13)
        self.assertEqual(
            sender.commands,
            [
                "/silent-command rcon.print(remote.call('factorio_player_mcp', 'start_wait', 3))",
                "/silent-command rcon.print(remote.call('factorio_player_mcp', 'action_status', 7))",
                "/silent-command rcon.print(remote.call('factorio_player_mcp', 'action_status', 7))",
            ],
        )
        self.assertEqual(sleeps, [0.01])

    def test_move_polls_the_same_action_until_completion(self) -> None:
        sender = RecordingSender(
            '{"status":"accepted","action_id":8,"requested_tick":20}',
            '{"status":"completed","action_id":8,"requested_tick":20,"resolved_tick":80}',
        )
        service = ActorService(sender, sleep=lambda _: None, poll_interval_seconds=0.01)

        result = service.move(x=-3.5, y=26)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(
            sender.commands,
            [
                "/silent-command rcon.print(remote.call('factorio_player_mcp', 'start_move', -3.5, 26))",
                "/silent-command rcon.print(remote.call('factorio_player_mcp', 'action_status', 8))",
            ],
        )

    def test_mine_polls_the_same_action_until_completion(self) -> None:
        sender = RecordingSender(
            '{"status":"accepted","action_id":9,"requested_tick":100}',
            '{"status":"completed","action_id":9,"requested_tick":100,"resolved_tick":180}',
        )
        service = ActorService(sender, sleep=lambda _: None, poll_interval_seconds=0.01)

        result = service.mine(x=1.5, y=-2, count=3)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(
            sender.commands,
            [
                "/silent-command rcon.print(remote.call('factorio_player_mcp', 'start_mine', 1.5, -2, 3))",
                "/silent-command rcon.print(remote.call('factorio_player_mcp', 'action_status', 9))",
            ],
        )

    def test_place_returns_the_mod_response(self) -> None:
        sender = RecordingSender('{"status":"completed","item":"stone-furnace"}')
        service = ActorService(sender)

        result = service.place(item="stone-furnace", x=3.5, y=-2, direction="east")

        self.assertEqual(result, {"status": "completed", "item": "stone-furnace"})
        self.assertEqual(
            sender.commands,
            [
                "/silent-command rcon.print(remote.call("
                "'factorio_player_mcp', 'place', 'stone-furnace', 3.5, -2, 'east'))"
            ],
        )

    def test_rotate_returns_the_mod_response(self) -> None:
        sender = RecordingSender('{"status":"completed","reverse":true}')
        service = ActorService(sender)

        result = service.rotate(x=3.5, y=-2, reverse=True)

        self.assertEqual(result, {"status": "completed", "reverse": True})
        self.assertEqual(
            sender.commands,
            ["/silent-command rcon.print(remote.call('factorio_player_mcp', 'rotate', 3.5, -2, true))"],
        )

    def test_invalid_craft_request_does_not_reach_the_sender(self) -> None:
        sender = RecordingSender()
        service = ActorService(sender)

        with self.assertRaisesRegex(ValueError, "recipe"):
            service.craft(recipe="iron'); game.print('unsafe", count=1)

        self.assertEqual(sender.commands, [])

    def test_malformed_mod_response_is_rejected(self) -> None:
        sender = RecordingSender("not-json")
        service = ActorService(sender)

        with self.assertRaisesRegex(ValueError, "valid JSON object"):
            service.observe_actor()


if __name__ == "__main__":
    unittest.main()
