"""Contract tests for the public, agent-facing capability manifest."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).parents[1]
MANIFEST_PATH = REPOSITORY_ROOT / "contracts" / "capability-manifest.v1.json"
ACTION_RESULT_SCHEMA_PATH = REPOSITORY_ROOT / "contracts" / "action-result.v1.schema.json"
OBSERVATION_SCHEMA_PATH = REPOSITORY_ROOT / "contracts" / "observation.v1.schema.json"


class CapabilityManifestTests(unittest.TestCase):
    def load_manifest(self) -> dict[str, object]:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_manifest_defines_only_legal_player_actions(self) -> None:
        manifest = self.load_manifest()

        self.assertEqual(
            manifest["allowed_actions"],
            [
                "craft",
                "interact_inventory",
                "mine",
                "move",
                "place",
                "rotate",
                "wait",
            ],
        )
        self.assertEqual(
            manifest["prohibited_capabilities"],
            [
                "arbitrary_lua",
                "direct_entity_creation",
                "direct_entity_destruction",
                "direct_mining",
                "evaluator_access",
                "forced_research",
                "full_map_state_dump",
                "generic_rcon_command_execution",
                "item_spawning",
                "player_selection",
                "teleportation",
            ],
        )

    def test_manifest_requires_a_fixed_connected_player_identity(self) -> None:
        manifest = self.load_manifest()

        self.assertEqual(manifest["actor"]["selection"], "configured_dedicated_player_name")
        self.assertTrue(manifest["actor"]["must_be_connected"])
        self.assertTrue(manifest["actor"]["must_have_character"])
        self.assertFalse(manifest["actor"]["allow_index_fallback"])
        self.assertFalse(manifest["actor"]["allow_caller_selected_player"])

    def test_manifest_bounds_agent_visible_observations(self) -> None:
        manifest = self.load_manifest()

        self.assertEqual(manifest["observations"]["world_scope"], "charted_local_area")
        self.assertEqual(manifest["observations"]["max_entities_per_response"], 256)
        self.assertEqual(manifest["observations"]["max_tiles_per_response"], 4096)
        self.assertNotIn("evaluator", manifest["observations"]["agent_visible_fields"])

    def test_manifest_requires_receipts_for_mutating_actions(self) -> None:
        manifest = self.load_manifest()

        self.assertEqual(
            manifest["mutation_receipt"],
            {
                "required_fields": [
                    "action_id",
                    "action_type",
                    "requested_tick",
                    "resolved_tick",
                    "outcome",
                    "reason",
                    "previous_receipt_hash",
                    "receipt_hash",
                ],
                "hash_chain": "sha256",
            },
        )

    def test_public_response_schemas_are_versioned_json_schemas(self) -> None:
        for schema_path in (ACTION_RESULT_SCHEMA_PATH, OBSERVATION_SCHEMA_PATH):
            schema = json.loads(schema_path.read_text(encoding="utf-8"))

            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertTrue(schema["$id"].startswith("https://factorio-player-mcp.dev/contracts/"))
            self.assertIn("contract_version", schema["properties"])


if __name__ == "__main__":
    unittest.main()
