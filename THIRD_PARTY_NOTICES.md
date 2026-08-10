# Third-party notices

## DuckDB

The release archives produced by this repository contain compiled DuckDB code and DuckDB public headers.

- Project: DuckDB
- Upstream: `duckdb/duckdb`
- Pinned version: `v1.5.4`
- License: MIT
- Copyright: 2018-2025 Stichting DuckDB Foundation

The DuckDB license text is preserved in `licenses/DuckDB-LICENSE` and copied into every generated platform package as `LICENSE-DuckDB`.

## duckdb-rs / libduckdb-sys

This repository uses the published `duckdb` / `libduckdb-sys` Rust crates to reproduce the same native compilation path used by AnyDatas.

- Project: `duckdb/duckdb-rs`
- Pinned crate series: `1.10504.0`
- License: MIT

`duckdb-rs` is a build-time dependency of the prebuild pipeline. The generated native archive contains DuckDB code; the Rust wrapper itself is not redistributed as part of the native archive.
