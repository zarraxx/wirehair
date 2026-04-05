#!/usr/bin/env python3
#
# Copyleft (c) 2019 Daniel Norte de Moraes <danielcheagle@gmail.com>.
#
# * This code is hereby placed in the public domain.
# *
# * THIS SOFTWARE IS PROVIDED BY THE AUTHORS ''AS IS'' AND ANY EXPRESS
# * OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# * ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE
# * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# * BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# * WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# * OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# * EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Wirehair ctypes helpers and the README round-trip example."""

import argparse
import ctypes
import os
import sys
from pathlib import Path


# Success code
Wirehair_Success = 0

# More data is needed to decode. This is normal and does not indicate a failure
Wirehair_NeedMore = 1

# Other values are failure codes:

# A function parameter was invalid
Wirehair_InvalidInput = 2

# Encoder needs a better dense seed
Wirehair_BadDenseSeed = 3

# Encoder needs a better peel seed
Wirehair_BadPeelSeed = 4

# N = ceil(messageBytes / blockBytes) is too small.
# Try reducing block_size or use a larger message
Wirehair_BadInput_SmallN = 5

# N = ceil(messageBytes / blockBytes) is too large.
# Try increasing block_size or use a smaller message
Wirehair_BadInput_LargeN = 6

# Not enough extra rows to solve it, must give up
Wirehair_ExtraInsufficient = 7

# An error occurred during the request
Wirehair_Error = 8

# Out of memory
Wirehair_OOM = 9

# Platform is not supported yet
Wirehair_UnsupportedPlatform = 10

WirehairResult_Count = 11  # /* for asserts */
WirehairResult_Padding = 0x7FFFFFFF  # /* int32_t padding */

WIREHAIR_VERSION = 2
DEFAULT_PACKET_SIZE = 1400
DEFAULT_MESSAGE_BYTES = 1_000_333
DEFAULT_LOSS_EVERY = 10

__all__ = [
    "DEFAULT_LOSS_EVERY",
    "DEFAULT_MESSAGE_BYTES",
    "DEFAULT_PACKET_SIZE",
    "WIREHAIR_VERSION",
    "Wirehair_BadDenseSeed",
    "Wirehair_BadInput_LargeN",
    "Wirehair_BadInput_SmallN",
    "Wirehair_BadPeelSeed",
    "Wirehair_Error",
    "Wirehair_ExtraInsufficient",
    "Wirehair_InvalidInput",
    "Wirehair_NeedMore",
    "Wirehair_OOM",
    "Wirehair_Success",
    "Wirehair_UnsupportedPlatform",
    "build_demo_message",
    "configure_api",
    "load_library",
    "main",
    "resolve_library_path",
    "run_readme_example",
]


def _default_library_names():
    if sys.platform == "win32":
        return ("wirehair.dll",)
    if sys.platform == "darwin":
        return ("libwirehair.dylib", "libwirehair.2.dylib")
    return ("libwirehair.so", "libwirehair.so.2")


def _candidate_library_paths(explicit_path=None):
    if explicit_path:
        yield Path(explicit_path).expanduser()

    env_path = os.environ.get("WIREHAIR_LIB_PATH")
    if env_path:
        yield Path(env_path).expanduser()

    module_dir = Path(__file__).resolve().parent
    search_dirs = (
        module_dir,
        module_dir / "_native",
        module_dir / "lib",
        module_dir / "bin",
        module_dir.parent / "lib",
        module_dir.parent / "bin",
    )

    for base_dir in search_dirs:
        for lib_name in _default_library_names():
            yield base_dir / lib_name


def resolve_library_path(explicit_path=None):
    checked = []
    seen = set()

    for candidate in _candidate_library_paths(explicit_path):
        candidate = candidate.resolve(strict=False)
        candidate_key = str(candidate)
        if candidate_key in seen:
            continue
        seen.add(candidate_key)
        checked.append(candidate)
        if candidate.is_file():
            return candidate

    search_hint = "\n".join(f"  - {path}" for path in checked)
    raise FileNotFoundError(
        "Unable to find a wirehair shared library. Checked:\n"
        f"{search_hint}"
    )


def configure_api(lib):
    lib.wirehair_init_.argtypes = [ctypes.c_int]
    lib.wirehair_init_.restype = ctypes.c_int

    lib.wirehair_encoder_create.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_uint64,
        ctypes.c_uint32,
    ]
    lib.wirehair_encoder_create.restype = ctypes.c_void_p

    lib.wirehair_encode.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint32),
    ]
    lib.wirehair_encode.restype = ctypes.c_int

    lib.wirehair_decoder_create.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint64,
        ctypes.c_uint32,
    ]
    lib.wirehair_decoder_create.restype = ctypes.c_void_p

    lib.wirehair_decode.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint,
        ctypes.c_void_p,
        ctypes.c_uint32,
    ]
    lib.wirehair_decode.restype = ctypes.c_int

    lib.wirehair_recover.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_uint64,
    ]
    lib.wirehair_recover.restype = ctypes.c_int

    lib.wirehair_free.argtypes = [ctypes.c_void_p]
    lib.wirehair_free.restype = None


def load_library(lib_path=None):
    resolved_path = resolve_library_path(lib_path)
    lib = ctypes.CDLL(str(resolved_path))
    configure_api(lib)
    return lib, resolved_path


def build_demo_message(message_bytes=DEFAULT_MESSAGE_BYTES):
    pattern = b"wirehair-ctypes-readme-example:"
    repeats = (message_bytes // len(pattern)) + 1
    return (pattern * repeats)[:message_bytes]


def run_readme_example(
    lib_path=None,
    packet_size=DEFAULT_PACKET_SIZE,
    message_bytes=DEFAULT_MESSAGE_BYTES,
    loss_every=DEFAULT_LOSS_EVERY,
):
    lib, resolved_path = load_library(lib_path)

    init_result = lib.wirehair_init_(WIREHAIR_VERSION)
    if init_result != Wirehair_Success:
        raise RuntimeError(f"wirehair_init_ failed: {init_result}")

    message = build_demo_message(message_bytes)
    message_buf = ctypes.create_string_buffer(message)

    encoder = lib.wirehair_encoder_create(
        None,
        ctypes.cast(message_buf, ctypes.c_void_p),
        ctypes.c_uint64(len(message)),
        ctypes.c_uint32(packet_size),
    )
    if not encoder:
        raise RuntimeError("wirehair_encoder_create failed")

    decoder = lib.wirehair_decoder_create(
        None,
        ctypes.c_uint64(len(message)),
        ctypes.c_uint32(packet_size),
    )
    if not decoder:
        lib.wirehair_free(encoder)
        raise RuntimeError("wirehair_decoder_create failed")

    try:
        block_id = 0
        needed = 0

        while True:
            block_id += 1

            if loss_every > 0 and (block_id % loss_every) == 0:
                continue

            needed += 1
            block = ctypes.create_string_buffer(packet_size)
            write_len = ctypes.c_uint32(0)

            encode_result = lib.wirehair_encode(
                encoder,
                ctypes.c_uint(block_id),
                ctypes.cast(block, ctypes.c_void_p),
                ctypes.c_uint32(packet_size),
                ctypes.byref(write_len),
            )
            if encode_result != Wirehair_Success:
                raise RuntimeError(f"wirehair_encode failed: {encode_result}")

            decode_result = lib.wirehair_decode(
                decoder,
                ctypes.c_uint(block_id),
                ctypes.cast(block, ctypes.c_void_p),
                write_len,
            )
            if decode_result == Wirehair_Success:
                break
            if decode_result != Wirehair_NeedMore:
                raise RuntimeError(f"wirehair_decode failed: {decode_result}")

            if needed > 4096:
                raise RuntimeError(
                    "decoder did not converge in a reasonable number of packets"
                )

        decoded = ctypes.create_string_buffer(len(message))
        recover_result = lib.wirehair_recover(
            decoder,
            ctypes.cast(decoded, ctypes.c_void_p),
            ctypes.c_uint64(len(message)),
        )
        if recover_result != Wirehair_Success:
            raise RuntimeError(f"wirehair_recover failed: {recover_result}")

        if decoded.raw != message:
            raise RuntimeError("decoded payload does not match the original input")
    finally:
        lib.wirehair_free(encoder)
        lib.wirehair_free(decoder)

    return {
        "library_path": resolved_path,
        "message_bytes": len(message),
        "packet_size": packet_size,
        "packets_needed": needed,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run the Wirehair README example through Python ctypes."
    )
    parser.add_argument("--lib", help="Path to the shared library to load")
    parser.add_argument(
        "--packet-size",
        type=int,
        default=DEFAULT_PACKET_SIZE,
        help=f"Packet size to use during the example (default: {DEFAULT_PACKET_SIZE})",
    )
    parser.add_argument(
        "--message-bytes",
        type=int,
        default=DEFAULT_MESSAGE_BYTES,
        help=(
            "Message size to use during the example "
            f"(default: {DEFAULT_MESSAGE_BYTES})"
        ),
    )
    parser.add_argument(
        "--loss-every",
        type=int,
        default=DEFAULT_LOSS_EVERY,
        help=(
            "Simulate packet loss by dropping every Nth packet "
            f"(default: {DEFAULT_LOSS_EVERY})"
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only report failures",
    )
    args = parser.parse_args(argv)

    result = run_readme_example(
        lib_path=args.lib,
        packet_size=args.packet_size,
        message_bytes=args.message_bytes,
        loss_every=args.loss_every,
    )

    if not args.quiet:
        print(
            "Wirehair README example passed "
            f"using {result['library_path']} "
            f"(message={result['message_bytes']} bytes, "
            f"packet_size={result['packet_size']}, "
            f"packets_needed={result['packets_needed']})"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
