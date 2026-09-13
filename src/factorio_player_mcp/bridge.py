"""Narrow command construction for the fixed Factorio mod interface.

This is deliberately not a general Lua or RCON command executor.  It adapts the
native-player primitive choices from FactoMCP to a fixed, server-owned mod
interface.
"""

from __future__ import annotations

import re


_RECIPE_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_MAX_WAIT_TICKS = 3_600


class TypedCommandBuilder:
    """Build only static calls to the factorio-player-mcp mod interface."""

    _INTERFACE = "factorio_player_mcp"

    def observe_actor(self) -> str:
        return self._remote_call("observe_actor")

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

    def _remote_call(self, method: str, *arguments: str) -> str:
        arguments_text = ", ".join(
            (f"'{self._INTERFACE}'", f"'{method}'", *arguments)
        )
        return f"/silent-command rcon.print(remote.call({arguments_text}))"
