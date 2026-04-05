#!/usr/bin/env bash
set -euo pipefail

ZIG_VERSION="${ZIG_VERSION:-0.15.2}"
INSTALL_ROOT="${1:-${PWD}/.zig}"

uname_s="$(uname -s)"
uname_m="$(uname -m)"

case "${uname_s}" in
    Linux) zig_os="linux" ;;
    Darwin) zig_os="macos" ;;
    *)
        echo "Unsupported host OS: ${uname_s}" >&2
        exit 1
        ;;
esac

case "${uname_m}" in
    x86_64|amd64) zig_arch="x86_64" ;;
    arm64|aarch64) zig_arch="aarch64" ;;
    *)
        echo "Unsupported host arch: ${uname_m}" >&2
        exit 1
        ;;
esac

mkdir -p "${INSTALL_ROOT}"

archive_ext="tar.xz"
if [[ "${zig_os}" == "windows" ]]; then
    archive_ext="zip"
fi

archive_name="zig-${zig_arch}-${zig_os}-${ZIG_VERSION}.${archive_ext}"
download_url="https://ziglang.org/download/${ZIG_VERSION}/${archive_name}"
archive_path="${INSTALL_ROOT}/${archive_name}"
extract_root="${INSTALL_ROOT}/zig-${ZIG_VERSION}"
binary_dir="${extract_root}/zig-${zig_arch}-${zig_os}-${ZIG_VERSION}"

if [[ ! -x "${binary_dir}/zig" ]]; then
    rm -rf "${extract_root}"
    mkdir -p "${extract_root}"
    curl -L --fail --retry 3 "${download_url}" -o "${archive_path}"
    tar -xf "${archive_path}" -C "${extract_root}"
fi

if [[ -n "${GITHUB_PATH:-}" ]]; then
    echo "${binary_dir}" >> "${GITHUB_PATH}"
else
    echo "${binary_dir}"
fi
