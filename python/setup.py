#!/usr/bin/env python3
"""
NE503 Platform Python SDK
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="hailo-ipc-sdk",
    version="0.3.0",
    author="NE503 Team",
    author_email="opensource@camthink.ai",
    description="NE503 EdgeCam AI Platform Python SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/camthink-ai/ne503-aipc-sdks/tree/main/python",
    packages=find_packages(exclude=("tests", "tests.*")),
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
