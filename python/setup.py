#!/usr/bin/env python3
"""
NeoRuntime Platform Python SDK
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="neoruntime-ipc-sdk",
    version="0.8.2",
    author="NeoRuntime Team",
    author_email="opensource@camthink.ai",
    description="NeoRuntime AI Platform Python SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/camthink-ai/neoruntime-sdks/tree/main/python",
    project_urls={
        "Source": "https://github.com/camthink-ai/neoruntime-sdks",
        "Bug Tracker": "https://github.com/camthink-ai/neoruntime-sdks/issues",
        "Documentation": "https://camthink-ai.github.io/neoruntime-sdks/python/en/",
    },
    packages=find_packages(exclude=("tests", "tests.*")),
    package_data={"neoruntime_ipc_sdk": ["py.typed"]},
    zip_safe=False,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "grpcio>=1.50.0",
        "grpcio-tools>=1.50.0",
        "protobuf>=4.21.0",
        "numpy>=1.20.0",
        "Pillow>=9.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
    },
)
