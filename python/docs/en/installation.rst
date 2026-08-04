Installation Guide
==================

System Requirements
-------------------

- Python 3.8 or higher
- Linux x86_64 or ARM64 for SDK development and tests
- NE503 AIPC Platform runtime environment for live device operations

Dependencies
------------

The SDK depends on the following Python packages:

- ``grpcio >= 1.50.0`` - gRPC communication
- ``protobuf >= 4.21.0`` - Protocol Buffers
- ``numpy >= 1.20.0`` - Array processing
- ``Pillow >= 9.0.0`` - Image processing

Installation Methods
--------------------

Install from Source
~~~~~~~~~~~~~~~~~~~

The SDK is not published to PyPI yet. Install from the public repository:

.. code-block:: bash

   git clone https://github.com/camthink-ai/ne503-aipc-sdks.git
   cd ne503-aipc-sdks
   python -m pip install -e ./python

Build a Wheel
~~~~~~~~~~~~~

.. code-block:: bash

   cd ne503-aipc-sdks/python
   python -m pip install --upgrade build
   python -m build --wheel
   ls dist/*.whl

The generated ``.whl`` file is written to ``dist/``. Install it locally to
verify the artifact:

.. code-block:: bash

   python -m pip install dist/hailo_ipc_sdk-*.whl

GitHub Actions Wheel Artifacts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The public repository builds the Python wheel with GitHub Actions. Open
``Actions`` -> ``Build Python SDK wheel`` and download the
``python-sdk-wheel`` artifact from a successful run.

Maintainers can also publish a GitHub Release by pushing a matching version tag
or running the workflow manually with release publishing enabled.

Planned Package Channels
~~~~~~~~~~~~~~~~~~~~~~~~

PyPI and tarball packages are not published yet. Do not use
``pip install hailo-ipc-sdk`` or tarball URLs until those release channels are
announced.

When PyPI publishing is enabled, installation will use:

.. code-block:: bash

   python -m pip install hailo-ipc-sdk

Verify Installation
-------------------

.. code-block:: python

   import hailo_ipc_sdk
   print(hailo_ipc_sdk.__version__)
   # Output: 0.3.0

Development Environment
-----------------------

If you need to develop or test the SDK, install the development dependencies:

.. code-block:: bash

   pip install -e ".[dev]"

This installs additional tools:

- ``pytest`` - Unit testing
- ``pytest-cov`` - Test coverage
- ``black`` - Code formatting
- ``flake8`` - Code linting
- ``mypy`` - Type checking

Docker Environment
------------------

Using the current public source repository:

.. code-block:: dockerfile

   FROM python:3.11-slim
   RUN apt-get update \
       && apt-get install -y --no-install-recommends git \
       && rm -rf /var/lib/apt/lists/*
   RUN python -m pip install --no-cache-dir \
       "git+https://github.com/camthink-ai/ne503-aipc-sdks.git#subdirectory=python"

Or build your own image:

.. code-block:: dockerfile

   FROM python:3.10-slim
   COPY hailo_ipc_sdk-0.3.0-py3-none-any.whl /tmp/
   RUN python -m pip install --no-cache-dir /tmp/hailo_ipc_sdk-0.3.0-py3-none-any.whl
   WORKDIR /app
   COPY app.py .
   CMD ["python3", "app.py"]

Troubleshooting
---------------

Permission Issues
~~~~~~~~~~~~~~~~~

If you encounter Unix socket permission errors:

.. code-block:: bash

   # Ensure the user is in the aipc group
   sudo usermod -aG aipc $USER

   # Re-login or refresh the group
   newgrp aipc

gRPC Connection Failure
~~~~~~~~~~~~~~~~~~~~~~~

Check if platform services are running:

.. code-block:: bash

   # Check service status
   systemctl status ai-runtime
   systemctl status event-bus
   systemctl status device-control

   # Check socket files
   ls -l /run/aipc/*.sock

Dependency Conflicts
~~~~~~~~~~~~~~~~~~~~

If you encounter dependency version conflicts, use a virtual environment:

.. code-block:: bash

   python3 -m venv venv
   source venv/bin/activate
   git clone https://github.com/camthink-ai/ne503-aipc-sdks.git
   python -m pip install -e ne503-aipc-sdks/python
