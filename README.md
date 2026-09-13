# factorio-player-mcp

An MCP control layer for one dedicated, connected Factorio player.

The project measures gameplay through a constrained interface; it is not a
general RCON or Lua automation server. The agent-facing API will expose only
typed, legal player actions and bounded local observations. It will not expose
arbitrary Lua/RCON, teleportation, item spawning, direct entity mutation,
forced research, evaluator state, or full-map dumps.

## Current status

The version 1 contract is defined. The repository contains an initial,
internal-only Factorio mod bootstrap for bounded actor observation and native
crafting. It is not an MCP server yet and must not be used for benchmark runs.

- Public policy: [`docs/CONTRACT.md`](docs/CONTRACT.md)
- Machine-readable capability manifest:
  [`contracts/capability-manifest.v1.json`](contracts/capability-manifest.v1.json)
- Response schemas: [`contracts/`](contracts/)
- FactoMCP adaptation boundary:
  [`docs/FACTOMCP_ADAPTATION.md`](docs/FACTOMCP_ADAPTATION.md)

## Development checks

The contract checks use only the Python standard library:

    python3 -m unittest discover -s tests -v

These tests guard the public allow-list, forbidden capabilities, dedicated
player identity policy, bounded observations, action-result fields, and
versioned response schemas.
