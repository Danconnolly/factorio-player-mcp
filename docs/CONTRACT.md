# Public gameplay contract

Contract version: `1.0.0`

`factorio-player-mcp` is an agent-facing control layer for one named, dedicated,
connected Factorio player. It is not an administration, RCON, remote-Lua, or
evaluator interface.

The normative machine-readable policy is
[`../contracts/capability-manifest.v1.json`](../contracts/capability-manifest.v1.json).
The JSON schemas in `contracts/` define stable response payloads. A later MCP
implementation must not add public tools or fields without a contract-version
change and corresponding policy/test update.

## Actor identity and lifecycle

The bridge is configured with exactly one dedicated player name. Every action
must resolve that name to one connected `LuaPlayer` with a character.

The bridge rejects a request when the player is absent, disconnected, lacks a
character, or the configured identity is ambiguous. It never selects a player
by index, connection order, caller input, or a virtual `character` fallback.

Player death, respawn, save/load, and server restart are lifecycle events. They
must produce a defined action outcome and must not cause the bridge to retarget
a human player.

## Agent-visible tools

Only these typed gameplay actions are permitted:

- `move`: request ordinary tick-driven walking.
- `wait`: advance only through normal game ticks.
- `mine`: request normal player mining state against a reachable target.
- `craft`: enqueue/cancel a recipe through the player's native crafting queue.
- `place`: place an item from the player's cursor/inventory using normal build
  rules.
- `rotate`: rotate a reachable rotatable entity through normal player rules.
- `interact_inventory`: transfer a bounded item count to or from one reachable,
  compatible target inventory slot (`container`, `input`, `fuel`, or `output`).

The bridge validates all preconditions in the game-side component: actor state,
reach, target existence, collision, ownership where applicable, inventory,
recipe/technology availability, and game rule constraints. A validation failure
is an ordinary rejected action, never a host-side mutation.

## Forbidden capabilities

The public gameplay MCP must never expose arbitrary Lua, generic RCON command
execution, teleportation, direct entity creation/destruction/mining, item
spawning, forced research, caller-selected players, evaluator controls, or a
full-map state dump. Debug or recovery tooling with these capabilities must run
in a separate operator-only process and cannot share the agent's credentials or
MCP endpoint.

## Observations

Observations report deliberately bounded local state only:

- current tick and player position;
- player character state and inventory;
- charted/local entities and tiles;
- warnings relevant to the player's next legal actions.

Version 1 bounds a response to 256 entities and 4,096 tiles. Evaluator state,
scenario secrets, global maps, and unbounded caller-directed scans are excluded.

## Action results

Every action response uses
[`../contracts/action-result.v1.schema.json`](../contracts/action-result.v1.schema.json).
Action results contain the action ID/type, requested and resolved ticks,
outcome, reason, and any relevant deltas. The run log is assumed correct; the
control contract does not require receipt hashes, hash chaining, signatures, or
tamper-evident storage.

## Negative acceptance gates

Before an implementation is benchmark-valid, tests must prove that it rejects:

1. raw Lua/RCON and arbitrary remote-call targets;
2. a request to act as any player other than the configured dedicated actor;
3. teleport, item grants, forced research, direct mine/create/destroy, and
   ghost/admin placement;
4. observations beyond the bounded local/charted projection;
5. evaluator requests or evaluator-only state through the gameplay endpoint;
6. actions when the dedicated player is absent, disconnected, or lacks a
   character.

Passing a tool-level unit test is not sufficient. Each gate requires an
integration test against a disposable Factorio instance once the mod exists.
