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

    def test_mine_uses_a_fixed_start_method(self) -> None:
        self.assertEqual(
            self.builder.start_mine(x=1.5, y=-2, count=3),
            "/silent-command rcon.print(remote.call('factorio_player_mcp', 'start_mine', 1.5, -2, 3))",
        )

    def test_mine_rejects_invalid_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "count"):
            self.builder.start_mine(x=0, y=0, count=0)
        with self.assertRaisesRegex(ValueError, "count"):
            self.builder.start_mine(x=0, y=0, count=101)

    def test_place_uses_a_validated_item_and_cardinal_direction(self) -> None:
        self.assertEqual(
            self.builder.place(item="stone-furnace", x=3.5, y=-2, direction="east"),
            "/silent-command rcon.print(remote.call('factorio_player_mcp', 'place', 'stone-furnace', 3.5, -2, 'east'))",
        )
        with self.assertRaisesRegex(ValueError, "item"):
            self.builder.place(item="stone'); game.print('unsafe", x=0, y=0, direction="north")
        with self.assertRaisesRegex(ValueError, "direction"):
            self.builder.place(item="stone-furnace", x=0, y=0, direction="up")

    def test_rotate_uses_a_fixed_target_and_optional_reverse(self) -> None:
        self.assertEqual(
            self.builder.rotate(x=3.5, y=-2, reverse=True),
            "/silent-command rcon.print(remote.call('factorio_player_mcp', 'rotate', 3.5, -2, true))",
        )
        with self.assertRaisesRegex(ValueError, "reverse"):
            self.builder.rotate(x=0, y=0, reverse=1)

    def test_interact_inventory_uses_a_fixed_operation_and_slot(self) -> None:
        self.assertEqual(
            self.builder.interact_inventory(
                x=3.5, y=-2, item="coal", count=2, operation="deposit", slot="fuel"
            ),
            "/silent-command rcon.print(remote.call("
            "'factorio_player_mcp', 'interact_inventory', 3.5, -2, 'coal', 2, 'deposit', 'fuel'))",
        )
        with self.assertRaisesRegex(ValueError, "operation"):
            self.builder.interact_inventory(x=0, y=0, item="coal", count=1, operation="delete", slot="fuel")
        with self.assertRaisesRegex(ValueError, "slot"):
            self.builder.interact_inventory(x=0, y=0, item="coal", count=1, operation="deposit", slot="all")

    def test_observe_local_uses_a_bounded_radius(self) -> None:
        self.assertEqual(
            self.builder.observe_local(radius=10),
            "/silent-command rcon.print(remote.call('factorio_player_mcp', 'observe_local', 10))",
        )
        with self.assertRaisesRegex(ValueError, "radius"):
            self.builder.observe_local(radius=0)
        with self.assertRaisesRegex(ValueError, "radius"):
            self.builder.observe_local(radius=21)

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
        self.assertIn("start_mine = function(x, y, count)", control_lua)
        self.assertIn("place = function(item_name, x, y, direction_name)", control_lua)
        self.assertIn("rotate = function(x, y, reverse)", control_lua)
        self.assertIn("interact_inventory = function(x, y, item_name, count, operation, slot_name)", control_lua)
        self.assertIn("target_inventory_for", control_lua)
        self.assertIn("entity.get_fuel_inventory()", control_lua)
        self.assertIn("entity.get_inventory(2)", control_lua)
        self.assertIn("if removed == 0 then", control_lua)
        self.assertIn("player.build_from_cursor", control_lua)
        self.assertIn("local before_count = inventory.get_item_count(item_name)", control_lua)
        self.assertIn("target.rotate({reverse = reverse, by_player = player.index})", control_lua)
        self.assertNotIn("player.rotate_entity", control_lua)
        self.assertIn("defines.events.on_player_mined_entity", control_lua)
        self.assertIn("action.mined_count", control_lua)
        self.assertIn("local progress = player.character_mining_progress", control_lua)
        self.assertIn("observe_local = function(radius)", control_lua)
        self.assertIn("action_status = function(action_id)", control_lua)
        self.assertIn("player.walking_state", control_lua)
        self.assertIn("player.mining_state", control_lua)
        self.assertNotIn("game.players[", control_lua)
        self.assertNotIn("teleport", control_lua)
        self.assertNotIn("create_entity", control_lua)
        self.assertNotIn("mine_entity", control_lua)

    def test_wait_action_remains_pending_before_its_target_tick(self) -> None:
        control_lua = CONTROL_LUA_PATH.read_text(encoding="utf-8")

        self.assertIn(
            '''  if action.action_type == "wait" then
    if event.tick >= action.target_tick then
      finish_action(action, "completed", event.tick)
    end
  elseif action.action_type == "move" then''',
            control_lua,
        )

    def test_mod_declares_factorio_2_1_compatibility(self) -> None:
        import json

        mod_info = json.loads(MOD_INFO_PATH.read_text(encoding="utf-8"))

        self.assertEqual(mod_info["factorio_version"], "2.1")
        self.assertEqual(mod_info["version"], "0.1.15")

    def test_mod_setting_has_a_human_readable_locale_name(self) -> None:
        locale = LOCALE_PATH.read_text(encoding="utf-8")

        self.assertIn("[mod-setting-name]", locale)
        self.assertIn("factorio-player-mcp-actor-name=Dedicated player name", locale)
        self.assertIn("[mod-setting-description]", locale)


if __name__ == "__main__":
    unittest.main()
