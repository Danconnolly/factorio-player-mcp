"""Typed operations exposed by the eventual MCP server."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Protocol

from factorio_player_mcp.bridge import TypedCommandBuilder


class CommandSender(Protocol):
    """Internal transport for fixed commands sent to a Factorio instance."""

    def send_command(self, command: str) -> str: ...


class ActorService:
    """Invoke only the fixed Factorio mod interface and decode its responses."""

    def __init__(
        self,
        sender: CommandSender,
        *,
        sleep: Callable[[float], None] = time.sleep,
        poll_interval_seconds: float = 0.1,
    ) -> None:
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be positive")
        self._sender = sender
        self._commands = TypedCommandBuilder()
        self._sleep = sleep
        self._poll_interval_seconds = poll_interval_seconds

    def observe_actor(self) -> dict[str, object]:
        return self._invoke(self._commands.observe_actor())

    def craft(self, *, recipe: str, count: int) -> dict[str, object]:
        return self._invoke(self._commands.craft(recipe=recipe, count=count))

    def wait(self, *, ticks: int) -> dict[str, object]:
        return self._wait_for_action(self._commands.start_wait(ticks=ticks))

    def move(self, *, x: float, y: float) -> dict[str, object]:
        return self._wait_for_action(self._commands.start_move(x=x, y=y))

    def _wait_for_action(self, start_command: str) -> dict[str, object]:
        started = self._invoke(start_command)
        if started.get("status") != "accepted":
            return started

        action_id = started.get("action_id")
        if not isinstance(action_id, int) or isinstance(action_id, bool) or action_id <= 0:
            raise ValueError("accepted action response has no valid action_id")

        while True:
            status = self._invoke(self._commands.action_status(action_id=action_id))
            if status.get("status") != "accepted":
                return status
            self._sleep(self._poll_interval_seconds)

    def _invoke(self, command: str) -> dict[str, object]:
        raw_response = self._sender.send_command(command)
        try:
            response = json.loads(raw_response)
        except json.JSONDecodeError as error:
            raise ValueError("Factorio mod response is not a valid JSON object") from error
        if not isinstance(response, dict):
            raise ValueError("Factorio mod response is not a valid JSON object")
        return response
