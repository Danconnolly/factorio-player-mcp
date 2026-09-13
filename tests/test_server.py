"""Tests for the agent-facing MCP tool allow-list."""

from __future__ import annotations

import asyncio
import unittest

from factorio_player_mcp.server import create_server


class FakeActorService:
    def observe_actor(self) -> dict[str, object]:
        return {"status": "completed"}

    def observe_local(self, *, radius: int) -> dict[str, object]:
        return {"status": "completed", "radius": radius}

    def craft(self, *, recipe: str, count: int) -> dict[str, object]:
        return {"status": "completed", "recipe": recipe, "count": count}

    def wait(self, *, ticks: int) -> dict[str, object]:
        return {"status": "completed", "ticks": ticks}

    def move(self, *, x: float, y: float) -> dict[str, object]:
        return {"status": "completed", "x": x, "y": y}

    def mine(self, *, x: float, y: float, count: int) -> dict[str, object]:
        return {"status": "completed", "x": x, "y": y, "count": count}

    def place(self, *, item: str, x: float, y: float, direction: str) -> dict[str, object]:
        return {"status": "completed", "item": item, "x": x, "y": y, "direction": direction}

    def rotate(self, *, x: float, y: float, reverse: bool = False) -> dict[str, object]:
        return {"status": "completed", "x": x, "y": y, "reverse": reverse}


class McpServerTests(unittest.TestCase):
    def test_server_exposes_only_observe_and_craft(self) -> None:
        server = create_server(FakeActorService())

        tools = asyncio.run(server.get_tools())

        self.assertEqual(server.name, "Factorio Player MCP")
        self.assertEqual(set(tools), {"observe_actor", "observe_local", "craft", "wait", "move", "mine", "place", "rotate"})
        self.assertNotIn("run_lua", tools)
        self.assertNotIn("execute", tools)


if __name__ == "__main__":
    unittest.main()
