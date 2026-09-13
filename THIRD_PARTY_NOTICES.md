# Third-party notices

## FactoMCP

This repository's initial typed bridge and Factorio mod use the native-player
primitive selection from FactoMCP: player walking/mining state, native
`begin_crafting`, and `build_from_cursor`. The current imported implementation
contains only the initial native craft/observation slice and was rewritten to
call a fixed game-mod interface rather than expose generic Lua/RCON execution.

Source reviewed: `https://github.com/WidAmi/FactoMCP`, commit
`f223f5482801638fe0f930ab84a073b6e5ac8ca1`.

Copyright (c) 2026 David Mitchell

Licensed under the MIT License. The upstream license text is available at
`https://github.com/WidAmi/FactoMCP/blob/f223f5482801638fe0f930ab84a073b6e5ac8ca1/LICENSE`.
