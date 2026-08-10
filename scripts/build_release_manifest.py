#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST_NAME = "duckdb-prebuilt-manifest.json"
SUMS_NAME = "SHA256SUMS"


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_metadata(archive: pathlib.Path) -> dict:
    with zipfile.ZipFile(archive) as handle:
        try:
            raw = handle.read("metadata.json")
        except KeyError as exc:
            raise SystemExit(f"{archive.name} does not contain metadata.json") from exc
    return json.loads(raw.decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True, type=pathlib.Path)
    args = parser.parse_args()

    directory = args.directory.resolve()
    config = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
    expected_targets = {target["platform"]: target for target in config["targets"]}
    archives = sorted(directory.glob("duckdb-static-*.zip"))
    if len(archives) != len(expected_targets):
        raise SystemExit(
            f"expected {len(expected_targets)} platform archives, found {len(archives)} in {directory}"
        )

    assets = []
    seen_platforms: set[str] = set()
    for archive in archives:
        metadata = read_metadata(archive)
        platform = metadata["platform"]
        if platform in seen_platforms:
            raise SystemExit(f"duplicate platform archive: {platform}")
        if platform not in expected_targets:
            raise SystemExit(f"unexpected platform archive: {platform}")
        seen_platforms.add(platform)

        expected = expected_targets[platform]
        for key, expected_value in (
            ("duckdbVersion", config["duckdbVersion"]),
            ("duckdbRsVersion", config["duckdbRsVersion"]),
            ("buildRevision", config["buildRevision"]),
            ("releaseTag", config["releaseTag"]),
            ("targetTriple", expected["targetTriple"]),
            ("library", expected["library"]),
            ("linkLibraries", expected["linkLibraries"]),
        ):
            if metadata.get(key) != expected_value:
                raise SystemExit(
                    f"{archive.name}: metadata {key} mismatch: "
                    f"expected {expected_value!r}, got {metadata.get(key)!r}"
                )
        if archive.name != expected["archive"]:
            raise SystemExit(
                f"{platform}: expected archive name {expected['archive']!r}, got {archive.name!r}"
            )

        assets.append(
            {
                "platform": platform,
                "targetTriple": metadata["targetTriple"],
                "fileName": archive.name,
                "size": archive.stat().st_size,
                "sha256": sha256(archive),
                "library": metadata["library"],
                "librarySha256": metadata["librarySha256"],
                "linkLibraries": metadata["linkLibraries"],
                "windowsCrt": metadata.get("windowsCrt"),
            }
        )

    if seen_platforms != set(expected_targets):
        missing = sorted(set(expected_targets) - seen_platforms)
        raise SystemExit(f"missing platform archives: {missing}")

    manifest = {
        "schemaVersion": 1,
        "releaseTag": config["releaseTag"],
        "duckdbVersion": config["duckdbVersion"],
        "duckdbRsVersion": config["duckdbRsVersion"],
        "rustToolchain": config["rustToolchain"],
        "buildRevision": config["buildRevision"],
        "duckdbRsFeatures": config["duckdbRsFeatures"],
        "nativeFeatures": config["nativeFeatures"],
        "assets": sorted(assets, key=lambda item: item["platform"]),
    }
    manifest_path = directory / MANIFEST_NAME
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    checksum_targets = archives + [manifest_path]
    sums_path = directory / SUMS_NAME
    sums_path.write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in checksum_targets),
        encoding="utf-8",
    )

    print(f"wrote {manifest_path}")
    print(f"wrote {sums_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
