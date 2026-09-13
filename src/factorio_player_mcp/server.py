"""stdio MCP server exposing the narrow typed Factorio action surface."""

from __future__ import annotations

import os
from typing import Protocol

from fastmcp import FastMCP

from factorio_player_mcp.rcon import FactorioRconSender
from factorio_player_mcp.service import ActorService


class ActorOperations(Protocol):
    def observe_actor(self) -> dict[str, object]: ...

    def observe_local(self, *, radius: int) -> dict[str, object]: ...

    def craft(self, *, recipe: str, count: int) -> dict[str, object]: ...

    def wait(self, *, ticks: int) -> dict[str, object]: ...

    def move(self, *, x: float, y: float) -> dict[str, object]: ...

    def mine(self, *, x: float, y: float, count: int) -> dict[str, object]: ...

    def place(self, *, item: str, x: float, y: float, direction: str) -> dict[str, object]: ...

    def rotate(self, *, x: float, y: float, reverse: bool = False) -> dict[str, object]: ...


def create_server(service: ActorOperations) -> FastMCP:
    """Create the public MCP server with only the currently implemented tools."""

    mcp = FastMCP("Factorio Player MCP")

    @mcp.tool
    def observe_actor() -> dict[str, object]:
        """Return bounded state for the configured dedicated player."""
        return service.observe_actor()

    @mcp.tool
    def observe_local(radius: int = 10) -> dict[str, object]:
        """Return chart-bounded entities within a small radius of the dedicated player."""
        return service.observe_local(radius=radius)

    @mcp.tool
    def craft(recipe: str, count: int = 1) -> dict[str, object]:
        """Queue an available recipe through the dedicated player's native craft queue."""
        return service.craft(recipe=recipe, count=count)

    @mcp.tool
    def wait(ticks: int) -> dict[str, object]:
        """Wait for a bounded number of normal Factorio game ticks."""
        return service.wait(ticks=ticks)

    @mcp.tool
    def move(x: float, y: float) -> dict[str, object]:
        """Walk the dedicated player toward a target using normal movement state."""
        return service.move(x=x, y=y)

    @mcp.tool
    def mine(x: float, y: float, count: int = 1) -> dict[str, object]:
        """Mine a reachable target through the dedicated player's normal mining state."""
        return service.mine(x=x, y=y, count=count)

    @mcp.tool
    def place(item: str, x: float, y: float, direction: str = "north") -> dict[str, object]:
        """Place one inventory item through the dedicated player's normal build action."""
        return service.place(item=item, x=x, y=y, direction=direction)

    @mcp.tool
    def rotate(x: float, y: float, reverse: bool = False) -> dict[str, object]:
        """Rotate one reachable rotatable entity through the dedicated player's normal action."""
        return service.rotate(x=x, y=y, reverse=reverse)

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
