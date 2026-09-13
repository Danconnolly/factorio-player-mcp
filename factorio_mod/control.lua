-- Copyright (c) 2026 Daniel Connolly
-- SPDX-License-Identifier: MIT
--
-- Native-player primitive selection informed by FactoMCP (David Mitchell),
-- used under the MIT license. See THIRD_PARTY_NOTICES.md.

local function response(payload)
  return helpers.table_to_json(payload)
end

local function configured_actor()
  local configured_dedicated_player_name = settings.global["factorio-player-mcp-actor-name"].value
  if configured_dedicated_player_name == nil or configured_dedicated_player_name == "" then
    return nil, "dedicated_player_not_configured"
  end

  local player = game.get_player(configured_dedicated_player_name)
  if player == nil then
    return nil, "dedicated_player_not_found"
  end
  if not player.connected then
    return nil, "dedicated_player_not_connected"
  end
  if player.character == nil or not player.character.valid then
    return nil, "dedicated_player_has_no_character"
  end

  return player, nil
end

local function actor_or_rejection()
  local player, reason = configured_actor()
  if player == nil then
    return nil, response({status = "rejected", reason = reason, tick = game.tick})
  end
  return player, nil
end

local function inventory_contents(player)
  local inventory = player.get_main_inventory()
  local contents = inventory.get_contents()
  local items = {}
  for name, count in pairs(contents) do
    table.insert(items, {name = name, count = count})
  end
  table.sort(items, function(left, right) return left.name < right.name end)
  return items
end

remote.add_interface("factorio_player_mcp", {
  observe_actor = function()
    local player, rejection = actor_or_rejection()
    if player == nil then
      return rejection
    end

    return response({
      status = "completed",
      tick = game.tick,
      player_position = {x = player.position.x, y = player.position.y},
      inventory = inventory_contents(player),
    })
  end,

  craft = function(recipe_name, count)
    local player, rejection = actor_or_rejection()
    if player == nil then
      return rejection
    end
    if type(recipe_name) ~= "string" or type(count) ~= "number" or count % 1 ~= 0 or count <= 0 then
      return response({status = "rejected", reason = "invalid_craft_request", tick = game.tick})
    end

    local recipe = player.force.recipes[recipe_name]
    if recipe == nil or not recipe.enabled then
      return response({status = "rejected", reason = "recipe_not_available", tick = game.tick})
    end

    local queued = player.begin_crafting({recipe = recipe_name, count = count})
    return response({
      status = "completed",
      tick = game.tick,
      requested_recipe = recipe_name,
      requested_count = count,
      queued_count = queued,
      crafting_queue_size = player.crafting_queue_size,
    })
  end,
})
