# Versioned contract artifacts

- `capability-manifest.v1.json`: normative allow-list, deny-list, actor policy,
  and observation boundary.
- `action-result.v1.schema.json`: agent-visible result of a typed action.
- `observation.v1.schema.json`: bounded agent-visible observation projection.

Breaking changes create a new versioned file. Do not silently expand an
allow-list, observation field, response bound, or actor-selection rule.
