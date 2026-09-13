"""Narrow command construction for the fixed Factorio mod interface.

This is deliberately not a general Lua or RCON command executor.  It adapts the
native-player primitive choices from FactoMCP to a fixed, server-owned mod
interface.
"""

from __future__ import annotations

import math
import re


_RECIPE_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_MAX_WAIT_TICKS = 3_600
_MAX_COORDINATE = 1_000_000
_MAX_MINE_COUNT = 100
_MAX_OBSERVATION_RADIUS = 20
_MAX_INVENTORY_INTERACTION_COUNT = 100
_DIRECTIONS = frozenset({"north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"})
_INVENTORY_OPERATIONS = frozenset({"deposit", "withdraw"})
_INVENTORY_SLOTS = frozenset({"container", "input", "fuel", "output"})


class TypedCommandBuilder:
    """Build only static calls to the factorio-player-mcp mod interface."""

    _INTERFACE = "factorio_player_mcp"

    def observe_actor(self) -> str:
        return self._remote_call("observe_actor")

    def observe_local(self, *, radius: int) -> str:
        if not isinstance(radius, int) or isinstance(radius, bool) or not 1 <= radius <= _MAX_OBSERVATION_RADIUS:
            raise ValueError(f"radius must be an integer between 1 and {_MAX_OBSERVATION_RADIUS}")
        return self._remote_call("observe_local", str(radius))

    def craft(self, *, recipe: str, count: int) -> str:
        if not _RECIPE_NAME.fullmatch(recipe):
            raise ValueError("recipe must be a lowercase Factorio prototype name")
        if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
            raise ValueError("count must be a positive integer")
        return self._remote_call("craft", f"'{recipe}'", str(count))

    def start_wait(self, *, ticks: int) -> str:
        if not isinstance(ticks, int) or isinstance(ticks, bool) or not 1 <= ticks <= _MAX_WAIT_TICKS:
            raise ValueError(f"ticks must be an integer between 1 and {_MAX_WAIT_TICKS}")
        return self._remote_call("start_wait", str(ticks))

    def action_status(self, *, action_id: int) -> str:
        if not isinstance(action_id, int) or isinstance(action_id, bool) or action_id <= 0:
            raise ValueError("action_id must be a positive integer")
        return self._remote_call("action_status", str(action_id))

    def start_move(self, *, x: float, y: float) -> str:
        return self._remote_call("start_move", self._coordinate("x", x), self._coordinate("y", y))

    def start_mine(self, *, x: float, y: float, count: int) -> str:
        if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= _MAX_MINE_COUNT:
            raise ValueError(f"count must be an integer between 1 and {_MAX_MINE_COUNT}")
        return self._remote_call(
            "start_mine",
            self._coordinate("x", x),
            self._coordinate("y", y),
            str(count),
        )

    def place(self, *, item: str, x: float, y: float, direction: str) -> str:
        if not _RECIPE_NAME.fullmatch(item):
            raise ValueError("item must be a lowercase Factorio prototype name")
        if direction not in _DIRECTIONS:
            raise ValueError("direction must be one of the eight Factorio directions")
        return self._remote_call(
            "place",
            f"'{item}'",
            self._coordinate("x", x),
            self._coordinate("y", y),
            f"'{direction}'",
        )

    def rotate(self, *, x: float, y: float, reverse: bool = False) -> str:
        if not isinstance(reverse, bool):
            raise ValueError("reverse must be a boolean")
        return self._remote_call(
            "rotate",
            self._coordinate("x", x),
            self._coordinate("y", y),
            "true" if reverse else "false",
        )

    def interact_inventory(
        self, *, x: float, y: float, item: str, count: int, operation: str, slot: str
    ) -> str:
        if not _RECIPE_NAME.fullmatch(item):
            raise ValueError("item must be a lowercase Factorio prototype name")
        if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= _MAX_INVENTORY_INTERACTION_COUNT:
            raise ValueError(f"count must be an integer between 1 and {_MAX_INVENTORY_INTERACTION_COUNT}")
        if operation not in _INVENTORY_OPERATIONS:
            raise ValueError("operation must be deposit or withdraw")
        if slot not in _INVENTORY_SLOTS:
            raise ValueError("slot must be container, input, fuel, or output")
        return self._remote_call(
            "interact_inventory",
            self._coordinate("x", x),
            self._coordinate("y", y),
            f"'{item}'",
            str(count),
            f"'{operation}'",
            f"'{slot}'",
        )

    @staticmethod
    def _coordinate(name: str, value: float) -> str:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be a finite coordinate")
        if not math.isfinite(value) or abs(value) > _MAX_COORDINATE:
            raise ValueError(f"{name} must be a finite coordinate within map bounds")
        return format(value, "g")

    def _remote_call(self, method: str, *arguments: str) -> str:
        arguments_text = ", ".join(
            (f"'{self._INTERFACE}'", f"'{method}'", *arguments)
        )
        return f"/silent-command rcon.print(remote.call({arguments_text}))"
