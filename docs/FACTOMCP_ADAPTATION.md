# FactoMCP adaptation boundary

FactoMCP was reviewed at commit
`f223f5482801638fe0f930ab84a073b6e5ac8ca1` under its MIT license.

## Imported now

- The choice to use a real connected player rather than an unattached virtual
  character.
- The native `LuaPlayer.begin_crafting` operation for hand crafting.
- The ordinary player position and main-inventory observation primitives.
- A Python command-builder shape for a host-side MCP bridge.

`factorio_mod/control.lua` deliberately exposes fixed methods for actor
observation, native crafting, a serialized bounded wait action, and normal
tick-driven movement. Actor-facing methods resolve the configured player name
on every request and reject an absent, disconnected, or characterless actor.

## Deliberately not imported

- `run_lua` and generic RCON command execution;
- `game.players[1]` actor lookup;
- teleportation, direct entity operations, ghost/admin actions, and player
  fallback behavior;
- unbounded scans and diagnostics;
- host-side polling/action handlers that use global tick-handler replacement;
- direct inventory/entity mutation paths.

## Important limitation

This is an MCP bootstrap, not a benchmark-valid controller. The command builder
is an internal-only transport component, and the mod payloads are not yet public
MCP action results. Before benchmark use, the bridge still needs public schema
conformance, authenticated transport, cancellation semantics, richer bounded
observations, and disposable-Factorio integration tests.
