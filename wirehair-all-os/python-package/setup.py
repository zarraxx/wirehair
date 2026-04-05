import os

from setuptools import find_packages, setup
from wheel.bdist_wheel import bdist_wheel


class BinaryWheel(bdist_wheel):
    def finalize_options(self):
        super().finalize_options()
        self.root_is_pure = False

    def get_tag(self):
        platform_tag = os.environ["WIREHAIR_PY_PLAT_TAG"]
        return ("py3", "none", platform_tag)


setup(
    name=os.environ.get("WIREHAIR_PY_DIST_NAME", "wirehair-ctypes"),
    version=os.environ.get("WIREHAIR_PY_VERSION", "0.0.0.dev0"),
    description="Python ctypes bindings that bundle the Wirehair shared library",
    long_description=(open("README.md", "r", encoding="utf-8").read()),
    long_description_content_type="text/markdown",
    license="BSD-3-Clause AND CC0-1.0",
    python_requires=">=3.8",
    package_dir={"": "src"},
    packages=find_packages("src"),
    py_modules=["whirehair"],
    package_data={"wirehair": ["_native/*"]},
    include_package_data=True,
    cmdclass={"bdist_wheel": BinaryWheel},
    url="https://github.com/zarraxx/wirehair",
    project_urls={
        "Source": "https://github.com/zarraxx/wirehair",
    },
)
