"""Typed operations exposed by the eventual MCP server."""

from __future__ import annotations

import json
from typing import Protocol

from factorio_player_mcp.bridge import TypedCommandBuilder


class CommandSender(Protocol):
    """Internal transport for fixed commands sent to a Factorio instance."""

    def send_command(self, command: str) -> str: ...


class ActorService:
    """Invoke only the fixed Factorio mod interface and decode its responses."""

    def __init__(self, sender: CommandSender) -> None:
        self._sender = sender
        self._commands = TypedCommandBuilder()

    def observe_actor(self) -> dict[str, object]:
        return self._invoke(self._commands.observe_actor())

    def craft(self, *, recipe: str, count: int) -> dict[str, object]:
        return self._invoke(self._commands.craft(recipe=recipe, count=count))

    def _invoke(self, command: str) -> dict[str, object]:
        raw_response = self._sender.send_command(command)
        try:
            response = json.loads(raw_response)
        except json.JSONDecodeError as error:
            raise ValueError("Factorio mod response is not a valid JSON object") from error
        if not isinstance(response, dict):
            raise ValueError("Factorio mod response is not a valid JSON object")
        return response
