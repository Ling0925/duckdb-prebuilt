#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def dependency_version(path: pathlib.Path) -> tuple[str, set[str]]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    dependency = data["dependencies"]["duckdb"]
    if isinstance(dependency, str):
        return dependency, set()
    return dependency["version"], set(dependency.get("features", []))


def main() -> int:
    config = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
    duckdb_version = config["duckdbVersion"]
    duckdb_rs_version = config["duckdbRsVersion"]
    revision = config["buildRevision"]

    expected_tag = f"duckdb-v{duckdb_version}-anydatas.{revision}"
    if config["releaseTag"] != expected_tag:
        raise SystemExit(
            f"releaseTag mismatch: expected {expected_tag!r}, got {config['releaseTag']!r}"
        )

    expected_dependency = f"={duckdb_rs_version}"
    builder_version, builder_features = dependency_version(ROOT / "builder" / "Cargo.toml")
    smoke_version, smoke_features = dependency_version(ROOT / "smoke" / "Cargo.toml")

    if builder_version != expected_dependency:
        raise SystemExit(
            f"builder duckdb version mismatch: expected {expected_dependency}, got {builder_version}"
        )
    if smoke_version != expected_dependency:
        raise SystemExit(
            f"smoke duckdb version mismatch: expected {expected_dependency}, got {smoke_version}"
        )

    configured_features = set(config["duckdbRsFeatures"])
    if builder_features != configured_features:
        raise SystemExit(
            "builder feature mismatch: "
            f"expected {sorted(configured_features)}, got {sorted(builder_features)}"
        )
    if "bundled" in smoke_features:
        raise SystemExit("smoke crate must never enable the duckdb-rs bundled feature")
    if smoke_features != configured_features - {"bundled"}:
        raise SystemExit(
            "smoke feature mismatch: "
            f"expected {sorted(configured_features - {'bundled'})}, got {sorted(smoke_features)}"
        )

    targets = config["targets"]
    platforms = [target["platform"] for target in targets]
    archives = [target["archive"] for target in targets]
    triples = [target["targetTriple"] for target in targets]
    for name, values in (("platform", platforms), ("archive", archives), ("targetTriple", triples)):
        if len(values) != len(set(values)):
            raise SystemExit(f"duplicate {name} entries in version.json")

    for target in targets:
        if duckdb_version not in target["archive"]:
            raise SystemExit(
                f"archive {target['archive']!r} does not contain DuckDB version {duckdb_version}"
            )

    print(
        json.dumps(
            {
                "releaseTag": expected_tag,
                "duckdbVersion": duckdb_version,
                "duckdbRsVersion": duckdb_rs_version,
                "rustToolchain": config["rustToolchain"],
                "targets": platforms,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
