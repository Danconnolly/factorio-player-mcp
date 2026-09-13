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

local function is_charted_for_player(player, position)
  local chunk_position = {x = math.floor(position.x / 32), y = math.floor(position.y / 32)}
  return player.force.is_chunk_charted(player.surface, chunk_position)
end

local function direction_from_name(direction_name)
  local directions = {
    north = defines.direction.north,
    northeast = defines.direction.northeast,
    east = defines.direction.east,
    southeast = defines.direction.southeast,
    south = defines.direction.south,
    southwest = defines.direction.southwest,
    west = defines.direction.west,
    northwest = defines.direction.northwest,
  }
  return directions[direction_name]
end

local function local_entities(player, radius)
  local position = player.position
  local area = {{position.x - radius, position.y - radius}, {position.x + radius, position.y + radius}}
  local entities = player.surface.find_entities_filtered({area = area})
  local result = {}
  for _, entity in ipairs(entities) do
    if #result >= 256 then
      break
    end
    if entity.valid and entity.type ~= "character" and is_charted_for_player(player, entity.position) then
      table.insert(result, {
        name = entity.name,
        type = entity.type,
        position = {x = entity.position.x, y = entity.position.y},
      })
    end
  end
  table.sort(result, function(left, right)
    if left.name ~= right.name then return left.name < right.name end
    if left.position.x ~= right.position.x then return left.position.x < right.position.x end
    return left.position.y < right.position.y
  end)
  return result
end

local function action_response(action, status, reason)
  return response({
    status = status or action.status,
    action_id = action.id,
    action_type = action.action_type,
    requested_tick = action.requested_tick,
    resolved_tick = action.resolved_tick,
    target_tick = action.target_tick,
    target_position = action.target_position,
    mined_count = action.mined_count,
    reason = reason or action.reason,
  })
end

local function stop_player_actions(player)
  player.walking_state = {walking = false, direction = defines.direction.south}
  player.mining_state = {mining = false}
end

local function finish_action(action, status, tick, reason, player)
  if player ~= nil then
    stop_player_actions(player)
  end
  action.status = status
  action.resolved_tick = tick
  action.reason = reason
  storage.last_finished_action = action
  storage.active_action = nil
end

local function move_direction(dx, dy)
  local index = math.floor(((math.deg(math.atan2(dy, dx)) + 360) % 360 + 22.5) / 45) % 8
  local directions = {
    [0] = defines.direction.east,
    [1] = defines.direction.southeast,
    [2] = defines.direction.south,
    [3] = defines.direction.southwest,
    [4] = defines.direction.west,
    [5] = defines.direction.northwest,
    [6] = defines.direction.north,
    [7] = defines.direction.northeast,
  }
  return directions[index]
end

local function advance_move(action, event)
  local player, reason = configured_actor()
  if player == nil then
    finish_action(action, "failed", event.tick, reason, nil)
    return
  end

  local dx = action.target_position.x - player.position.x
  local dy = action.target_position.y - player.position.y
  local distance = math.sqrt(dx * dx + dy * dy)
  if distance <= 0.75 then
    finish_action(action, "completed", event.tick, nil, player)
    return
  end

  if action.last_progress_tick == nil or event.tick - action.last_progress_tick >= 60 then
    if action.last_distance ~= nil and distance >= action.last_distance - 0.1 then
      action.stalled_checks = (action.stalled_checks or 0) + 1
    else
      action.stalled_checks = 0
    end
    action.last_distance = distance
    action.last_progress_tick = event.tick
  end
  if action.stalled_checks >= 3 then
    finish_action(action, "failed", event.tick, "movement_stalled", player)
    return
  end

  player.walking_state = {walking = true, direction = move_direction(dx, dy)}
end

local function selected_mine_target(player, action)
  player.update_selected_entity(action.target_position)
  local target = player.selected
  if target == nil or not target.valid or not target.minable then
    return nil
  end
  if target.name ~= action.target_name or not player.can_reach_entity(target) then
    return nil
  end
  return target
end

local function advance_mine(action, event)
  local player, reason = configured_actor()
  if player == nil then
    finish_action(action, "failed", event.tick, reason, nil)
    return
  end

  local target = selected_mine_target(player, action)
  if target == nil then
    finish_action(action, "failed", event.tick, "mine_target_unavailable", player)
    return
  end

  player.mining_state = {mining = true, position = target.position}
  local progress = player.character_mining_progress
  if progress < 0.01 then
    action.no_progress_ticks = (action.no_progress_ticks or 0) + 1
  else
    action.no_progress_ticks = 0
  end
  if action.no_progress_ticks > 120 then
    finish_action(action, "failed", event.tick, "mining_no_progress", player)
    return
  end
  action.last_mining_progress = progress
end

script.on_event(defines.events.on_player_mined_entity, function(event)
  local action = storage.active_action
  if action == nil or action.action_type ~= "mine" then
    return
  end

  local player, reason = configured_actor()
  if player == nil then
    finish_action(action, "failed", event.tick, reason, nil)
    return
  end
  if event.player_index ~= player.index or event.entity.name ~= action.target_name then
    return
  end

  action.mined_count = action.mined_count + 1
  if action.mined_count >= action.requested_count then
    finish_action(action, "completed", event.tick, nil, player)
  end
end)

script.on_event(defines.events.on_tick, function(event)
  local action = storage.active_action
  if action == nil then
    return
  end

  if action.action_type == "wait" and event.tick >= action.target_tick then
    finish_action(action, "completed", event.tick)
  elseif action.action_type == "move" then
    advance_move(action, event)
  elseif action.action_type == "mine" then
    advance_mine(action, event)
  else
    finish_action(action, "failed", event.tick, "unknown_action_type")
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

  observe_local = function(radius)
    local player, rejection = actor_or_rejection()
    if player == nil then
      return rejection
    end
    if type(radius) ~= "number" or radius % 1 ~= 0 or radius < 1 or radius > 20 then
      return response({status = "rejected", reason = "invalid_observation_radius", tick = game.tick})
    end
    return response({
      status = "completed",
      tick = game.tick,
      player_position = {x = player.position.x, y = player.position.y},
      radius = radius,
      local_entities = local_entities(player, radius),
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

  place = function(item_name, x, y, direction_name)
    local player, rejection = actor_or_rejection()
    if player == nil then
      return rejection
    end
    if type(item_name) ~= "string" or type(x) ~= "number" or type(y) ~= "number"
        or math.abs(x) > 1000000 or math.abs(y) > 1000000 then
      return response({status = "rejected", reason = "invalid_placement_request", tick = game.tick})
    end
    local direction = direction_from_name(direction_name)
    if direction == nil then
      return response({status = "rejected", reason = "invalid_placement_direction", tick = game.tick})
    end
    if storage.active_action ~= nil then
      return response({
        status = "rejected",
        reason = "action_in_progress",
        action_id = storage.active_action.id,
        tick = game.tick,
      })
    end

    local position = {x = x, y = y}
    if not is_charted_for_player(player, position) then
      return response({status = "rejected", reason = "placement_not_charted", tick = game.tick})
    end
    local dx = player.position.x - x
    local dy = player.position.y - y
    if math.sqrt(dx * dx + dy * dy) > player.build_distance then
      return response({status = "rejected", reason = "placement_out_of_reach", tick = game.tick})
    end

    local inventory = player.get_main_inventory()
    local slot = inventory.find_item_stack(item_name)
    if slot == nil then
      return response({status = "rejected", reason = "placement_item_unavailable", tick = game.tick})
    end

    local before_count = inventory.get_item_count(item_name)
    player.cursor_stack.swap_stack(slot)
    local can_build = player.can_build_from_cursor({position = position, direction = direction})
    if can_build then
      player.build_from_cursor({position = position, direction = direction})
    end
    player.cursor_stack.swap_stack(slot)
    local placed = can_build and inventory.get_item_count(item_name) == before_count - 1

    if not placed then
      return response({status = "rejected", reason = "placement_not_allowed", tick = game.tick})
    end
    return response({
      status = "completed",
      tick = game.tick,
      item = item_name,
      position = position,
      direction = direction_name,
    })
  end,

  rotate = function(x, y, reverse)
    local player, rejection = actor_or_rejection()
    if player == nil then
      return rejection
    end
    if type(x) ~= "number" or type(y) ~= "number" or type(reverse) ~= "boolean"
        or math.abs(x) > 1000000 or math.abs(y) > 1000000 then
      return response({status = "rejected", reason = "invalid_rotate_request", tick = game.tick})
    end
    if storage.active_action ~= nil then
      return response({
        status = "rejected",
        reason = "action_in_progress",
        action_id = storage.active_action.id,
        tick = game.tick,
      })
    end
    local position = {x = x, y = y}
    if not is_charted_for_player(player, position) then
      return response({status = "rejected", reason = "rotate_target_not_charted", tick = game.tick})
    end

    player.update_selected_entity(position)
    local target = player.selected
    if target == nil or not target.valid or not target.rotatable or not player.can_reach_entity(target) then
      return response({status = "rejected", reason = "rotate_target_unavailable", tick = game.tick})
    end
    if not target.rotate({reverse = reverse, by_player = true}) then
      return response({status = "rejected", reason = "rotation_not_allowed", tick = game.tick})
    end
    return response({
      status = "completed",
      tick = game.tick,
      target_name = target.name,
      target_position = {x = target.position.x, y = target.position.y},
      reverse = reverse,
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

  start_move = function(x, y)
    local player, rejection = actor_or_rejection()
    if player == nil then
      return rejection
    end
    if type(x) ~= "number" or type(y) ~= "number" or math.abs(x) > 1000000 or math.abs(y) > 1000000 then
      return response({status = "rejected", reason = "invalid_move_target", tick = game.tick})
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
      action_type = "move",
      requested_tick = game.tick,
      target_position = {x = x, y = y},
    }
    storage.active_action = action
    return action_response(action, "accepted")
  end,

  start_mine = function(x, y, count)
    local player, rejection = actor_or_rejection()
    if player == nil then
      return rejection
    end
    if type(x) ~= "number" or type(y) ~= "number" or math.abs(x) > 1000000 or math.abs(y) > 1000000
        or type(count) ~= "number" or count % 1 ~= 0 or count < 1 or count > 100 then
      return response({status = "rejected", reason = "invalid_mine_request", tick = game.tick})
    end
    if storage.active_action ~= nil then
      return response({
        status = "rejected",
        reason = "action_in_progress",
        action_id = storage.active_action.id,
        tick = game.tick,
      })
    end

    player.update_selected_entity({x = x, y = y})
    local target = player.selected
    if target == nil or not target.valid or not target.minable or not player.can_reach_entity(target) then
      return response({status = "rejected", reason = "mine_target_unavailable", tick = game.tick})
    end

    storage.next_action_id = (storage.next_action_id or 0) + 1
    local action = {
      id = storage.next_action_id,
      action_type = "mine",
      requested_tick = game.tick,
      target_position = {x = target.position.x, y = target.position.y},
      target_name = target.name,
      requested_count = count,
      mined_count = 0,
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
    if storage.last_finished_action ~= nil and storage.last_finished_action.id == action_id then
      return action_response(storage.last_finished_action)
    end
    return response({status = "rejected", reason = "unknown_action", action_id = action_id, tick = game.tick})
  end,
})
