#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import stat
import sys
import zipfile

FIXED_TIMESTAMP = (2026, 1, 1, 0, 0, 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    args = parser.parse_args()

    stage = args.stage.resolve()
    output = args.output.resolve()
    if not stage.is_dir():
        raise SystemExit(f"stage directory does not exist: {stage}")
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    files = sorted(path for path in stage.rglob("*") if path.is_file())
    if not files:
        raise SystemExit(f"stage directory is empty: {stage}")

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(stage).as_posix()
            info = zipfile.ZipInfo(relative, FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, path.read_bytes(), compresslevel=9)

    print(f"created {output} ({output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
