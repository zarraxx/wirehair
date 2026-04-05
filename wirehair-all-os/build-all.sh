#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_ROOT="${BUILD_ROOT:-${SCRIPT_DIR}/out/build}"
DIST_ROOT="${DIST_ROOT:-${SCRIPT_DIR}/out/dist}"
ZIG_EXECUTABLE="${ZIG_EXECUTABLE:-zig}"
ZIG_GLOBAL_CACHE_DIR="${ZIG_GLOBAL_CACHE_DIR:-${SCRIPT_DIR}/out/zig-global-cache}"
DEFAULT_MACOS_SDK_ROOT="/home/zarra/opt/macosx-sdks/MacOSX13.3.sdk"
MACOS_SDK_ROOT="${MACOS_SDK_ROOT:-}"
GENERATOR="${CMAKE_GENERATOR:-Unix Makefiles}"

mkdir -p "${BUILD_ROOT}" "${DIST_ROOT}" "${ZIG_GLOBAL_CACHE_DIR}"
export ZIG_GLOBAL_CACHE_DIR

usage() {
    cat <<'EOF'
Usage:
  ./build-all.sh                # build all targets
  ./build-all.sh linux-x64      # build one target
  ./build-all.sh linux-x64 windows-x64

Outputs:
  wirehair-all-os/out/dist/<target>/
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

target_specs=(
    "windows-x64|windows|x86_64|x86_64-windows-gnu|"
    "linux-x64|linux|x86_64|x86_64-linux-gnu.2.17|"
    "linux-aarch64|linux|aarch64|aarch64-linux-gnu.2.28|"
    "darwin-x64|darwin|x86_64|x86_64-macos.10.13|10.13"
    "darwin-aarch64|darwin|arm64|aarch64-macos.11.0|11.0"
)

selected_targets=("$@")
if [[ "${#selected_targets[@]}" -eq 0 ]]; then
    selected_targets=(
        "windows-x64"
        "linux-x64"
        "linux-aarch64"
        "darwin-x64"
        "darwin-aarch64"
    )
fi

contains_target() {
    local wanted="$1"
    shift
    local item
    for item in "$@"; do
        if [[ "${item}" == "${wanted}" ]]; then
            return 0
        fi
    done
    return 1
}

resolve_macos_sdk_root() {
    if [[ -n "${MACOS_SDK_ROOT}" ]]; then
        echo "${MACOS_SDK_ROOT}"
        return 0
    fi

    if command -v xcrun >/dev/null 2>&1; then
        xcrun --sdk macosx --show-sdk-path
        return 0
    fi

    echo "${DEFAULT_MACOS_SDK_ROOT}"
}

configure_target() {
    local package_name="$1"
    local target_os="$2"
    local target_arch="$3"
    local zig_target="$4"
    local deployment_target="$5"

    local build_dir="${BUILD_ROOT}/${package_name}"
    local dist_dir="${DIST_ROOT}/${package_name}"
    local zig_local_cache_dir="${build_dir}/.zig-cache"

    cmake -E rm -rf "${build_dir}" "${dist_dir}"
    mkdir -p "${build_dir}" "${dist_dir}" "${zig_local_cache_dir}"

    local cmake_args=(
        -S "${SCRIPT_DIR}"
        -B "${build_dir}"
        -G "${GENERATOR}"
        -DCMAKE_BUILD_TYPE=Release
        -DCMAKE_TOOLCHAIN_FILE="${SCRIPT_DIR}/cmake/ZigToolchain.cmake"
        -DCMAKE_INSTALL_PREFIX="${dist_dir}"
        -DWIREHAIR_SOURCE_DIR="${SOURCE_DIR}"
        -DZIG_EXECUTABLE="${ZIG_EXECUTABLE}"
        -DWIREHAIR_TARGET_OS="${target_os}"
        -DWIREHAIR_TARGET_ARCH="${target_arch}"
        -DWIREHAIR_ZIG_TARGET="${zig_target}"
    )

    if [[ "${target_os}" == "darwin" ]]; then
        local resolved_macos_sdk_root
        resolved_macos_sdk_root="$(resolve_macos_sdk_root)"
        if [[ ! -d "${resolved_macos_sdk_root}" ]]; then
            echo "macOS SDK not found: ${resolved_macos_sdk_root}" >&2
            exit 1
        fi
        cmake_args+=(
            -DWIREHAIR_OSX_SYSROOT="${resolved_macos_sdk_root}"
            -DWIREHAIR_OSX_DEPLOYMENT_TARGET="${deployment_target}"
        )
    fi

    echo "==> Configuring ${package_name} (${zig_target})"
    ZIG_LOCAL_CACHE_DIR="${zig_local_cache_dir}" cmake "${cmake_args[@]}"

    echo "==> Building ${package_name}"
    ZIG_LOCAL_CACHE_DIR="${zig_local_cache_dir}" cmake --build "${build_dir}" --config Release --target wirehair

    echo "==> Installing ${package_name} -> ${dist_dir}"
    ZIG_LOCAL_CACHE_DIR="${zig_local_cache_dir}" cmake --install "${build_dir}" --config Release
}

found_any=0
for spec in "${target_specs[@]}"; do
    IFS='|' read -r package_name target_os target_arch zig_target deployment_target <<<"${spec}"
    if contains_target "${package_name}" "${selected_targets[@]}"; then
        found_any=1
        configure_target "${package_name}" "${target_os}" "${target_arch}" "${zig_target}" "${deployment_target}"
    fi
done

if [[ "${found_any}" -eq 0 ]]; then
    echo "No valid target requested." >&2
    usage >&2
    exit 1
fi

echo
echo "Artifacts are under: ${DIST_ROOT}"
