Installation Guide
==================

System Requirements
-------------------

- Python 3.8 or higher
- Linux x86_64 or ARM64 for SDK development and tests
- NeoRuntime Platform runtime environment for live device operations

Dependencies
------------

The SDK depends on the following Python packages:

- ``grpcio >= 1.50.0`` - gRPC communication
- ``protobuf >= 4.21.0`` - Protocol Buffers
- ``numpy >= 1.20.0`` - Array processing
- ``Pillow >= 9.0.0`` - Image processing

Installation Methods
--------------------

Install from PyPI
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python -m pip install neoruntime-ipc-sdk

Install from Source
~~~~~~~~~~~~~~~~~~~

Install from the public repository:

.. code-block:: bash

   git clone https://github.com/camthink-ai/neoruntime-sdks.git
   cd neoruntime-sdks
   python -m pip install -e ./python

Build a Wheel
~~~~~~~~~~~~~

.. code-block:: bash

   cd neoruntime-sdks/python
   python -m pip install --upgrade build
   python -m build --wheel
   ls dist/*.whl

The generated ``.whl`` file is written to ``dist/``. Install it locally to
verify the artifact:

.. code-block:: bash

   python -m pip install dist/neoruntime_ipc_sdk-*.whl

GitHub Actions Wheel Artifacts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The public repository builds and tests the wheel and sdist with GitHub
Actions. Open ``Actions`` -> ``Build SDK release artifacts`` and download
the ``python-sdk-dist`` artifact from a successful run.

Maintainers publish by pushing a ``v*`` tag (or running the workflow
manually with publishing enabled): this creates a GitHub Release and
publishes the distributions to TestPyPI and then PyPI.

Verify Installation
-------------------

.. code-block:: python

   import neoruntime_ipc_sdk
   print(neoruntime_ipc_sdk.__version__)
   # Output: 0.8.2

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
       "git+https://github.com/camthink-ai/neoruntime-sdks.git#subdirectory=python"

Or build your own image:

.. code-block:: dockerfile

   FROM python:3.10-slim
   COPY neoruntime_ipc_sdk-0.8.2-py3-none-any.whl /tmp/
   RUN python -m pip install --no-cache-dir /tmp/neoruntime_ipc_sdk-0.8.2-py3-none-any.whl
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
   git clone https://github.com/camthink-ai/neoruntime-sdks.git
   python -m pip install -e neoruntime-sdks/python
