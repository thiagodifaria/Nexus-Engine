"""
Setup script for Nexus Engine Python backend.

This setup.py handles building PyBind11 C++ bindings and configuring the Python package.
For standard configuration, see pyproject.toml.
"""

import os
import sys
from pathlib import Path
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext


class CMakeExtension(Extension):
    """Custom Extension class for CMake-based builds."""

    def __init__(self, name: str, sourcedir: str = "") -> None:
        super().__init__(name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    """Custom build_ext command that uses CMake to build C++ extensions."""

    def build_extension(self, ext: CMakeExtension) -> None:
        import subprocess

        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))

        # Required for auto-detection of auxiliary "native" libs
        if not extdir.endswith(os.path.sep):
            extdir += os.path.sep

        debug = int(os.environ.get("DEBUG", 0)) if self.debug is None else self.debug
        cfg = "Debug" if debug else "Release"

        # CMake lets you override the generator - we check this
        cmake_generator = os.environ.get("CMAKE_GENERATOR", "")

        cmake_args = [
            f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={extdir}",
            f"-DPYTHON_EXECUTABLE={sys.executable}",
            f"-DCMAKE_BUILD_TYPE={cfg}",
            "-DCMAKE_CXX_STANDARD=20",
        ]
        build_args = []

        if "CMAKE_ARGS" in os.environ:
            cmake_args += [item for item in os.environ["CMAKE_ARGS"].split(" ") if item]

        # Windows-specific configuration
        if sys.platform.startswith("win"):
            cmake_args += [
                f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{cfg.upper()}={extdir}",
            ]
            if "Visual Studio" in cmake_generator:
                build_args += ["--config", cfg]
        else:
            # Unix-specific configuration
            build_args += ["--", "-j4"]

        env = os.environ.copy()
        env["CXXFLAGS"] = f'{env.get("CXXFLAGS", "")} -DVERSION_INFO=\\"{self.distribution.get_version()}\\"'

        # Build directory
        build_temp = Path(self.build_temp) / ext.name
        if not build_temp.exists():
            build_temp.mkdir(parents=True)

        print(f"Building extension {ext.name}")
        print(f"CMake args: {cmake_args}")
        print(f"Build args: {build_args}")

        # Configure
        subprocess.check_call(
            ["cmake", ext.sourcedir] + cmake_args, cwd=build_temp, env=env
        )

        # Build
        subprocess.check_call(
            ["cmake", "--build", "."] + build_args, cwd=build_temp
        )


# Determine if C++ bindings should be built
BUILD_CPP_BINDINGS = os.environ.get("BUILD_CPP_BINDINGS", "1") == "1"

# Extensions list
ext_modules = []
if BUILD_CPP_BINDINGS:
    ext_modules = [
        CMakeExtension(
            "nexus_bindings.nexus_core",
            sourcedir="src/nexus_bindings"
        ),
    ]

# Setup configuration
setup(
    ext_modules=ext_modules,
    cmdclass={"build_ext": CMakeBuild},
    zip_safe=False,
    # All other configuration is in pyproject.toml
)