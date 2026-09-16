#!/usr/bin/env python3
"""Create a deterministic, installable Factorio mod archive and SHA-256 sidecar."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[1]
MOD_DIRECTORY = REPOSITORY_ROOT / "factorio_mod"
ARCHIVE_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def package_mod(output_directory: Path) -> tuple[Path, Path]:
    """Package the full mod tree beneath Factorio's required versioned root."""
    mod_info = json.loads((MOD_DIRECTORY / "info.json").read_text(encoding="utf-8"))
    archive_stem = f"{mod_info['name']}_{mod_info['version']}"
    output_directory.mkdir(parents=True, exist_ok=True)
    archive_path = output_directory / f"{archive_stem}.zip"

    source_files = sorted(path for path in MOD_DIRECTORY.rglob("*") if path.is_file())
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source_path in source_files:
            archive_member = Path(archive_stem) / source_path.relative_to(MOD_DIRECTORY)
            metadata = zipfile.ZipInfo(str(archive_member), date_time=ARCHIVE_TIMESTAMP)
            metadata.compress_type = zipfile.ZIP_DEFLATED
            metadata.external_attr = 0o100644 << 16
            archive.writestr(metadata, source_path.read_bytes())

    digest_path = output_directory / f"{archive_path.name}.sha256"
    digest_path.write_text(
        f"{hashlib.sha256(archive_path.read_bytes()).hexdigest()}  {archive_path.name}\n",
        encoding="utf-8",
    )
    return archive_path, digest_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for archive and digest")
    arguments = parser.parse_args()
    archive_path, digest_path = package_mod(arguments.output_dir)
    print(archive_path)
    print(digest_path)


if __name__ == "__main__":
    main()
