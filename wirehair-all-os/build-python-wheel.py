#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = ROOT_DIR / "wirehair-all-os"
DIST_ROOT = PROJECT_DIR / "out" / "dist"
WHEEL_BUILD_ROOT = PROJECT_DIR / "out" / "wheel-build"
WHEELHOUSE_ROOT = PROJECT_DIR / "out" / "wheelhouse"
PACKAGE_TEMPLATE_DIR = PROJECT_DIR / "python-package"

TARGETS = {
    "windows-x64": {
        "lib_relpath": Path("bin") / "wirehair.dll",
        "packaged_lib_name": "wirehair.dll",
        "wheel_platform_tag": "win_amd64",
    },
    "linux-x64": {
        "lib_relpath": Path("lib") / "libwirehair.so.2",
        "packaged_lib_name": "libwirehair.so",
        "wheel_platform_tag": "manylinux2014_x86_64",
    },
    "linux-aarch64": {
        "lib_relpath": Path("lib") / "libwirehair.so.2",
        "packaged_lib_name": "libwirehair.so",
        "wheel_platform_tag": "manylinux_2_28_aarch64",
    },
    "darwin-x64": {
        "lib_relpath": Path("lib") / "libwirehair.2.dylib",
        "packaged_lib_name": "libwirehair.dylib",
        "wheel_platform_tag": "macosx_10_13_x86_64",
    },
    "darwin-aarch64": {
        "lib_relpath": Path("lib") / "libwirehair.2.dylib",
        "packaged_lib_name": "libwirehair.dylib",
        "wheel_platform_tag": "macosx_11_0_arm64",
    },
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build a platform wheel that bundles the wirehair shared library."
    )
    parser.add_argument("--target", required=True, choices=sorted(TARGETS))
    parser.add_argument(
        "--version",
        default=os.environ.get("WIREHAIR_PY_VERSION", "0.0.0.dev0"),
        help="Distribution version to embed into the wheel.",
    )
    parser.add_argument(
        "--dist-name",
        default=os.environ.get("WIREHAIR_PY_DIST_NAME", "wirehair-ctypes"),
        help="Distribution name to use for the wheel metadata.",
    )
    parser.add_argument(
        "--outdir",
        default=str(WHEELHOUSE_ROOT),
        help="Directory where the built wheel will be written.",
    )
    parser.add_argument(
        "--no-isolation",
        action="store_true",
        help="Pass --no-isolation through to python -m build.",
    )
    return parser.parse_args()


def copy_package_sources(stage_dir: Path, target: str) -> None:
    package_src_dir = stage_dir / "src"
    wirehair_pkg_dir = package_src_dir / "wirehair"
    native_dir = wirehair_pkg_dir / "_native"
    native_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(ROOT_DIR / "python" / "whirehair.py", wirehair_pkg_dir / "whirehair.py")
    shutil.copy2(ROOT_DIR / "LICENSE", stage_dir / "LICENSE")

    target_info = TARGETS[target]
    source_library = DIST_ROOT / target / target_info["lib_relpath"]
    if not source_library.is_file():
        raise FileNotFoundError(
            f"Missing built library for {target}: {source_library}. "
            "Run build-all.sh first."
        )
    shutil.copy2(source_library, native_dir / target_info["packaged_lib_name"])


def stage_package_tree(target: str) -> Path:
    stage_dir = WHEEL_BUILD_ROOT / target
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    shutil.copytree(PACKAGE_TEMPLATE_DIR, stage_dir)
    copy_package_sources(stage_dir, target)
    return stage_dir


def build_wheel(stage_dir: Path, target: str, version: str, dist_name: str, outdir: Path, no_isolation: bool) -> None:
    outdir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["WIREHAIR_PY_VERSION"] = version
    env["WIREHAIR_PY_DIST_NAME"] = dist_name
    env["WIREHAIR_PY_PLAT_TAG"] = TARGETS[target]["wheel_platform_tag"]

    command = [sys.executable, "-m", "build", "--wheel", "--outdir", str(outdir)]
    if no_isolation:
        command.append("--no-isolation")

    subprocess.run(command, cwd=stage_dir, env=env, check=True)


def main() -> int:
    args = parse_args()
    stage_dir = stage_package_tree(args.target)
    build_wheel(
        stage_dir=stage_dir,
        target=args.target,
        version=args.version,
        dist_name=args.dist_name,
        outdir=Path(args.outdir).resolve(),
        no_isolation=args.no_isolation,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
