"""stdio MCP server exposing the narrow typed Factorio action surface."""

from __future__ import annotations

import os
from typing import Protocol

from fastmcp import FastMCP

from factorio_player_mcp.rcon import FactorioRconSender
from factorio_player_mcp.service import ActorService


class ActorOperations(Protocol):
    def observe_actor(self) -> dict[str, object]: ...

    def craft(self, *, recipe: str, count: int) -> dict[str, object]: ...


def create_server(service: ActorOperations) -> FastMCP:
    """Create the public MCP server with only the currently implemented tools."""

    mcp = FastMCP("Factorio Player MCP")

    @mcp.tool
    def observe_actor() -> dict[str, object]:
        """Return bounded state for the configured dedicated player."""
        return service.observe_actor()

    @mcp.tool
    def craft(recipe: str, count: int = 1) -> dict[str, object]:
        """Queue an available recipe through the dedicated player's native craft queue."""
        return service.craft(recipe=recipe, count=count)

    return mcp


def create_default_service() -> ActorService:
    """Create the internal RCON-backed service from explicit runtime settings."""

    host = os.environ.get("FACTORIO_RCON_HOST", "127.0.0.1")
    port = int(os.environ.get("FACTORIO_RCON_PORT", "25575"))
    password = os.environ.get("FACTORIO_RCON_PASSWORD", "")
    return ActorService(FactorioRconSender(host=host, port=port, password=password))


def main() -> None:
    create_server(create_default_service()).run()


if __name__ == "__main__":
    main()
