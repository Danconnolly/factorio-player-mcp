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
  for _, item in pairs(contents) do
    table.insert(items, {name = item.name, count = item.count, quality = item.quality})
  end
  table.sort(items, function(left, right) return left.name < right.name end)
  return items
end

local function action_response(action, status, reason)
  return response({
    status = status,
    action_id = action.id,
    action_type = action.action_type,
    requested_tick = action.requested_tick,
    resolved_tick = action.resolved_tick,
    target_tick = action.target_tick,
    reason = reason,
  })
end

script.on_event(defines.events.on_tick, function(event)
  local action = storage.active_action
  if action == nil then
    return
  end

  if event.tick >= action.target_tick then
    action.resolved_tick = event.tick
    storage.last_completed_action = action
    storage.active_action = nil
  end
end)

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

  start_wait = function(ticks)
    local player, rejection = actor_or_rejection()
    if player == nil then
      return rejection
    end
    if type(ticks) ~= "number" or ticks % 1 ~= 0 or ticks < 1 or ticks > 3600 then
      return response({status = "rejected", reason = "invalid_wait_ticks", tick = game.tick})
    end
    if storage.active_action ~= nil then
      return response({
        status = "rejected",
        reason = "action_in_progress",
        action_id = storage.active_action.id,
        tick = game.tick,
      })
    end

    storage.next_action_id = (storage.next_action_id or 0) + 1
    local action = {
      id = storage.next_action_id,
      action_type = "wait",
      requested_tick = game.tick,
      target_tick = game.tick + ticks,
    }
    storage.active_action = action
    return action_response(action, "accepted")
  end,

  action_status = function(action_id)
    if type(action_id) ~= "number" or action_id % 1 ~= 0 or action_id < 1 then
      return response({status = "rejected", reason = "invalid_action_id", tick = game.tick})
    end

    if storage.active_action ~= nil and storage.active_action.id == action_id then
      return action_response(storage.active_action, "accepted")
    end
    if storage.last_completed_action ~= nil and storage.last_completed_action.id == action_id then
      return action_response(storage.last_completed_action, "completed")
    end
    return response({status = "rejected", reason = "unknown_action", action_id = action_id, tick = game.tick})
  end,
})
