#!/usr/bin/env python3

import argparse
import os
import zipfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = ROOT_DIR / "wirehair-all-os"
DIST_ROOT = PROJECT_DIR / "out" / "dist"
SDK_ROOT = PROJECT_DIR / "out" / "sdk"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create a zip archive for one built wirehair SDK target."
    )
    parser.add_argument("--target", required=True)
    parser.add_argument(
        "--version",
        default=os.environ.get("WIREHAIR_SDK_VERSION", "0.0.0-dev"),
        help="Version string used in the archive file name.",
    )
    parser.add_argument(
        "--outdir",
        default=str(SDK_ROOT),
        help="Directory where the archive will be written.",
    )
    return parser.parse_args()


def iter_sdk_files(target_dir: Path):
    for path in sorted(target_dir.rglob("*")):
        if path.is_file():
            yield path


def main() -> int:
    args = parse_args()
    target_dir = DIST_ROOT / args.target
    if not target_dir.is_dir():
        raise FileNotFoundError(
            f"SDK directory does not exist for {args.target}: {target_dir}"
        )

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    prefix = f"wirehair-sdk-{args.version}-{args.target}"
    archive_path = outdir / f"{prefix}.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(ROOT_DIR / "LICENSE", arcname=f"{prefix}/LICENSE")
        archive.write(ROOT_DIR / "README.md", arcname=f"{prefix}/README.md")
        archive.write(PROJECT_DIR / "README.md", arcname=f"{prefix}/BUILDING.md")
        for file_path in iter_sdk_files(target_dir):
            archive.write(file_path, arcname=f"{prefix}/{file_path.relative_to(target_dir)}")

    print(archive_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
