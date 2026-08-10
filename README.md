# duckdb-prebuilt

Precompiled DuckDB static libraries for [AnyDatas](https://github.com/Ling0925/AnyDatas).

This repository exists to move the expensive native DuckDB C++ compilation out of the normal AnyDatas CI and release pipelines. A DuckDB native library is compiled once per supported platform and DuckDB version, verified through the non-`bundled` `duckdb-rs` path, and published as immutable versioned release assets.

## Current pin

- DuckDB: `1.5.4`
- `duckdb-rs`: `1.10504.0`
- Rust toolchain: `1.97.0`
- Build revision: `1`
- Release tag: `duckdb-v1.5.4-anydatas.1`

The builder intentionally uses the same `duckdb-rs` `bundled` feature set that AnyDatas currently uses. This keeps the native library aligned with AnyDatas instead of relying on DuckDB's upstream multi-archive `static-libs-*` packages.

## Supported assets

A release produces:

- `duckdb-static-v1.5.4-linux-x64.zip`
- `duckdb-static-v1.5.4-windows-x64-msvc-static-crt.zip`
- `duckdb-static-v1.5.4-macos-arm64.zip`
- `duckdb-static-v1.5.4-macos-x64.zip`
- `duckdb-prebuilt-manifest.json`
- `SHA256SUMS`

Every platform archive has the same basic layout:

```text
include/
  duckdb.h
  duckdb.hpp
lib/
  libduckdb_static.a       # Linux/macOS
  duckdb_static.lib        # Windows MSVC
  pkgconfig/duckdb.pc      # Linux/macOS
metadata.json
LICENSE-DuckDB
```

Windows is compiled with the static MSVC CRT so AnyDatas can continue producing a self-contained server executable without requiring the Visual C++ Redistributable.

## Release workflow

The expensive workflow is **manual only**. Normal pushes do not compile DuckDB.

1. Open **Actions → Build DuckDB prebuilt release**.
2. Run the workflow from `main`.
3. The workflow builds all four platform libraries, stages a normalized package, and then performs a second smoke build using `duckdb-rs` **without** the `bundled` feature.
4. Only after every platform passes does the workflow create the GitHub Release and publish the manifest/checksums.

The release workflow creates the configured release tag automatically. Do not manually create the tag first.

## AnyDatas consumption model

AnyDatas will eventually remove the `bundled` feature and download one of these archives before Cargo runs. The linked build uses:

```text
DUCKDB_LIB_DIR=<package>/lib
DUCKDB_INCLUDE_DIR=<package>/include
DUCKDB_STATIC=1
```

Linux/macOS packages include `lib/pkgconfig/duckdb.pc` so `libduckdb-sys` can discover the required C++/system link libraries. Windows additionally requires the system libraries documented in `metadata.json` (`ws2_32`, `rstrtmgr`, and `bcrypt`).

The release manifest is intended to be the source of truth for the AnyDatas downloader: platform, filename, byte size, SHA-256, DuckDB version, `duckdb-rs` version, and link metadata are all recorded there.

## Updating DuckDB

When AnyDatas moves to a new DuckDB release:

1. Update `version.json`.
2. Update the exact `duckdb` dependency in `builder/Cargo.toml` and `smoke/Cargo.toml`.
3. Increment `buildRevision` if the DuckDB version stays the same but the build recipe changes.
4. Merge the changes to `main`.
5. Manually run the release workflow once.
6. Point AnyDatas at the new release tag/manifest.

`scripts/verify_config.py` prevents the version metadata and Cargo dependencies from drifting apart.

## Licensing

The build/release automation in this repository is MIT licensed. DuckDB is separately distributed under its upstream MIT license; see `licenses/DuckDB-LICENSE` and `THIRD_PARTY_NOTICES.md`.
