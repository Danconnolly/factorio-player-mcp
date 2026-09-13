"""Tests for the narrowed FactoMCP-derived typed bridge."""

from __future__ import annotations

import unittest
from pathlib import Path

from factorio_player_mcp.bridge import TypedCommandBuilder


REPOSITORY_ROOT = Path(__file__).parents[1]
CONTROL_LUA_PATH = REPOSITORY_ROOT / "factorio_mod" / "control.lua"
MOD_INFO_PATH = REPOSITORY_ROOT / "factorio_mod" / "info.json"
LOCALE_PATH = REPOSITORY_ROOT / "factorio_mod" / "locale" / "en" / "factorio-player-mcp.cfg"


class TypedCommandBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = TypedCommandBuilder()

    def test_observe_command_calls_only_the_fixed_mod_interface(self) -> None:
        command = self.builder.observe_actor()

        self.assertEqual(
            command,
            "/silent-command rcon.print(remote.call('factorio_player_mcp', 'observe_actor'))",
        )
        self.assertNotIn("game.players[", command)

    def test_craft_command_uses_a_validated_recipe_and_count(self) -> None:
        command = self.builder.craft(recipe="iron-gear-wheel", count=2)

        self.assertEqual(
            command,
            "/silent-command rcon.print(remote.call('factorio_player_mcp', 'craft', 'iron-gear-wheel', 2))",
        )

    def test_craft_command_rejects_lua_injection_in_recipe_name(self) -> None:
        with self.assertRaisesRegex(ValueError, "recipe"):
            self.builder.craft(recipe="iron'); game.print('unsafe", count=1)

    def test_craft_command_rejects_non_positive_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "count"):
            self.builder.craft(recipe="iron-gear-wheel", count=0)

    def test_wait_uses_fixed_start_and_status_methods(self) -> None:
        self.assertEqual(
            self.builder.start_wait(ticks=120),
            "/silent-command rcon.print(remote.call('factorio_player_mcp', 'start_wait', 120))",
        )
        self.assertEqual(
            self.builder.action_status(action_id=7),
            "/silent-command rcon.print(remote.call('factorio_player_mcp', 'action_status', 7))",
        )

    def test_wait_rejects_unbounded_or_non_positive_ticks(self) -> None:
        with self.assertRaisesRegex(ValueError, "ticks"):
            self.builder.start_wait(ticks=0)
        with self.assertRaisesRegex(ValueError, "ticks"):
            self.builder.start_wait(ticks=3601)

    def test_move_uses_fixed_start_and_status_methods(self) -> None:
        self.assertEqual(
            self.builder.start_move(x=-3.5, y=26),
            "/silent-command rcon.print(remote.call('factorio_player_mcp', 'start_move', -3.5, 26))",
        )

    def test_move_rejects_non_finite_coordinates(self) -> None:
        with self.assertRaisesRegex(ValueError, "x"):
            self.builder.start_move(x=float("inf"), y=0)
        with self.assertRaisesRegex(ValueError, "y"):
            self.builder.start_move(x=0, y=float("nan"))

    def test_no_generic_command_execution_is_available(self) -> None:
        self.assertFalse(hasattr(self.builder, "execute"))
        self.assertFalse(hasattr(self.builder, "run_lua"))

    def test_game_mod_exposes_only_fixed_actor_operations(self) -> None:
        control_lua = CONTROL_LUA_PATH.read_text(encoding="utf-8")

        self.assertIn('remote.add_interface("factorio_player_mcp"', control_lua)
        self.assertIn("configured_dedicated_player_name", control_lua)
        self.assertIn("player.begin_crafting", control_lua)
        self.assertIn("for _, item in pairs(contents) do", control_lua)
        self.assertIn("name = item.name, count = item.count", control_lua)
        self.assertIn("storage.active_action", control_lua)
        self.assertIn("script.on_event(defines.events.on_tick", control_lua)
        self.assertIn("start_wait = function(ticks)", control_lua)
        self.assertIn("start_move = function(x, y)", control_lua)
        self.assertIn("action_status = function(action_id)", control_lua)
        self.assertIn("player.walking_state", control_lua)
        self.assertNotIn("game.players[", control_lua)
        self.assertNotIn("teleport", control_lua)
        self.assertNotIn("create_entity", control_lua)
        self.assertNotIn("mine_entity", control_lua)

    def test_mod_declares_factorio_2_1_compatibility(self) -> None:
        import json

        mod_info = json.loads(MOD_INFO_PATH.read_text(encoding="utf-8"))

        self.assertEqual(mod_info["factorio_version"], "2.1")
        self.assertEqual(mod_info["version"], "0.1.5")

    def test_mod_setting_has_a_human_readable_locale_name(self) -> None:
        locale = LOCALE_PATH.read_text(encoding="utf-8")

        self.assertIn("[mod-setting-name]", locale)
        self.assertIn("factorio-player-mcp-actor-name=Dedicated player name", locale)
        self.assertIn("[mod-setting-description]", locale)


if __name__ == "__main__":
    unittest.main()
