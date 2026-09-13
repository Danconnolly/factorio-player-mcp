"""Internal RCON transport for the fixed Factorio mod interface."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol


class RconClient(Protocol):
    def send_command(self, command: str) -> str: ...


RconClientFactory = Callable[[str, int, str], RconClient]


def _default_client_factory(host: str, port: int, password: str) -> RconClient:
    import factorio_rcon

    return factorio_rcon.RCONClient(host, port, password)


class FactorioRconSender:
    """Lazily connect to Factorio and send commands built by trusted code only."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        password: str,
        client_factory: RconClientFactory = _default_client_factory,
    ) -> None:
        if not host:
            raise ValueError("host must not be empty")
        if not 1 <= port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        if not password:
            raise ValueError("password must not be empty")

        self._host = host
        self._port = port
        self._password = password
        self._client_factory = client_factory
        self._client: RconClient | None = None

    def send_command(self, command: str) -> str:
        if self._client is None:
            self._client = self._client_factory(self._host, self._port, self._password)
        return self._client.send_command(command) or ""
