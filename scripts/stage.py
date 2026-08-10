#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_native_archive(target_dir: pathlib.Path, windows: bool) -> pathlib.Path:
    names = ["duckdb.lib"] if windows else ["libduckdb.a"]
    candidates: list[pathlib.Path] = []
    for name in names:
        for path in target_dir.rglob(name):
            normalized = path.as_posix()
            if "libduckdb-sys-" in normalized and path.parent.name == "out":
                candidates.append(path)
    candidates = sorted(set(candidates))
    if len(candidates) != 1:
        rendered = "\n".join(f"  - {candidate}" for candidate in candidates) or "  (none)"
        raise SystemExit(
            f"expected exactly one bundled DuckDB archive below {target_dir}, found {len(candidates)}:\n{rendered}"
        )
    return candidates[0]


def write_pkg_config(stage: pathlib.Path, duckdb_version: str, link_libraries: list[str]) -> None:
    private_libs = " ".join(f"-l{library}" for library in link_libraries)
    pkgconfig = stage / "lib" / "pkgconfig"
    pkgconfig.mkdir(parents=True, exist_ok=True)
    (pkgconfig / "duckdb.pc").write_text(
        "\n".join(
            [
                "prefix=${pcfiledir}/../..",
                "exec_prefix=${prefix}",
                "libdir=${prefix}/lib",
                "includedir=${prefix}/include",
                "",
                "Name: DuckDB",
                "Description: DuckDB static library prepared for AnyDatas",
                f"Version: {duckdb_version}",
                "Libs: -L${libdir} -lduckdb_static",
                f"Libs.private: {private_libs}",
                "Cflags: -I${includedir}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-dir", required=True, type=pathlib.Path)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    args = parser.parse_args()

    config = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
    target = next(
        (target for target in config["targets"] if target["platform"] == args.platform),
        None,
    )
    if target is None:
        raise SystemExit(f"unknown platform {args.platform!r}")

    windows = args.platform.startswith("windows-")
    archive = find_native_archive(args.target_dir.resolve(), windows)
    out_dir = archive.parent
    source_include = out_dir / "duckdb" / "src" / "include"
    duckdb_h = source_include / "duckdb.h"
    duckdb_hpp = source_include / "duckdb.hpp"
    if not duckdb_h.is_file() or not duckdb_hpp.is_file():
        raise SystemExit(f"DuckDB headers were not found below {source_include}")

    stage = args.output.resolve()
    if stage.exists():
        shutil.rmtree(stage)
    (stage / "include").mkdir(parents=True)
    (stage / "lib").mkdir(parents=True)

    library_name = target["library"]
    staged_library = stage / "lib" / library_name
    shutil.copy2(archive, staged_library)
    shutil.copy2(duckdb_h, stage / "include" / "duckdb.h")
    shutil.copy2(duckdb_hpp, stage / "include" / "duckdb.hpp")
    shutil.copy2(ROOT / "licenses" / "DuckDB-LICENSE", stage / "LICENSE-DuckDB")

    if not windows:
        write_pkg_config(stage, config["duckdbVersion"], target["linkLibraries"])

    metadata = {
        "schemaVersion": 1,
        "duckdbVersion": config["duckdbVersion"],
        "duckdbRsVersion": config["duckdbRsVersion"],
        "buildRevision": config["buildRevision"],
        "releaseTag": config["releaseTag"],
        "platform": target["platform"],
        "targetTriple": target["targetTriple"],
        "library": library_name,
        "librarySha256": sha256(staged_library),
        "linkLibraries": target["linkLibraries"],
        "windowsCrt": config["windowsCrt"] if windows else None,
        "duckdbRsFeatures": config["duckdbRsFeatures"],
        "nativeFeatures": config["nativeFeatures"],
        "source": "duckdb-rs bundled native build",
    }
    (stage / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"staged {archive} -> {staged_library}")
    print(f"library sha256: {metadata['librarySha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
