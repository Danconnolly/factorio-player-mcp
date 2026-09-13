"""Tests for the agent-facing MCP tool allow-list."""

from __future__ import annotations

import asyncio
import unittest

from factorio_player_mcp.server import create_server


class FakeActorService:
    def observe_actor(self) -> dict[str, object]:
        return {"status": "completed"}

    def craft(self, *, recipe: str, count: int) -> dict[str, object]:
        return {"status": "completed", "recipe": recipe, "count": count}

    def wait(self, *, ticks: int) -> dict[str, object]:
        return {"status": "completed", "ticks": ticks}


class McpServerTests(unittest.TestCase):
    def test_server_exposes_only_observe_and_craft(self) -> None:
        server = create_server(FakeActorService())

        tools = asyncio.run(server.get_tools())

        self.assertEqual(server.name, "Factorio Player MCP")
        self.assertEqual(set(tools), {"observe_actor", "craft", "wait"})
        self.assertNotIn("run_lua", tools)
        self.assertNotIn("execute", tools)


if __name__ == "__main__":
    unittest.main()
