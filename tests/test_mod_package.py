"""Tests for the reproducible Factorio mod archive."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[1]
PACKAGE_SCRIPT = REPOSITORY_ROOT / "scripts" / "package_mod.py"
MOD_INFO_PATH = REPOSITORY_ROOT / "factorio_mod" / "info.json"


class ModPackageTests(unittest.TestCase):
    def test_package_creates_versioned_recursive_archive_and_sha256(self) -> None:
        mod_info = json.loads(MOD_INFO_PATH.read_text(encoding="utf-8"))
        archive_stem = f"{mod_info['name']}_{mod_info['version']}"

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            completed = subprocess.run(
                ["python3", str(PACKAGE_SCRIPT), "--output-dir", str(output_directory)],
                check=True,
                capture_output=True,
                text=True,
            )

            archive_path = output_directory / f"{archive_stem}.zip"
            digest_path = output_directory / f"{archive_stem}.zip.sha256"
            self.assertTrue(archive_path.is_file(), completed.stdout + completed.stderr)
            self.assertTrue(digest_path.is_file(), completed.stdout + completed.stderr)
            self.assertEqual(
                digest_path.read_text(encoding="utf-8").strip(),
                f"{hashlib.sha256(archive_path.read_bytes()).hexdigest()}  {archive_path.name}",
            )

            with zipfile.ZipFile(archive_path) as archive:
                self.assertEqual(
                    archive.namelist(),
                    sorted(archive.namelist()),
                    "archive members must have deterministic ordering",
                )
                self.assertIn(f"{archive_stem}/info.json", archive.namelist())
                self.assertIn(f"{archive_stem}/control.lua", archive.namelist())
                self.assertIn(f"{archive_stem}/settings.lua", archive.namelist())
                self.assertIn(
                    f"{archive_stem}/locale/en/factorio-player-mcp.cfg",
                    archive.namelist(),
                )


if __name__ == "__main__":
    unittest.main()
