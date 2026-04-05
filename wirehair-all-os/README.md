# wirehair-all-os

这是一个包在上游 `wirehair` 外面的 CMake 工程，用 `zig cc` / `zig c++` 交叉编译给 Python `ctypes` 直接加载的动态库。

默认支持这些目标：

- `windows-x64`
- `linux-x64`，glibc `2.17`
- `linux-aarch64`，glibc `2.28`
- `darwin-x64`
- `darwin-aarch64`

## 用法

在仓库根目录执行：

```bash
cd wirehair-all-os
./build-all.sh
```

只构建单个平台：

```bash
./build-all.sh linux-x64
```

对当前主机可直接运行的目标，还可以在对应构建目录里执行：

```bash
cd out/build/linux-x64
ctest --output-on-failure
```

现在默认会注册一个 `wirehair_python_ctypes` 测试，它使用 Python `ctypes` 加载刚刚构建出来的共享库，并按上游 README 里的编码/丢包/解码流程跑一遍完整回环。
这个测试现在直接复用上游的 [whirehair.py](/home/zarra/Documents/projects/wirehair/python/whirehair.py)。

## 构建 Python wheel

先构建目标动态库，再生成对应平台 wheel：

```bash
./build-all.sh linux-x64
python3 build-python-wheel.py --target linux-x64 --version 0.1.0 --no-isolation
```

生成结果默认在：

```text
wirehair-all-os/out/wheelhouse/
```

wheel 内会打包：

- `wirehair` Python 包
- `wirehair/_native/` 下的平台动态库
- 兼容旧拼写的 `whirehair` 顶层模块

## 打包 C++ SDK

```bash
python3 package-sdk.py --target linux-x64 --version 0.1.0
```

SDK zip 默认输出到：

```text
wirehair-all-os/out/sdk/
```

## GitHub Actions

仓库里已经加了 [build-release.yml](/home/zarra/Documents/projects/wirehair/.github/workflows/build-release.yml)：

- `ubuntu-latest` 上用 Zig 构建 `linux-x64`、`linux-aarch64`、`windows-x64`
- `macos-latest` 上用 Zig 构建 `darwin-x64`、`darwin-aarch64`
- 每个目标都会产出：
  - 对应平台的 C++ SDK zip
  - 对应平台的 `ctypes` wheel
- tag 触发时会自动上传 GitHub Release 资产
- 如果仓库 secret 里配置了 `PYPI_API_TOKEN`，还会把 wheel 发布到 PyPI

说明：

- GitHub 官方当前没有 Python/PyPI registry 的 GitHub Packages 支持，所以这里采用 `GitHub Release + wheel`，以及可选的 PyPI 发布。
- 如果只想手动构建产物，可以直接用 `workflow_dispatch`。

如果 `zig` 或 macOS SDK 不在默认位置，可以覆盖环境变量：

```bash
ZIG_EXECUTABLE=/path/to/zig \
MACOS_SDK_ROOT=/home/zarra/opt/macosx-sdks/MacOSX13.3.sdk \
./build-all.sh
```

## 输出目录

构建和安装产物默认在：

```text
wirehair-all-os/out/build/<target>/
wirehair-all-os/out/dist/<target>/
```

安装结果包含：

- `bin/wirehair.dll` 或 `lib/libwirehair.{so,dylib}`
- `include/wirehair/wirehair.h`
- `python/whirehair.py`

Windows 下 `ctypes.CDLL()` 直接指向 `bin/wirehair.dll`；
Linux/macOS 下指向 `lib/libwirehair.so` 或 `lib/libwirehair.dylib`。

## 说明

- 上游源码仍然在仓库根目录，外层工程通过 `add_subdirectory(..)` 引入。
- 默认关闭上游测试和 `-march=native`，避免交叉编译污染目标产物。
- macOS 使用外部 SDK：`/home/zarra/opt/macosx-sdks/MacOSX13.3.sdk`
