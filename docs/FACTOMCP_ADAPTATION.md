# FactoMCP adaptation boundary

FactoMCP was reviewed at commit
`f223f5482801638fe0f930ab84a073b6e5ac8ca1` under its MIT license.

## Imported now

- The choice to use a real connected player rather than an unattached virtual
  character.
- The native `LuaPlayer.begin_crafting` operation for hand crafting.
- The ordinary player position and main-inventory observation primitives.
- A Python command-builder shape for a host-side MCP bridge.

`factorio_mod/control.lua` deliberately exposes only two fixed methods during
this bootstrap: `observe_actor` and `craft`. Both resolve the configured player
name on every request and reject an absent, disconnected, or characterless
actor.

## Deliberately not imported

- `run_lua` and generic RCON command execution;
- `game.players[1]` actor lookup;
- teleportation, direct entity operations, ghost/admin actions, and player
  fallback behavior;
- unbounded scans and diagnostics;
- host-side polling/action handlers that use global tick-handler replacement;
- direct inventory/entity mutation paths.

## Important limitation

This is not an MCP server yet and is not benchmark-valid. The command builder
is an internal-only transport component, and the mod payloads are not public
MCP action results. Before an MCP endpoint is exposed, the bridge must add
public schema conformance, authenticated transport, serialized action lifecycle,
bounded observations, and disposable-Factorio integration tests.
